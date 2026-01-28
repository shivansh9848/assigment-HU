from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.errors import bad_request, forbidden, not_found
from app.db.models import Artifact, Project, User
from app.db.session import get_db
from app.schemas.projects import ProjectCreate, ProjectResponse, ProjectWithArtifactsResponse
from app.services.storage import save_pdf_upload, validate_pdf_bytes


router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> ProjectResponse:
    product_request = (payload.product_request or "").strip()
    if not product_request:
        raise bad_request("Product Request cannot be empty")

    project = Project(owner_id=user.id, product_request=product_request)
    db.add(project)
    db.commit()
    db.refresh(project)
    return ProjectResponse.model_validate(project)


@router.get("", response_model=list[ProjectResponse])
def list_my_projects(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[ProjectResponse]:
    projects = db.query(Project).filter(Project.owner_id == user.id).order_by(Project.created_at.desc()).all()
    return [ProjectResponse.model_validate(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectWithArtifactsResponse)
def get_project(project_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> ProjectWithArtifactsResponse:
    project = db.get(Project, project_id)
    if not project:
        raise not_found("Project not found")
    if project.owner_id != user.id:
        raise forbidden("You can only access your own projects")

    artifacts = db.query(Artifact).filter(Artifact.project_id == project_id).order_by(Artifact.created_at.desc()).all()
    return ProjectWithArtifactsResponse(
        **ProjectResponse.model_validate(project).model_dump(),
        artifacts=[{
            "id": a.id,
            "kind": a.kind,
            "path": a.path,
            "original_filename": a.original_filename,
            "content_type": a.content_type,
            "size_bytes": a.size_bytes,
            "created_at": a.created_at,
        } for a in artifacts],
    )


@router.post("/{project_id}/documents", response_model=dict, status_code=status.HTTP_201_CREATED)
async def upload_project_pdf(
    project_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    project = db.get(Project, project_id)
    if not project:
        raise not_found("Project not found")
    if project.owner_id != user.id:
        raise forbidden("You can only upload to your own projects")

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise bad_request("Only PDF uploads are supported")

    settings = get_settings()
    max_bytes = settings.max_upload_mb * 1024 * 1024

    raw = await file.read()
    if not raw:
        raise bad_request("Uploaded file is empty")
    if len(raw) > max_bytes:
        raise bad_request(f"File too large (max {settings.max_upload_mb}MB)")

    try:
        validate_pdf_bytes(raw)
    except Exception:
        raise bad_request("Unsupported or corrupted PDF document")

    stored_path = save_pdf_upload(project_id=project_id, filename=file.filename, content=raw)

    artifact = Artifact(
        project_id=project_id,
        kind="supporting_document_pdf",
        path=str(stored_path.as_posix()),
        original_filename=file.filename,
        content_type=file.content_type or "application/pdf",
        size_bytes=len(raw),
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)

    return {"artifact_id": artifact.id, "project_id": project_id, "message": "PDF uploaded"}
