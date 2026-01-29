
from __future__ import annotations

import json
from functools import partial

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.errors import bad_request, forbidden, not_found
from app.db.models import (
    Project, Epic, EpicStatus, Run, RunStatus,
    StoryBatch, Story, StoryBatchStatus, StoryStatus, User,
)
from app.db.session import get_db
from app.schemas.stories import (
    StoryGenerateRequest, StoryBatchResponse, StoryResponse, StoryApproveRequest, StoryUpdateRequest,
)
from app.services.run_events import emit_run_event
from app.services.story_generation import generate_stories

router = APIRouter(prefix="/projects", tags=["stories"])

def _ensure_project_owner(db: Session, *, project_id: str, user: User) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise not_found("Project not found")
    if project.owner_id != user.id:
        raise forbidden("You can only access your own projects")
    return project

@router.post("/{project_id}/stories/generate", response_model=StoryBatchResponse, status_code=status.HTTP_201_CREATED)
def generate_epic_stories(
    project_id: str,
    payload: StoryGenerateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> StoryBatchResponse:
    _ensure_project_owner(db, project_id=project_id, user=user)

    epic = db.get(Epic, payload.epic_id)
    if not epic or epic.project_id != project_id:
        raise not_found("Epic not found")
    if epic.status != EpicStatus.approved:
        raise bad_request("User stories require an approved epic (Milestone 3 approval gate).")

    constraints = (payload.constraints or "").strip()
    count = max(1, min(int(payload.count), 25))

    run = Run(project_id=project_id, run_type="story_generation", status=RunStatus.started)
    db.add(run)
    db.commit()
    db.refresh(run)

    emit_run_event(db, run_id=run.id, event_type="stories.started", message="Story generation started")

    gen = generate_stories(
        product_request=db.get(Project, project_id).product_request,
        epic_title=epic.title,
        epic_goal=epic.goal,
        constraints=constraints,
        count=count,
    )

    batch = StoryBatch(project_id=project_id, epic_id=epic.id, run_id=run.id, constraints=constraints, status=StoryBatchStatus.generated)
    db.add(batch)
    db.commit()
    db.refresh(batch)

    story_rows: list[Story] = []
    for s in gen:
        row = Story(
            project_id=project_id,
            epic_id=epic.id,
            batch_id=batch.id,
            statement=s.statement,
            acceptance_criteria_json=json.dumps(s.acceptance_criteria, ensure_ascii=False),
            edge_cases=s.edge_cases,
            non_functional=s.non_functional,
            estimate=s.estimate,
            estimate_reason=s.estimate_reason,
            dependencies_json=json.dumps(s.dependencies, ensure_ascii=False),
            status=StoryStatus.proposed,
        )
        story_rows.append(row)

    db.add_all(story_rows)
    db.commit()

    emit_run_event(db, run_id=run.id, event_type="stories.generated", message=f"Generated {len(story_rows)} stories")
    run.status = RunStatus.completed
    db.commit()

    stories_resp: list[StoryResponse] = []
    for row in db.query(Story).filter(Story.batch_id == batch.id).order_by(Story.created_at.asc()).all():
        stories_resp.append(
            StoryResponse(
                id=row.id,
                project_id=row.project_id,
                epic_id=row.epic_id,
                batch_id=row.batch_id,
                statement=row.statement,
                acceptance_criteria=json.loads(row.acceptance_criteria_json or "[]"),
                edge_cases=row.edge_cases,
                non_functional=row.non_functional,
                estimate=row.estimate,
                estimate_reason=row.estimate_reason,
                dependencies=json.loads(row.dependencies_json or "[]"),
                status=row.status,
                created_at=row.created_at,
                feedback=row.feedback,
            )
        )

    return StoryBatchResponse(
        batch_id=batch.id,
        project_id=batch.project_id,
        epic_id=batch.epic_id,
        run_id=batch.run_id,
        constraints=batch.constraints,
        status=batch.status,
        created_at=batch.created_at,
        stories=stories_resp,
    )

@router.get("/{project_id}/stories", response_model=StoryBatchResponse)
def get_latest_story_batch(
    project_id: str,
    epic_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> StoryBatchResponse:
    _ensure_project_owner(db, project_id=project_id, user=user)

    batch = (
        db.query(StoryBatch)
        .filter(StoryBatch.project_id == project_id, StoryBatch.epic_id == epic_id)
        .order_by(StoryBatch.created_at.desc())
        .first()
    )
    if not batch:
        raise not_found("No story batch found for this epic. Generate stories first.")

    rows = db.query(Story).filter(Story.batch_id == batch.id).order_by(Story.created_at.asc()).all()
    stories_resp = [
        StoryResponse(
            id=r.id,
            project_id=r.project_id,
            epic_id=r.epic_id,
            batch_id=r.batch_id,
            statement=r.statement,
            acceptance_criteria=json.loads(r.acceptance_criteria_json or "[]"),
            edge_cases=r.edge_cases,
            non_functional=r.non_functional,
            estimate=r.estimate,
            estimate_reason=r.estimate_reason,
            dependencies=json.loads(r.dependencies_json or "[]"),
            status=r.status,
            created_at=r.created_at,
            feedback=r.feedback,
        )
        for r in rows
    ]

    return StoryBatchResponse(
        batch_id=batch.id,
        project_id=batch.project_id,
        epic_id=batch.epic_id,
        run_id=batch.run_id,
        constraints=batch.constraints,
        status=batch.status,
        created_at=batch.created_at,
        stories=stories_resp,
    )

@router.post("/{project_id}/stories/{batch_id}/approve", response_model=dict)
def approve_story_batch(
    project_id: str,
    batch_id: str,
    payload: StoryApproveRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    _ensure_project_owner(db, project_id=project_id, user=user)

    batch = db.get(StoryBatch, batch_id)
    if not batch or batch.project_id != project_id:
        raise not_found("Story batch not found")

    if payload.approve_all:
        db.query(Story).filter(Story.batch_id == batch_id).update({Story.status: StoryStatus.approved})

    batch.status = StoryBatchStatus.approved
    db.commit()

    if batch.run_id:
        emit_run_event(db, run_id=batch.run_id, event_type="stories.approved", message="Stories approved")

    return {"message": "Approved", "batch_id": batch_id}

@router.patch("/stories/{story_id}", response_model=dict)
def update_story_status(
    story_id: str,
    payload: StoryUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    row = db.get(Story, story_id)
    if not row:
        raise not_found("Story not found")

    project = db.get(Project, row.project_id)
    if not project or project.owner_id != user.id:
        raise forbidden("You can only update your own stories")

    row.status = payload.status
    row.feedback = (payload.feedback or None)
    db.commit()
    return {"message": "Updated", "story_id": story_id, "status": row.status}
