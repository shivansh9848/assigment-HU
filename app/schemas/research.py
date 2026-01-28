from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ResearchAppendixResponse(BaseModel):
    id: str
    project_id: str
    run_id: str
    markdown: str
    urls: list[str]
    summary: str
    impact: str
    created_at: datetime
