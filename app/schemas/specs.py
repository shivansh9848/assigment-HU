
from __future__ import annotations

from typing import Any, List, Optional
from datetime import datetime
from pydantic import BaseModel
from enum import Enum


class SpecStatus(str, Enum):
    proposed = "proposed"
    approved = "approved"
    rejected = "rejected"


class SpecSummary(BaseModel):
    id: str
    project_id: str
    story_id: str
    version: int
    status: SpecStatus
    constraints: Optional[str] = None
    feedback: Optional[str] = None
    mermaid_sequence: Optional[str] = None
    mermaid_er: Optional[str] = None


class SpecFull(BaseModel):
    id: str
    project_id: str
    story_id: str
    version: int
    status: SpecStatus
    constraints: Optional[str] = None
    feedback: Optional[str] = None
    overview: Optional[str] = None
    goals: Optional[str] = None
    functional_requirements: List[Any] = []
    api_contracts: List[Any] = []
    data_model_changes: List[Any] = []
    security_considerations: Optional[str] = None
    error_handling: Optional[str] = None
    observability: Optional[str] = None
    test_plan: List[Any] = []
    implementation_plan: List[Any] = []
    mermaid_sequence: Optional[str] = None
    mermaid_er: Optional[str] = None
    created_at: datetime
