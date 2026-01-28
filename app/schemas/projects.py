from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProjectCreate(BaseModel):
    product_request: str


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: str
    product_request: str
    created_at: datetime


class ArtifactResponse(BaseModel):
    id: str
    kind: str
    path: str
    original_filename: str
    content_type: str
    size_bytes: int
    created_at: datetime


class ProjectWithArtifactsResponse(ProjectResponse):
    artifacts: list[ArtifactResponse]
