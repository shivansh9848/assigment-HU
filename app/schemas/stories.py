
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel
from app.db.models import StoryBatchStatus, StoryStatus

class StoryGenerateRequest(BaseModel):
    epic_id: str
    constraints: str | None = None
    count: int = 10

class StoryResponse(BaseModel):
    id: str
    project_id: str
    epic_id: str
    batch_id: str
    statement: str
    acceptance_criteria: list[str]
    edge_cases: str
    non_functional: str
    estimate: str
    estimate_reason: str
    dependencies: list[str]
    status: StoryStatus
    created_at: datetime
    feedback: str | None = None

class StoryBatchResponse(BaseModel):
    batch_id: str
    project_id: str
    epic_id: str
    run_id: str | None
    constraints: str
    status: StoryBatchStatus
    created_at: datetime
    stories: list[StoryResponse]

class StoryApproveRequest(BaseModel):
    approve_all: bool = True

class StoryUpdateRequest(BaseModel):
    status: StoryStatus
    feedback: str | None = None
