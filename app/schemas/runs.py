from __future__ import annotations

from pydantic import BaseModel

from app.db.models import RunStatus


class RunResponse(BaseModel):
    id: str
    project_id: str
    run_type: str
    status: RunStatus
    message: str
