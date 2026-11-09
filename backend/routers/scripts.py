"""Script generation routes."""

import logging
from typing import List
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Script, User
from schemas import ScriptGenerateRequest, ScriptOut, ScriptUpdate
from services.script_service import generate_script, improve_script
from routers.auth import get_current_user
from config import settings

router = APIRouter(prefix="/scripts", tags=["Scripts"])
logger = logging.getLogger(__name__)


def _raise_ollama_unavailable(exc: httpx.RequestError) -> None:
    logger.warning("Ollama request failed at %s", settings.OLLAMA_BASE_URL, exc_info=exc)
    raise HTTPException(
        status_code=503,
        detail=(
            f"Cannot connect to Ollama at {settings.OLLAMA_BASE_URL}. "
            f"Start Ollama and install the configured model with "
            f"`ollama pull {settings.OLLAMA_MODEL}`, then try again."
        ),
    ) from exc


@router.post("/generate", response_model=ScriptOut)
async def create_script(
    request: ScriptGenerateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        script = await generate_script(db, user.id, request)
    except httpx.RequestError as exc:
        _raise_ollama_unavailable(exc)
    return script


@router.get("/", response_model=List[ScriptOut])
def list_scripts(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return (
        db.query(Script)
        .filter(Script.user_id == user.id)
        .order_by(Script.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{script_id}", response_model=ScriptOut)
def get_script(
    script_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    script = db.query(Script).filter(Script.id == script_id, Script.user_id == user.id).first()
    if not script:
        raise HTTPException(404, "Script not found")
    return script


@router.patch("/{script_id}", response_model=ScriptOut)
def update_script(
    script_id: int,
    data: ScriptUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    script = db.query(Script).filter(Script.id == script_id, Script.user_id == user.id).first()
    if not script:
        raise HTTPException(404, "Script not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(script, k, v)
    if data.content:
        script.word_count = len(data.content.split())
    db.commit()
    db.refresh(script)
    return script


@router.post("/{script_id}/improve", response_model=ScriptOut)
async def improve(
    script_id: int,
    instruction: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    script = db.query(Script).filter(Script.id == script_id, Script.user_id == user.id).first()
    if not script:
        raise HTTPException(404, "Script not found")
    try:
        return await improve_script(db, script, instruction)
    except httpx.RequestError as exc:
        _raise_ollama_unavailable(exc)


@router.delete("/{script_id}")
def delete_script(
    script_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    script = db.query(Script).filter(Script.id == script_id, Script.user_id == user.id).first()
    if not script:
        raise HTTPException(404, "Script not found")
    db.delete(script)
    db.commit()
    return {"ok": True}
