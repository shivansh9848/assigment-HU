from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.errors import forbidden, not_found
from app.db.models import Project, ResearchAppendix, Run, RunEvent, User
from app.db.session import get_db
from app.schemas.research import ResearchAppendixResponse
from app.schemas.run_events import RunEventResponse


router = APIRouter(prefix="/runs", tags=["run-events"])


@router.get("/{run_id}/events", response_model=list[RunEventResponse])
def list_run_events(run_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[RunEventResponse]:
    run = db.get(Run, run_id)
    if not run:
        raise not_found("Run not found")

    project = db.get(Project, run.project_id)
    if not project:
        raise not_found("Project not found")
    if project.owner_id != user.id:
        raise forbidden("You can only access your own runs")

    events = db.query(RunEvent).filter(RunEvent.run_id == run_id).order_by(RunEvent.created_at.asc()).all()
    return [
        RunEventResponse(
            id=e.id,
            run_id=e.run_id,
            level=e.level,
            event_type=e.event_type,
            message=e.message,
            payload_json=e.payload_json,
            created_at=e.created_at,
        )
        for e in events
    ]


@router.get("/{run_id}/research", response_model=ResearchAppendixResponse)
def get_research_appendix(run_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> ResearchAppendixResponse:
    run = db.get(Run, run_id)
    if not run:
        raise not_found("Run not found")

    project = db.get(Project, run.project_id)
    if not project:
        raise not_found("Project not found")
    if project.owner_id != user.id:
        raise forbidden("You can only access your own runs")

    appendix = db.query(ResearchAppendix).filter(ResearchAppendix.run_id == run_id).one_or_none()
    if not appendix:
        raise not_found("Research appendix not found for this run")

    settings = get_settings()
    md_path = settings.storage_root / Path(appendix.markdown_path)
    markdown = md_path.read_text(encoding="utf-8", errors="ignore") if md_path.exists() else ""

    return ResearchAppendixResponse(
        id=appendix.id,
        project_id=appendix.project_id,
        run_id=appendix.run_id,
        markdown=markdown,
        urls=json.loads(appendix.urls_json),
        summary=appendix.summary,
        impact=appendix.impact,
        created_at=appendix.created_at,
    )
