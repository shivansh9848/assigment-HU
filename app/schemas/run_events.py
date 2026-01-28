from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.db.models import RunEventLevel


class RunEventResponse(BaseModel):
    id: str
    run_id: str
    level: RunEventLevel
    event_type: str
    message: str
    payload_json: str | None
    created_at: datetime
