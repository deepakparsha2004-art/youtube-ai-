"""Authentication routes."""

import hmac
import re
import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from config import settings
from database import get_db
from models import User
from schemas import UserCreate, UserOut, Token
from utils.security import hash_password, verify_password, create_access_token, decode_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
OAUTH_STATE_COOKIE_MAX_AGE = 600


def _oauth_settings(provider: str) -> tuple[str | None, str | None, str, str]:
    if provider == "google":
        return (
            settings.GOOGLE_CLIENT_ID,
            settings.GOOGLE_CLIENT_SECRET,
            settings.GOOGLE_LOGIN_REDIRECT_URI,
            "https://accounts.google.com/o/oauth2/v2/auth",
        )
    return (
        settings.GITHUB_CLIENT_ID,
        settings.GITHUB_CLIENT_SECRET,
        settings.GITHUB_REDIRECT_URI,
        "https://github.com/login/oauth/authorize",
    )


def _oauth_error_redirect(error: str) -> RedirectResponse:
    frontend_origin = settings.FRONTEND_URL.split(",", 1)[0].strip().rstrip("/")
    return RedirectResponse(
        f"{frontend_origin}/#oauth_error={error}",
        status_code=303,
    )


def _oauth_start(provider: str) -> RedirectResponse:
    client_id, client_secret, redirect_uri, authorization_endpoint = _oauth_settings(provider)
    if not client_id or not client_secret:
        return _oauth_error_redirect("provider_not_configured")

    state = secrets.token_urlsafe(32)
    scopes = "openid email profile" if provider == "google" else "read:user user:email"
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scopes,
        "state": state,
    }
    if provider == "google":
        params["prompt"] = "select_account"

    response = RedirectResponse(
        f"{authorization_endpoint}?{urlencode(params)}",
        status_code=303,
    )
    response.set_cookie(
        key=f"{provider}_oauth_state",
        value=state,
        max_age=OAUTH_STATE_COOKIE_MAX_AGE,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        path=f"{settings.API_PREFIX}/auth/{provider}/callback",
    )
    return response


async def _oauth_profile(provider: str, code: str) -> dict:
    client_id, client_secret, redirect_uri, _ = _oauth_settings(provider)
    if not client_id or not client_secret:
        raise HTTPException(status_code=503, detail=f"{provider.title()} sign-in is not configured")

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            if provider == "google":
                token_response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "code": code,
                        "redirect_uri": redirect_uri,
                        "grant_type": "authorization_code",
                    },
                )
                token_response.raise_for_status()
                token_data = token_response.json()
                if not isinstance(token_data, dict):
                    raise HTTPException(status_code=502, detail="Invalid Google token response")
                access_token = token_data.get("access_token")
                if not access_token:
                    raise HTTPException(status_code=401, detail="Google sign-in did not return an access token")
                profile_response = await client.get(
                    "https://openidconnect.googleapis.com/v1/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                profile_response.raise_for_status()
                profile = profile_response.json()
                if not isinstance(profile, dict):
                    raise HTTPException(status_code=502, detail="Invalid Google sign-in profile")
                email = profile.get("email")
                if not isinstance(email, str) or not profile.get("email_verified"):
                    raise HTTPException(status_code=403, detail="Google account email is not verified")
                return {
                    "email": email,
                    "full_name": profile.get("name") if isinstance(profile.get("name"), str) else None,
                    "username": email.split("@", 1)[0],
                }

            token_response = await client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
                headers={"Accept": "application/json"},
            )
            token_response.raise_for_status()
            token_data = token_response.json()
            if not isinstance(token_data, dict):
                raise HTTPException(status_code=502, detail="Invalid GitHub token response")
            access_token = token_data.get("access_token")
            if not access_token:
                raise HTTPException(status_code=401, detail="GitHub sign-in did not return an access token")
            headers = {
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {access_token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": settings.APP_NAME,
            }
            profile_response = await client.get("https://api.github.com/user", headers=headers)
            profile_response.raise_for_status()
            profile = profile_response.json()
            if not isinstance(profile, dict):
                raise HTTPException(status_code=502, detail="Invalid GitHub sign-in profile")
            emails_response = await client.get("https://api.github.com/user/emails", headers=headers)
            emails_response.raise_for_status()
            emails = emails_response.json()
            if not isinstance(emails, list):
                raise HTTPException(status_code=502, detail="Invalid GitHub email response")
            verified_email = next(
                (
                    item.get("email")
                    for item in emails
                    if isinstance(item, dict) and item.get("primary") and item.get("verified")
                ),
                None,
            )
            if not isinstance(verified_email, str) or not verified_email:
                raise HTTPException(status_code=403, detail="GitHub account has no verified primary email")
            github_login = profile.get("login")
            full_name = profile.get("name")
            return {
                "email": verified_email,
                "full_name": full_name if isinstance(full_name, str) else github_login,
                "username": github_login,
            }
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"{provider.title()} sign-in provider rejected the request") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Could not reach {provider.title()} sign-in") from exc
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=502, detail=f"Invalid response from {provider.title()} sign-in") from exc


