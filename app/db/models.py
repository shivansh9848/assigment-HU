from __future__ import annotations

from datetime import datetime
import enum
import json
import uuid
from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func, Column
from sqlalchemy import (
    Column, String, Text, DateTime, Enum, Integer, ForeignKey, Index
)

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.base import Base  
class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"


class RunStatus(str, enum.Enum):
    started = "started"
    completed = "completed"
    failed = "failed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.user)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    projects: Mapped[list[Project]] = relationship(back_populates="owner", cascade="all, delete-orphan")  # type: ignore[name-defined]


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    product_request: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped[User] = relationship(back_populates="projects")
    artifacts: Mapped[list[Artifact]] = relationship(back_populates="project", cascade="all, delete-orphan")  # type: ignore[name-defined]
    runs: Mapped[list[Run]] = relationship(back_populates="project", cascade="all, delete-orphan")  # type: ignore[name-defined]


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), index=True)
    kind: Mapped[str] = mapped_column(String(50))
    path: Mapped[str] = mapped_column(String(500))
    original_filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped[Project] = relationship(back_populates="artifacts")


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), index=True)
    run_type: Mapped[str] = mapped_column(String(50))
    status: Mapped[RunStatus] = mapped_column(Enum(RunStatus), default=RunStatus.started)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    project: Mapped[Project] = relationship(back_populates="runs")


class RunEventLevel(str, enum.Enum):
    info = "info"
    warning = "warning"
    error = "error"


class RunEvent(Base):
    __tablename__ = "run_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("runs.id"), index=True)
    level: Mapped[RunEventLevel] = mapped_column(Enum(RunEventLevel), default=RunEventLevel.info)
    event_type: Mapped[str] = mapped_column(String(80))
    message: Mapped[str] = mapped_column(Text)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ResearchAppendix(Base):
    __tablename__ = "research_appendices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), index=True)
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("runs.id"), index=True, unique=True)
    markdown_path: Mapped[str] = mapped_column(String(500))
    urls_json: Mapped[str] = mapped_column(Text)
    summary: Mapped[str] = mapped_column(Text)
    impact: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EpicBatchStatus(str, enum.Enum):
    generated = "generated"
    approved = "approved"


class EpicStatus(str, enum.Enum):
    proposed = "proposed"
    approved = "approved"
    rejected = "rejected"
    changes_requested = "changes_requested"  # NEW


class EpicBatch(Base):
    __tablename__ = "epic_batches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), index=True)
    run_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("runs.id"), index=True, nullable=True)
    constraints: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[EpicBatchStatus] = mapped_column(Enum(EpicBatchStatus), default=EpicBatchStatus.generated)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Epic(Base):
    __tablename__ = "epics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), index=True)
    batch_id: Mapped[str] = mapped_column(String(36), ForeignKey("epic_batches.id"), index=True)

    title: Mapped[str] = mapped_column(String(200))
    goal: Mapped[str] = mapped_column(Text)
    in_scope: Mapped[str] = mapped_column(Text)
    out_of_scope: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(10))
    priority_reason: Mapped[str] = mapped_column(Text)
    dependencies_json: Mapped[str] = mapped_column(Text, default="[]")
    risks: Mapped[str] = mapped_column(Text)
    assumptions: Mapped[str] = mapped_column(Text)
    open_questions: Mapped[str] = mapped_column(Text)
    success_metrics: Mapped[str] = mapped_column(Text)
    status: Mapped[EpicStatus] = mapped_column(Enum(EpicStatus), default=EpicStatus.proposed)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)


class StoryBatchStatus(str, enum.Enum):
    generated = "generated"
    approved = "approved"


class StoryStatus(str, enum.Enum):
    proposed = "proposed"
    approved = "approved"
    rejected = "rejected"
    changes_requested = "changes_requested"


class StoryBatch(Base):
    __tablename__ = "story_batches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), index=True)
    epic_id: Mapped[str] = mapped_column(String(36), ForeignKey("epics.id"), index=True)
    run_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("runs.id"), index=True, nullable=True)
    constraints: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[StoryBatchStatus] = mapped_column(Enum(StoryBatchStatus), default=StoryBatchStatus.generated)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Story(Base):
    __tablename__ = "stories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), index=True)
    epic_id: Mapped[str] = mapped_column(String(36), ForeignKey("epics.id"), index=True)
    batch_id: Mapped[str] = mapped_column(String(36), ForeignKey("story_batches.id"), index=True)

    # Required fields from Milestone 4 brief:
    # - user story statement, acceptance criteria, edge cases, NFRs, estimate, dependencies
    statement: Mapped[str] = mapped_column(Text)  # “As a <role>, I want <need>, so that <benefit>”
    acceptance_criteria_json: Mapped[str] = mapped_column(Text, default="[]")  # list[str] (Given/When/Then)
    edge_cases: Mapped[str] = mapped_column(Text, default="")
    non_functional: Mapped[str] = mapped_column(Text, default="")  # performance/security/privacy if relevant
    estimate: Mapped[str] = mapped_column(String(50), default="M")  # t-shirt size by default
    estimate_reason: Mapped[str] = mapped_column(Text, default="")
    dependencies_json: Mapped[str] = mapped_column(Text, default="[]")  # list[str]
    status: Mapped[StoryStatus] = mapped_column(Enum(StoryStatus), default=StoryStatus.proposed)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())




class SpecStatus(str, enum.Enum):
    proposed = "proposed"
    approved = "approved"
    rejected = "rejected"


class SpecDocument(Base):
    __tablename__ = "spec_documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    story_id = Column(String, ForeignKey("stories.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)

    # Inputs / governance
    constraints = Column(Text, nullable=True)
    feedback = Column(Text, nullable=True)
    status = Column(Enum(SpecStatus), nullable=False, default=SpecStatus.proposed)

    # Spec content
    overview = Column(Text, nullable=True)
    goals = Column(Text, nullable=True)
    functional_requirements_json = Column(Text, nullable=True)
    api_contracts_json = Column(Text, nullable=True)
    data_model_changes_json = Column(Text, nullable=True)
    security_considerations = Column(Text, nullable=True)
    error_handling = Column(Text, nullable=True)
    observability = Column(Text, nullable=True)
    test_plan_json = Column(Text, nullable=True)
    implementation_plan_json = Column(Text, nullable=True)

    # Mermaid diagrams
    mermaid_sequence = Column(Text, nullable=True)
    mermaid_er = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    project = relationship("Project", lazy="joined")
    story = relationship("Story", lazy="joined")

Index("ix_spec_documents_story_version", SpecDocument.story_id, SpecDocument.version, unique=True)