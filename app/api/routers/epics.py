from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.errors import bad_request, forbidden, not_found
from app.db.models import Epic, EpicBatch, EpicBatchStatus, EpicStatus, Project, ResearchAppendix, Run, RunStatus, User
from app.db.session import get_db
from app.schemas.epics import (
    EpicApproveRequest,
    EpicBatchResponse,
    EpicGenerateRequest,
    EpicResponse,
    EpicUpdateRequest,
)
from app.services.epic_generation import generate_epics, make_mermaid_dependency_graph
from app.services.run_events import emit_run_event
from app.services.storage import project_root


router = APIRouter(prefix="/projects", tags=["epics"])


def _ensure_project_owner(db: Session, *, project_id: str, user: User) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise not_found("Project not found")
    if project.owner_id != user.id:
        raise forbidden("You can only access your own projects")
    return project


def _latest_research(db: Session, *, project_id: str) -> ResearchAppendix | None:
    return (
        db.query(ResearchAppendix)
        .filter(ResearchAppendix.project_id == project_id)
        .order_by(ResearchAppendix.created_at.desc())
        .first()
    )


@router.post("/{project_id}/epics/generate", response_model=EpicBatchResponse, status_code=status.HTTP_201_CREATED)
def generate_project_epics(
    project_id: str,
    payload: EpicGenerateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EpicBatchResponse:
    project = _ensure_project_owner(db, project_id=project_id, user=user)

    research = _latest_research(db, project_id=project_id)
    if not research:
        raise bad_request("Milestone 3 requires research first. Run backlog generation (Milestone 2) to create a research appendix.")

    constraints = (payload.constraints or "").strip()
    count = max(1, min(payload.count, 12))

    run = Run(project_id=project_id, run_type="epic_generation", status=RunStatus.started)
    db.add(run)
    db.commit()
    db.refresh(run)

    emit_run_event(db, run_id=run.id, event_type="epics.started", message="Epic generation started")

    citations = json.loads(research.urls_json) if research.urls_json else []
    gen = generate_epics(
        product_request=project.product_request,
        research_summary=research.summary,
        citations=citations,
        constraints=constraints,
        count=count,
    )

    batch = EpicBatch(project_id=project_id, run_id=run.id, constraints=constraints, status=EpicBatchStatus.generated)
    db.add(batch)
    db.commit()
    db.refresh(batch)

    epic_rows: list[Epic] = []
    for e in gen:
        row = Epic(
            project_id=project_id,
            batch_id=batch.id,
            title=e.title,
            goal=e.goal,
            in_scope=e.in_scope,
            out_of_scope=e.out_of_scope,
            priority=e.priority,
            priority_reason=e.priority_reason,
            dependencies_json=json.dumps(e.dependencies, ensure_ascii=False),
            risks=e.risks,
            assumptions=e.assumptions,
            open_questions=e.open_questions,
            success_metrics=e.success_metrics,
            status=EpicStatus.proposed,
        )
        epic_rows.append(row)
        db.add(row)

    db.commit()

    mermaid = make_mermaid_dependency_graph(gen)

    # Persist Mermaid diagram artifact
    settings = get_settings()
    run_dir = project_root(project_id) / "runs" / run.id
    run_dir.mkdir(parents=True, exist_ok=True)
    mmd_path = run_dir / "epic_dependency_graph.mmd"
    mmd_path.write_text(mermaid, encoding="utf-8")

    emit_run_event(db, run_id=run.id, event_type="epics.generated", message=f"Generated {len(epic_rows)} epics")
    emit_run_event(db, run_id=run.id, event_type="epics.mermaid", message="Mermaid dependency graph saved", payload={"path": str(mmd_path)})

    run.status = RunStatus.completed
    db.commit()

    epics_resp: list[EpicResponse] = []
    for row in db.query(Epic).filter(Epic.batch_id == batch.id).order_by(Epic.created_at.asc()).all():
        epics_resp.append(
            EpicResponse(
                id=row.id,
                project_id=row.project_id,
                batch_id=row.batch_id,
                title=row.title,
                goal=row.goal,
                in_scope=row.in_scope,
                out_of_scope=row.out_of_scope,
                priority=row.priority,
                priority_reason=row.priority_reason,
                dependencies=json.loads(row.dependencies_json or "[]"),
                risks=row.risks,
                assumptions=row.assumptions,
                open_questions=row.open_questions,
                success_metrics=row.success_metrics,
                status=row.status,
                created_at=row.created_at,
            )
        )

    return EpicBatchResponse(
        batch_id=batch.id,
        project_id=batch.project_id,
        run_id=batch.run_id,
        constraints=batch.constraints,
        status=batch.status,
        created_at=batch.created_at,
        epics=epics_resp,
        mermaid=mermaid,
    )


@router.get("/{project_id}/epics", response_model=EpicBatchResponse)
def get_latest_epic_batch(
    project_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EpicBatchResponse:
    _ensure_project_owner(db, project_id=project_id, user=user)

    batch = (
        db.query(EpicBatch)
        .filter(EpicBatch.project_id == project_id)
        .order_by(EpicBatch.created_at.desc())
        .first()
    )
    if not batch:
        raise not_found("No epic batch found. Generate epics first.")

    epics = db.query(Epic).filter(Epic.batch_id == batch.id).order_by(Epic.created_at.asc()).all()
    epics_resp = [
        EpicResponse(
            id=e.id,
            project_id=e.project_id,
            batch_id=e.batch_id,
            title=e.title,
            goal=e.goal,
            in_scope=e.in_scope,
            out_of_scope=e.out_of_scope,
            priority=e.priority,
            priority_reason=e.priority_reason,
            dependencies=json.loads(e.dependencies_json or "[]"),
            risks=e.risks,
            assumptions=e.assumptions,
            open_questions=e.open_questions,
            success_metrics=e.success_metrics,
            status=e.status,
            created_at=e.created_at,
        )
        for e in epics
    ]

    # Attempt to load mermaid file from run folder (if available)
    mermaid = ""
    if batch.run_id:
        run = db.get(Run, batch.run_id)
        if run:
            settings = get_settings()
            mmd_path = project_root(project_id) / "runs" / run.id / "epic_dependency_graph.mmd"
            if mmd_path.exists():
                mermaid = mmd_path.read_text(encoding="utf-8", errors="ignore")

    return EpicBatchResponse(
        batch_id=batch.id,
        project_id=batch.project_id,
        run_id=batch.run_id,
        constraints=batch.constraints,
        status=batch.status,
        created_at=batch.created_at,
        epics=epics_resp,
        mermaid=mermaid,
    )


@router.post("/{project_id}/epics/{batch_id}/approve", response_model=dict)
def approve_epic_batch(
    project_id: str,
    batch_id: str,
    payload: EpicApproveRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    _ensure_project_owner(db, project_id=project_id, user=user)

    batch = db.get(EpicBatch, batch_id)
    if not batch or batch.project_id != project_id:
        raise not_found("Epic batch not found")

    if payload.approve_all:
        db.query(Epic).filter(Epic.batch_id == batch_id).update({Epic.status: EpicStatus.approved})

    batch.status = EpicBatchStatus.approved
    db.commit()

    if batch.run_id:
        emit_run_event(db, run_id=batch.run_id, event_type="epics.approved", message="Epics approved")

    return {"message": "Approved", "batch_id": batch_id}


@router.patch("/epics/{epic_id}", response_model=dict)
def update_epic_status(
    epic_id: str,
    payload: EpicUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    epic = db.get(Epic, epic_id)
    if not epic:
        raise not_found("Epic not found")

    project = db.get(Project, epic.project_id)
    if not project or project.owner_id != user.id:
        raise forbidden("You can only update your own epics")

    epic.status = payload.status
    db.commit()

    # Feedback is accepted but not persisted yet (kept simple for Milestone 3).
    return {"message": "Updated", "epic_id": epic_id, "status": epic.status}
