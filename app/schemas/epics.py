from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.db.models import EpicBatchStatus, EpicStatus


class EpicGenerateRequest(BaseModel):
    constraints: str | None = None
    count: int = 6


class EpicResponse(BaseModel):
    id: str
    project_id: str
    batch_id: str
    title: str
    goal: str
    in_scope: str
    out_of_scope: str
    priority: str
    priority_reason: str
    dependencies: list[str]
    risks: str
    assumptions: str
    open_questions: str
    success_metrics: str
    status: EpicStatus
    created_at: datetime


class EpicBatchResponse(BaseModel):
    batch_id: str
    project_id: str
    run_id: str | None
    constraints: str
    status: EpicBatchStatus
    created_at: datetime
    epics: list[EpicResponse]
    mermaid: str


class EpicApproveRequest(BaseModel):
    approve_all: bool = True


class EpicUpdateRequest(BaseModel):
    status: EpicStatus
    feedback: str | None = None
