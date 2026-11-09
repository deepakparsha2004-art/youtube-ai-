"""Helper utilities."""

from pathlib import Path
from fastapi import HTTPException
from config import settings


def safe_path(base: Path, filename: str) -> Path:
    """Prevent path traversal."""
    path = (base / filename).resolve()
    if not str(path).startswith(str(base.resolve())):
        raise HTTPException(status_code=400, detail="Invalid path")
    return path


def ensure_file_exists(path: str) -> Path:
    p = Path(path)
    if not p.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return p
