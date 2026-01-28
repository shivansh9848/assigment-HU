from __future__ import annotations

import uuid
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from app.core.config import get_settings


def project_root(project_id: str) -> Path:
    settings = get_settings()
    root = settings.storage_root / "projects" / project_id
    root.mkdir(parents=True, exist_ok=True)
    return root


def save_pdf_upload(*, project_id: str, filename: str, content: bytes) -> Path:
    uploads_dir = project_root(project_id) / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(filename).name
    ext = ".pdf" if safe_name.lower().endswith(".pdf") else ""
    target = uploads_dir / f"{uuid.uuid4()}{ext}"
    target.write_bytes(content)
    return target


def validate_pdf_bytes(content: bytes) -> None:
    # Will raise if the PDF is invalid/corrupted.
    # PdfReader expects a file path or a file-like object, not raw bytes.
    reader = PdfReader(BytesIO(content), strict=False)
    _ = len(reader.pages)
