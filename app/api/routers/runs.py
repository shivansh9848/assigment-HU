from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.errors import forbidden, not_found
from app.db.models import Project, Run, RunStatus, User
from app.db.session import get_db
from app.schemas.runs import RunResponse


router = APIRouter(prefix="/projects", tags=["runs"])


@router.post("/{project_id}/runs/backlog", response_model=RunResponse, status_code=status.HTTP_202_ACCEPTED)
def start_backlog_generation(project_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> RunResponse:
    project = db.get(Project, project_id)
    if not project:
        raise not_found("Project not found")
    if project.owner_id != user.id:
        raise forbidden("You can only start runs for your own projects")

    run = Run(project_id=project_id, run_type="backlog_generation", status=RunStatus.started)
    db.add(run)
    db.commit()
    db.refresh(run)

    return RunResponse(
        id=run.id,
        project_id=run.project_id,
        run_type=run.run_type,
        status=run.status,
        message="Backlog Generation Started",
    )