def _get_or_create_oauth_user(db: Session, profile: dict) -> User:
    email = profile.get("email")
    if not isinstance(email, str) or not email.strip():
        raise HTTPException(status_code=403, detail="Sign-in provider did not return an email address")

    email = email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if user is not None:
        if user.is_active is not True:
            raise HTTPException(status_code=403, detail="This account is inactive")
        return user

    provider_username = profile.get("username")
    candidate = re.sub(
        r"[^a-zA-Z0-9_.-]",
        "",
        provider_username if isinstance(provider_username, str) else "",
    ).strip("._-")
    candidate = (candidate or "user")[:90]
    username = candidate
    suffix = 1
    while db.query(User.id).filter(User.username == username).first():
        suffix_text = f"-{suffix}"
        username = f"{candidate[:100 - len(suffix_text)]}{suffix_text}"
        suffix += 1

    user = User(
        email=email,
        username=username,
        hashed_password=hash_password(secrets.token_urlsafe(32)),
        full_name=profile.get("full_name") if isinstance(profile.get("full_name"), str) else None,
        is_active=True,
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError as exc:
        db.rollback()
        user = db.query(User).filter(User.email == email).first()
        if user is not None and user.is_active is True:
            return user
        raise HTTPException(status_code=409, detail="Could not create an account for this email") from exc


async def _oauth_callback(
    provider: str,
    request: Request,
    code: str | None,
    state: str | None,
    db: Session,
) -> RedirectResponse:
    cookie_key = f"{provider}_oauth_state"
    expected_state = request.cookies.get(cookie_key)
    if not state or not expected_state or not hmac.compare_digest(state, expected_state):
        response = _oauth_error_redirect("invalid_state")
    elif not code:
        response = _oauth_error_redirect("sign_in_failed")
    else:
        try:
            profile = await _oauth_profile(provider, code)
            user = _get_or_create_oauth_user(db, profile)
            token = create_access_token({"sub": str(user.id)})
            frontend_origin = settings.FRONTEND_URL.split(",", 1)[0].strip().rstrip("/")
            response = RedirectResponse(
                f"{frontend_origin}/#oauth_token={token}",
                status_code=303,
            )
        except HTTPException as exc:
            error = "account_unavailable" if exc.status_code in (403, 409) else "sign_in_failed"
            response = _oauth_error_redirect(error)
    response.delete_cookie(
        key=cookie_key,
        path=f"{settings.API_PREFIX}/auth/{provider}/callback",
        secure=not settings.DEBUG,
        httponly=True,
        samesite="lax",
    )
    return response


def _create_guest_user(db: Session) -> User:
    existing_user = db.query(User).filter(User.username == "guest").first()
    if existing_user:
        return existing_user

    guest_user = User(
        email="guest@local.test",
        username="guest",
        hashed_password=hash_password("guest"),
        full_name="Guest User",
        is_active=True,
    )
    db.add(guest_user)
    db.commit()
    db.refresh(guest_user)
    return guest_user


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not token:
        if settings.ALLOW_GUEST_ACCESS:
            return db.query(User).filter(User.is_active.is_(True)).order_by(User.id.asc()).first() or _create_guest_user(db)
        raise HTTPException(status_code=401, detail="Authentication required", headers={"WWW-Authenticate": "Bearer"})

    payload = decode_access_token(token)
    if not payload or payload.get("purpose") != "access":
        raise HTTPException(status_code=401, detail="Invalid or expired access token", headers={"WWW-Authenticate": "Bearer"})

    user_id = payload.get("sub")
    if not user_id or not str(user_id).isdigit():
        raise HTTPException(status_code=401, detail="Invalid access token", headers={"WWW-Authenticate": "Bearer"})

    user = db.query(User).filter(
        User.id == int(user_id),
        User.is_active.is_(True),
    ).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or inactive user", headers={"WWW-Authenticate": "Bearer"})

    return user


@router.post("/register", response_model=UserOut)
def register(data: UserCreate, db: Session = Depends(get_db)):
    if not settings.ALLOW_GUEST_ACCESS:
        raise HTTPException(status_code=403, detail="Public registration is disabled")
    if db.query(User).filter((User.email == data.email) | (User.username == data.username)).first():
        raise HTTPException(status_code=400, detail="Email or username already registered")
    user = User(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(
        User.username == form_data.username,
        User.is_active.is_(True),
    ).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.get("/google")
def google_login():
    return _oauth_start("google")


@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    if error:
        response = _oauth_error_redirect("sign_in_cancelled")
        response.delete_cookie(
            key="google_oauth_state",
            path=f"{settings.API_PREFIX}/auth/google/callback",
            secure=not settings.DEBUG,
            httponly=True,
            samesite="lax",
        )
        return response
    return await _oauth_callback("google", request, code, state, db)


@router.get("/github")
def github_login():
    return _oauth_start("github")


@router.get("/github/callback")
async def github_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    if error:
        response = _oauth_error_redirect("sign_in_cancelled")
        response.delete_cookie(
            key="github_oauth_state",
            path=f"{settings.API_PREFIX}/auth/github/callback",
            secure=not settings.DEBUG,
            httponly=True,
            samesite="lax",
        )
        return response
    return await _oauth_callback("github", request, code, state, db)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
