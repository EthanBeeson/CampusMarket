"""
Helpers for file storage so uploads can live in a shared folder.

Configure with env var UPLOADS_BASE_DIR (defaults to "uploads").
All helpers ensure target directories exist.
"""
import os
from pathlib import Path


def get_upload_root() -> str:
    root = os.getenv("UPLOADS_BASE_DIR", "uploads")
    Path(root).mkdir(parents=True, exist_ok=True)
    return root


def get_upload_subdir(subdir: str | None = None) -> str:
    root = get_upload_root()
    target = Path(root) / subdir if subdir else Path(root)
    target.mkdir(parents=True, exist_ok=True)
    return str(target)


def build_upload_path(subdir: str | None, filename: str) -> str:
    target_dir = Path(get_upload_subdir(subdir))
    return str(target_dir / filename)
