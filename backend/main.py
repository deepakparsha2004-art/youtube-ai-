"""YouTube AI Command Center - FastAPI Backend."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import traceback

from config import settings
from database import engine, init_db
from routers import auth, scripts, voice, videos, youtube, scheduler, analytics, settings as settings_router

allowed_origins = [
    origin.strip().rstrip("/")
    for origin in settings.FRONTEND_URL.split(",")
    if origin.strip()
]
if settings.DEBUG:
    allowed_origins.extend([
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ])

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered YouTube content automation platform",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
prefix = settings.API_PREFIX
app.include_router(auth.router, prefix=prefix)
app.include_router(scripts.router, prefix=prefix)
app.include_router(voice.router, prefix=prefix)
app.include_router(videos.router, prefix=prefix)
app.include_router(youtube.router, prefix=prefix)
app.include_router(scheduler.router, prefix=prefix)
app.include_router(analytics.router, prefix=prefix)
app.include_router(settings_router.router, prefix=prefix)


@app.on_event("startup")
def on_startup():
    if not settings.DEBUG:
        if engine.url.get_backend_name() != "postgresql":
            raise RuntimeError("Set DATABASE_URL to a Supabase PostgreSQL connection URL before production deployment")
        if engine.url.query.get("sslmode") != "require":
            raise RuntimeError("Supabase PostgreSQL connections must use SSL")
        if settings.ALLOW_GUEST_ACCESS:
            raise RuntimeError("ALLOW_GUEST_ACCESS must be false when DEBUG is false")
        if len(settings.SECRET_KEY) < 32 or settings.SECRET_KEY == "change-this-to-a-long-random-secret-key-in-production":
            raise RuntimeError("Set SECRET_KEY to a unique random value of at least 32 characters")
        if settings.DEFAULT_PASSWORD == "Admin@123" or len(settings.DEFAULT_PASSWORD) < 12:
            raise RuntimeError("Set DEFAULT_PASSWORD to a unique value of at least 12 characters")

    init_db()
    print(f"{settings.APP_NAME} v{settings.APP_VERSION} started")
    print("Docs: http://localhost:8000/docs")


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "status": "online",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if settings.DEBUG:
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "traceback": traceback.format_exc()},
        )
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
