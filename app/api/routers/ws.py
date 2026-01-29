from __future__ import annotations

import asyncio
import anyio
import json
from functools import partial
from typing import Any, Iterable

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, Depends
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.services.run_events import emit_run_event

from fastapi import status
from app.core.config import get_settings
from app.api.deps import get_current_user  # if used in this file
from app.core.errors import forbidden, not_found, bad_request  # as used
from app.core.events import broker
from app.db.session import SessionLocal, get_db
from app.db.models import (
    User, Project, Run, RunStatus,
    Epic, EpicStatus, EpicBatch, EpicBatchStatus,
    ResearchAppendix,
    StoryBatch, Story, StoryBatchStatus, StoryStatus,SpecDocument, SpecStatus
)
from app.services.spec_generation import generate_spec_for_story
from app.services.run_events import emit_run_event

router = APIRouter(tags=["websocket"])


def _decode_ws_jwt_or_none(token: str | None) -> str | None:
    if not token:
        return None
    settings = get_settings()
    try:
        claims = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id: str | None = claims.get("sub")
        return user_id
    except JWTError:
        return None


def _latest_research(db: Session, *, project_id: str) -> ResearchAppendix | None:
    return (
        db.query(ResearchAppendix)
        .filter(ResearchAppendix.project_id == project_id)
        .order_by(ResearchAppendix.created_at.desc())
        .first()
    )


def _epic_to_dict(e: Epic) -> dict[str, Any]:
    return {
        "id": str(e.id),
        "project_id": str(e.project_id),
        "batch_id": str(e.batch_id),
        "title": e.title,
        "goal": e.goal,
        "priority": e.priority,
        "priority_reason": e.priority_reason,
        "status": e.status.value if hasattr(e.status, "value") else str(e.status),
        "in_scope": e.in_scope,
        "out_of_scope": e.out_of_scope,
        "dependencies": json.loads(e.dependencies_json) if e.dependencies_json else [],
        "risks": e.risks,
        "assumptions": e.assumptions,
        "open_questions": e.open_questions,
        "success_metrics": e.success_metrics,
        "created_at": e.created_at.isoformat() if getattr(e, "created_at", None) else None,
        "updated_at": e.updated_at.isoformat() if getattr(e, "updated_at", None) else None,
    }


def _epics_summary(epics: Iterable[Epic]) -> list[dict[str, Any]]:
    return [_epic_to_dict(e) for e in epics]


def _generate_epics_job(*, project_id: str, run_id: str, constraints: str, count: int) -> dict[str, Any]:
    """
    Worker thread job.
    Persists epics + batch; emits run events; returns {"batch_id":..., "epics":[...], "mermaid_path": "..."}.
    """
    db = SessionLocal()
    try:
        project = db.get(Project, project_id)
        if not project:
            raise not_found("Project not found")

        research = _latest_research(db, project_id=project_id)
        if not research:
            raise bad_request(
                "Milestone 3 requires research first. Run backlog generation (Milestone 2) to create a research appendix."
            )

        emit_run_event(db, run_id=run_id, event_type="epics.started", message="Epic generation started")

        citations = json.loads(research.urls_json) if research.urls_json else []
        gen = generate_epics(
            product_request=project.product_request,
            research_summary=research.summary,
            citations=citations,
            constraints=constraints,
            count=count,
        )

        batch = EpicBatch(project_id=project_id, run_id=run_id, constraints=constraints, status=EpicBatchStatus.generated)
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

        run_dir = project_root(project_id) / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        mmd_path = run_dir / "epic_dependency_graph.mmd"
        mmd_path.write_text(mermaid, encoding="utf-8")

        epics_payload = _epics_summary(epic_rows)

        emit_run_event(
            db,
            run_id=run_id,
            event_type="epics.generated",
            message=f"Generated {len(epic_rows)} epics",
            payload={"batch_id": str(batch.id), "constraints": constraints, "epics": epics_payload},
        )
        emit_run_event(
            db,
            run_id=run_id,
            event_type="epics.mermaid",
            message="Mermaid dependency graph saved",
            payload={"path": str(mmd_path)},
        )

        run = db.get(Run, run_id)
        if run:
            run.status = RunStatus.completed
            db.commit()

        return {"batch_id": str(batch.id), "constraints": constraints, "epics": epics_payload, "mermaid_path": str(mmd_path)}

    except Exception as ex:
        try:
            emit_run_event(
                db,
                run_id=run_id,
                event_type="epics.error",
                message=f"Epic generation failed: {type(ex).__name__}: {ex}",
            )
            run = db.get(Run, run_id)
            if run:
                run.status = RunStatus.failed
                db.commit()
        except Exception:
            pass
        raise
    finally:
        db.close()


def _approve_epics_job(*, project_id: str, batch_id: str, approve_all: bool) -> dict[str, Any]:
    """
    Worker thread job.
    Approves epics; emits epics.approved; returns {"run_id":..., "epics":[...]}.
    """
    db = SessionLocal()
    try:
        batch = db.get(EpicBatch, batch_id)
        if not batch or str(batch.project_id) != str(project_id):
            raise not_found("Epic batch not found")

        if approve_all:
            db.query(Epic).filter(Epic.batch_id == batch_id).update({Epic.status: EpicStatus.approved})

        batch.status = EpicBatchStatus.approved
        db.commit()

        epics = db.query(Epic).filter(Epic.batch_id == batch_id).all()
        epics_payload = _epics_summary(epics)

        run_id = str(batch.run_id) if batch.run_id else ""
        if run_id:
            emit_run_event(
                db,
                run_id=run_id,
                event_type="epics.approved",
                message="Epics approved",
                payload={"batch_id": str(batch.id), "epics": epics_payload},
            )

        return {"run_id": run_id, "epics": epics_payload}
    finally:
        db.close()


@router.websocket("/ws/runs/{run_id}")
async def ws_run_events(websocket: WebSocket, run_id: str) -> None:
    token = websocket.query_params.get("token")
    user_id = _decode_ws_jwt_or_none(token)
    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    db_gen = get_db()
    db: Session = next(db_gen)
    try:
        run = db.get(Run, run_id)
        if not run:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        project = db.get(Project, run.project_id)
        if not project or str(project.owner_id) != str(user_id):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await websocket.accept()

        queue = await broker.subscribe(str(run_id))
        try:
            await websocket.send_json({"type": "ws.connected", "run_id": run_id})
            while True:
                evt: dict[str, Any] = await queue.get()
                await websocket.send_json(evt)
        except WebSocketDisconnect:
            pass
        finally:
            await broker.unsubscribe(str(run_id), queue)
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass
        db.close()


@router.websocket("/ws/projects/{project_id}/epics")
async def ws_epics_control(websocket: WebSocket, project_id: str) -> None:
    """
    Commands:
      - {"type":"epics.generate","constraints":"...","count":6}
      - {"type":"epics.regenerate","constraints":"...","count":6}
      - {"type":"epics.approve","batch_id":"...","approve_all":true}
      - {"type":"epics.list","batch_id":"..."}             # fetch epics for a batch
      - {"type":"epics.latest"}                            # fetch latest batch + epics for project
      - {"type":"runs.attach","run_id":"..."}              # subscribe to an existing run's events
    """
    token = websocket.query_params.get("token")
    user_id = _decode_ws_jwt_or_none(token)
    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    db_gen = get_db()
    db: Session = next(db_gen)
    try:
        project = db.get(Project, project_id)
        if not project or str(project.owner_id) != str(user_id):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass
        db.close()

    await websocket.accept()
    await websocket.send_json({"type": "ws.connected", "scope": "epics", "project_id": project_id})

    current_queue: asyncio.Queue | None = None
    current_run_id: str | None = None
    forwarder_task: asyncio.Task | None = None

    async def _stop_forwarding() -> None:
        nonlocal current_queue, current_run_id, forwarder_task
        if forwarder_task:
            forwarder_task.cancel()
            try:
                await forwarder_task
            except Exception:
                pass
            forwarder_task = None
        if current_queue and current_run_id:
            await broker.unsubscribe(current_run_id, current_queue)
        current_queue = None
        current_run_id = None

    async def _start_forwarding(run_id: str) -> None:
        nonlocal current_queue, current_run_id, forwarder_task
        await _stop_forwarding()
        current_run_id = str(run_id)
        current_queue = await broker.subscribe(current_run_id)

        async def _forward_loop() -> None:
            assert current_queue is not None
            while True:
                evt = await current_queue.get()
                await websocket.send_json(evt)

        forwarder_task = asyncio.create_task(_forward_loop())
        await websocket.send_json({"type": "runs.attached", "run_id": current_run_id})

    async def _send_batch_summary(batch_id: str) -> None:
        db_local = SessionLocal()
        try:
            batch = db_local.get(EpicBatch, batch_id)
            if not batch:
                await websocket.send_json({"type": "error", "message": "Epic batch not found"})
                return
            epics = db_local.query(Epic).filter(Epic.batch_id == batch_id).all()
            await websocket.send_json(
                {
                    "type": "epics.batch.summary",
                    "batch_id": str(batch.id),
                    "project_id": str(batch.project_id),
                    "constraints": batch.constraints,
                    "status": batch.status.value if hasattr(batch.status, "value") else str(batch.status),
                    "epics": _epics_summary(epics),
                }
            )
        finally:
            db_local.close()

    async def _handle_generate(*, constraints: str | None, count: int | None) -> None:
        db_local = SessionLocal()
        try:
            research = _latest_research(db_local, project_id=project_id)
            if not research:
                await websocket.send_json(
                    {"type": "error", "message": "No research appendix found; run backlog generation first (Milestone 2)."}
                )
                return
        finally:
            db_local.close()

        constraints_norm = (constraints or "").strip()
        count_norm = max(1, min(int(count or 6), 12))

        db_local = SessionLocal()
        try:
            run = Run(project_id=project_id, run_type="epic_generation", status=RunStatus.started)
            db_local.add(run)
            db_local.commit()
            db_local.refresh(run)
            run_id = str(run.id)
        finally:
            db_local.close()

        await _start_forwarding(run_id)
        await websocket.send_json({"type": "epics.run.created", "run_id": run_id})

        try:
            result = await anyio.to_thread.run_sync(
                partial(
                    _generate_epics_job,
                    project_id=project_id,
                    run_id=run_id,
                    constraints=constraints_norm,
                    count=count_norm,
                )
            )
            batch_id = result["batch_id"]
            await websocket.send_json({"type": "epics.batch.created", "run_id": run_id, "batch_id": batch_id})
            # Also push a direct summary to this WS so the client immediately has the epics, regardless of run-event timing.
            await websocket.send_json(
                {
                    "type": "epics.batch.summary",
                    "run_id": run_id,
                    "batch_id": batch_id,
                    "constraints": result.get("constraints"),
                    "epics": result.get("epics", []),
                    "mermaid_path": result.get("mermaid_path"),
                }
            )
        except Exception as ex:
            await websocket.send_json(
                {"type": "error", "run_id": run_id, "message": f"Generation failed: {type(ex).__name__}: {ex}"}
            )

    async def _handle_approve(*, batch_id: str | None, approve_all: bool | None) -> None:
        if not batch_id:
            await websocket.send_json({"type": "error", "message": "batch_id is required"})
            return

        approve_all_norm = True if approve_all is None else bool(approve_all)

        db_local = SessionLocal()
        try:
            batch = db_local.get(EpicBatch, batch_id)
            if not batch or str(batch.project_id) != str(project_id):
                await websocket.send_json({"type": "error", "message": "Epic batch not found"})
                return
            batch_run_id = str(batch.run_id) if batch.run_id else ""
        finally:
            db_local.close()

        if batch_run_id:
            await _start_forwarding(batch_run_id)

        try:
            result = await anyio.to_thread.run_sync(
                partial(
                    _approve_epics_job,
                    project_id=project_id,
                    batch_id=str(batch_id),
                    approve_all=approve_all_norm,
                )
            )
            await websocket.send_json(
                {"type": "epics.approved", "batch_id": str(batch_id), "run_id": (result.get("run_id") or batch_run_id or None)}
            )
            # Return updated summary so client sees approved statuses immediately.
            await _send_batch_summary(str(batch_id))
        except Exception as ex:
            await websocket.send_json({"type": "error", "message": f"Approval failed: {type(ex).__name__}: {ex}"})

    async def _handle_list(*, batch_id: str | None) -> None:
        if not batch_id:
            await websocket.send_json({"type": "error", "message": "batch_id is required"})
            return
        await _send_batch_summary(str(batch_id))

    async def _handle_latest() -> None:
        db_local = SessionLocal()
        try:
            batch = (
                db_local.query(EpicBatch)
                .filter(EpicBatch.project_id == project_id)
                .order_by(EpicBatch.created_at.desc())
                .first()
            )
            if not batch:
                await websocket.send_json({"type": "epics.latest", "message": "No batches yet"})
                return
            epics = db_local.query(Epic).filter(Epic.batch_id == batch.id).all()
            await websocket.send_json(
                {
                    "type": "epics.latest",
                    "batch_id": str(batch.id),
                    "project_id": str(batch.project_id),
                    "constraints": batch.constraints,
                    "status": batch.status.value if hasattr(batch.status, "value") else str(batch.status),
                    "epics": _epics_summary(epics),
                }
            )
        finally:
            db_local.close()

    try:
        while True:
            try:
                msg = await websocket.receive_json()
            except WebSocketDisconnect:
                break
            except Exception:
                await websocket.send_json({"type": "error", "message": "Invalid JSON message"})
                continue

            msg_type = str(msg.get("type") or "").strip()

            if msg_type in ("epics.generate", "epics.regenerate"):
                await _handle_generate(constraints=msg.get("constraints"), count=msg.get("count"))
            elif msg_type == "epics.approve":
                await _handle_approve(batch_id=msg.get("batch_id"), approve_all=msg.get("approve_all"))
            elif msg_type == "epics.list":
                await _handle_list(batch_id=msg.get("batch_id"))
            elif msg_type == "epics.latest":
                await _handle_latest()
            elif msg_type == "runs.attach":
                run_id = str(msg.get("run_id") or "").strip()
                if not run_id:
                    await websocket.send_json({"type": "error", "message": "run_id is required"})
                    continue
                await _start_forwarding(run_id)
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            else:
                await websocket.send_json({"type": "error", "message": f"Unknown message type: {msg_type}"})
    finally:
        await _stop_forwarding()
        try:
            await websocket.close()
        except Exception:
            pass


# strories

def _ensure_project_owner(db: Session, *, project_id: str, user: User) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise not_found("Project not found")
    if project.owner_id != user.id:
        raise forbidden("You can only access your own projects")
    return project

def _stories_summary(rows: list[Story]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for r in rows:
        out.append(
            {
                "id": str(r.id),
                "statement": r.statement,
                "status": r.status.value if hasattr(r.status, "value") else str(r.status),
                "estimate": r.estimate,
            }
        )
    return out

@router.websocket("/ws/projects/{project_id}/stories")
async def ws_stories(websocket: WebSocket, project_id: str) -> None:
    token = websocket.query_params.get("token")
    user_id = _decode_ws_jwt_or_none(token)
    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    db_check = SessionLocal()
    try:
        user = db_check.get(User, user_id)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        _ensure_project_owner(db_check, project_id=project_id, user=user)
    finally:
        db_check.close()

    await websocket.accept()
    await websocket.send_json({"type": "ws.connected", "scope": "stories", "project_id": project_id})

    current_queue: asyncio.Queue | None = None
    current_run_id: str | None = None
    forwarder_task: asyncio.Task | None = None

    async def _stop_forwarding() -> None:
        nonlocal current_queue, current_run_id, forwarder_task
        if forwarder_task:
            forwarder_task.cancel()
            try:
                await forwarder_task
            except Exception:
                pass
            forwarder_task = None
        if current_queue and current_run_id:
            await broker.unsubscribe(current_run_id, current_queue)
        current_queue = None
        current_run_id = None

    async def _start_forwarding(run_id: str) -> None:
        nonlocal current_queue, current_run_id, forwarder_task
        await _stop_forwarding()
        current_run_id = str(run_id)
        current_queue = await broker.subscribe(current_run_id)

        async def _forward_loop() -> None:
            assert current_queue is not None
            while True:
                evt: dict[str, Any] = await current_queue.get()
                await websocket.send_json(evt)

        forwarder_task = asyncio.create_task(_forward_loop())
        await websocket.send_json({"type": "runs.attached", "run_id": current_run_id})

    async def _send_batch_summary(batch_id: str) -> None:
        db_local = SessionLocal()
        try:
            batch = db_local.get(StoryBatch, batch_id)
            if not batch:
                await websocket.send_json({"type": "error", "message": "Story batch not found"})
                return
            rows = db_local.query(Story).filter(Story.batch_id == batch_id).all()
            await websocket.send_json(
                {
                    "type": "stories.batch.summary",
                    "batch_id": str(batch.id),
                    "project_id": str(batch.project_id),
                    "epic_id": str(batch.epic_id),
                    "constraints": batch.constraints,
                    "status": batch.status.value if hasattr(batch.status, "value") else str(batch.status),
                    "stories": _stories_summary(rows),
                }
            )
        finally:
            db_local.close()

    async def _generate_job(*, project_id: str, epic_id: str, constraints: str, count: int) -> dict[str, Any]:
        db_local = SessionLocal()
        try:
            epic = db_local.get(Epic, epic_id)
            if not epic or str(epic.project_id) != str(project_id):
                raise bad_request("Epic not found")
            if epic.status != EpicStatus.approved:
                raise bad_request("Epic must be approved before generating stories")

            run = Run(project_id=project_id, run_type="story_generation", status=RunStatus.started)
            db_local.add(run); db_local.commit(); db_local.refresh(run)

            await anyio.to_thread.run_sync(lambda: emit_run_event(db_local, run_id=run.id, event_type="stories.started", message="Story generation started"))
            gen = generate_stories(
                product_request=db_local.get(Project, project_id).product_request,
                epic_title=epic.title,
                epic_goal=epic.goal,
                constraints=constraints,
                count=count,
            )
            batch = StoryBatch(project_id=project_id, epic_id=epic_id, run_id=run.id, constraints=constraints, status=StoryBatchStatus.generated)
            db_local.add(batch); db_local.commit(); db_local.refresh(batch)

            rows: list[Story] = []
            import json as _json
            for s in gen:
                rows.append(
                    Story(
                        project_id=project_id,
                        epic_id=epic_id,
                        batch_id=batch.id,
                        statement=s.statement,
                        acceptance_criteria_json=_json.dumps(s.acceptance_criteria, ensure_ascii=False),
                        edge_cases=s.edge_cases,
                        non_functional=s.non_functional,
                        estimate=s.estimate,
                        estimate_reason=s.estimate_reason,
                        dependencies_json=_json.dumps(s.dependencies, ensure_ascii=False),
                        status=StoryStatus.proposed,
                    )
                )
            db_local.add_all(rows); db_local.commit()

            emit_run_event(db_local, run_id=run.id, event_type="stories.generated", message=f"Generated {len(rows)} stories")
            run.status = RunStatus.completed; db_local.commit()
            return {"batch_id": str(batch.id), "constraints": constraints, "stories": _stories_summary(rows), "run_id": str(run.id)}
        finally:
            db_local.close()

    async def _handle_generate(*, epic_id: str | None, constraints: str | None, count: int | None) -> None:
        if not epic_id:
            await websocket.send_json({"type": "error", "message": "epic_id is required"})
            return
        constraints_norm = (constraints or "").strip()
        count_norm = max(1, min(int(count or 10), 25))

        # Create run inside the job to get the run_id to attach
        result = await anyio.to_thread.run_sync(
            partial(_generate_job, project_id=project_id, epic_id=str(epic_id), constraints=constraints_norm, count=count_norm)
        )
        run_id = result.get("run_id")
        if run_id:
            await _start_forwarding(run_id)
        await websocket.send_json({"type": "stories.batch.created", "batch_id": result.get("batch_id"), "run_id": run_id})
        await websocket.send_json(
            {
                "type": "stories.batch.summary",
                "batch_id": result.get("batch_id"),
                "constraints": result.get("constraints"),
                "stories": result.get("stories", []),
            }
        )

    async def _handle_approve(*, batch_id: str | None, approve_all: bool | None) -> None:
        if not batch_id:
            await websocket.send_json({"type": "error", "message": "batch_id is required"})
            return
        approve_all_norm = True if approve_all is None else bool(approve_all)

        db_local = SessionLocal()
        try:
            batch = db_local.get(StoryBatch, batch_id)
            if not batch or str(batch.project_id) != str(project_id):
                await websocket.send_json({"type": "error", "message": "Story batch not found"})
                return
            if approve_all_norm:
                db_local.query(Story).filter(Story.batch_id == batch_id).update({Story.status: StoryStatus.approved})
            batch.status = StoryBatchStatus.approved
            db_local.commit()
            if batch.run_id:
                emit_run_event(db_local, run_id=batch.run_id, event_type="stories.approved", message="Stories approved")
        finally:
            db_local.close()

        await websocket.send_json({"type": "stories.approved", "batch_id": str(batch_id)})
        await _send_batch_summary(str(batch_id))

    async def _handle_latest(*, epic_id: str | None) -> None:
        if not epic_id:
            await websocket.send_json({"type": "error", "message": "epic_id is required"})
            return
        db_local = SessionLocal()
        try:
            batch = (
                db_local.query(StoryBatch)
                .filter(StoryBatch.project_id == project_id, StoryBatch.epic_id == epic_id)
                .order_by(StoryBatch.created_at.desc())
                .first()
            )
            if not batch:
                await websocket.send_json({"type": "stories.latest", "message": "No batches yet"})
                return
            rows = db_local.query(Story).filter(Story.batch_id == batch.id).all()
            await websocket.send_json(
                {
                    "type": "stories.latest",
                    "batch_id": str(batch.id),
                    "project_id": str(batch.project_id),
                    "epic_id": str(batch.epic_id),
                    "constraints": batch.constraints,
                    "status": batch.status.value if hasattr(batch.status, "value") else str(batch.status),
                    "stories": _stories_summary(rows),
                }
            )
        finally:
            db_local.close()

    try:
        while True:
            try:
                msg = await websocket.receive_json()
            except WebSocketDisconnect:
                break
            except Exception:
                await websocket.send_json({"type": "error", "message": "Invalid JSON message"})
                continue

            t = str(msg.get("type") or "").strip()
            if t in ("stories.generate", "stories.regenerate"):
                await _handle_generate(epic_id=msg.get("epic_id"), constraints=msg.get("constraints"), count=msg.get("count"))
            elif t == "stories.approve":
                await _handle_approve(batch_id=msg.get("batch_id"), approve_all=msg.get("approve_all"))
            elif t == "stories.latest":
                await _handle_latest(epic_id=msg.get("epic_id"))
            elif t == "runs.attach":
                run_id = str(msg.get("run_id") or "").strip()
                if not run_id:
                    await websocket.send_json({"type": "error", "message": "run_id is required"})
                    continue
                await _start_forwarding(run_id)
            elif t == "ping":
                await websocket.send_json({"type": "pong"})
            else:
                await websocket.send_json({"type": "error", "message": f"Unknown message type: {t}"})
    finally:
        await _stop_forwarding()
        try:
            await websocket.close()
        except Exception:
            pass


@router.websocket("/ws/projects/{project_id}/specs")
async def ws_specs_control(websocket: WebSocket, project_id: str) -> None:
    """
    Commands:
      - {"type":"specs.generate","story_id":".","constraints":"."}
      - {"type":"specs.regenerate","story_id":".","constraints":".","feedback":"."}
      - {"type":"specs.get","story_id":"."}
      - {"type":"specs.approve","spec_id":"."}
      - {"type":"specs.reject","spec_id":".","feedback":"."}
      - {"type":"runs.attach","run_id":"."}
      - {"type":"ping"}
    """
    # Auth via JWT in query param (token)
    token = websocket.query_params.get("token")
    user_id = _decode_ws_jwt_or_none(token)
    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Ownership check
    db_gen = get_db()
    db: Session = next(db_gen)
    try:
        project = db.get(Project, project_id)
        if not project or str(project.owner_id) != str(user_id):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass
        db.close()

    await websocket.accept()
    await websocket.send_json({"type": "ws.connected", "scope": "specs", "project_id": project_id})

    # Run-events forwarding (same pattern as epics/stories)
    current_queue: asyncio.Queue | None = None
    current_run_id: str | None = None
    forwarder_task: asyncio.Task | None = None

    async def _stop_forwarding() -> None:
        nonlocal current_queue, current_run_id, forwarder_task
        if forwarder_task:
            forwarder_task.cancel()
            try:
                await forwarder_task
            except asyncio.CancelledError:
                pass
            except Exception:
                pass
            forwarder_task = None
        if current_queue and current_run_id:
            await broker.unsubscribe(current_run_id, current_queue)
        current_queue = None
        current_run_id = None

    async def _start_forwarding(run_id: str) -> None:
        nonlocal current_queue, current_run_id, forwarder_task
        await _stop_forwarding()
        current_run_id = str(run_id)
        current_queue = await broker.subscribe(current_run_id)

        async def _forward_loop() -> None:
            assert current_queue is not None
            try:
                while True:
                    evt = await current_queue.get()
                    await websocket.send_json(evt)
            except asyncio.CancelledError:
                return

        forwarder_task = asyncio.create_task(_forward_loop())
        await websocket.send_json({"type": "runs.attached", "run_id": current_run_id})



    async def _generate_or_regenerate(*, story_id: str, constraints: str, feedback: str) -> None:
        if not story_id:
            await websocket.send_json({"type": "error", "message": "story_id is required"})
            return

        db_local = SessionLocal()
        try:
            story = db_local.get(Story, story_id)
            if not story or str(story.project_id) != str(project_id):
                await websocket.send_json({"type": "error", "message": "story not found"})
                return

            # FIX: started (not running) per enum in models.py
            run = Run(project_id=project_id, run_type="spec_generation", status=RunStatus.started)
            db_local.add(run)
            db_local.commit()
            db_local.refresh(run)
            await websocket.send_json({"type": "runs.created", "run_id": str(run.id)})

            await anyio.to_thread.run_sync(
                lambda: emit_run_event(
                    db_local,
                    run_id=run.id,
                    event_type="specs.started",
                    message="Spec generation started",
                )
            )

            spec_payload = generate_spec_for_story(
                product_request=db_local.get(Project, project_id).product_request,
                story_statement=story.statement,
                acceptance_criteria=json.loads(story.acceptance_criteria_json or "[]"),
                constraints=(constraints or "").strip(),
                feedback=(feedback or "").strip(),
            )

            # Next version
            latest_ver = (
                db_local.query(SpecDocument)
                .filter(SpecDocument.story_id == story_id)
                .order_by(SpecDocument.version.desc())
                .with_entities(SpecDocument.version)
                .first()
            )
            next_ver = 1 if not latest_ver else int(latest_ver[0]) + 1

            doc = SpecDocument(
                project_id=project_id,
                story_id=story_id,
                version=next_ver,
                constraints=(constraints or "").strip(),
                feedback=(feedback or "").strip(),
                status=SpecStatus.proposed,
                overview=spec_payload.get("overview", ""),
                goals=spec_payload.get("goals", ""),
                functional_requirements_json=json.dumps(spec_payload.get("functional_requirements", []), ensure_ascii=False),
                api_contracts_json=json.dumps(spec_payload.get("api_contracts", []), ensure_ascii=False),
                data_model_changes_json=json.dumps(spec_payload.get("data_model_changes", []), ensure_ascii=False),
                security_considerations=spec_payload.get("security_considerations", ""),
                error_handling=spec_payload.get("error_handling", ""),
                observability=spec_payload.get("observability", ""),
                test_plan_json=json.dumps(spec_payload.get("test_plan", []), ensure_ascii=False),
                implementation_plan_json=json.dumps(spec_payload.get("implementation_plan", []), ensure_ascii=False),
                mermaid_sequence=spec_payload.get("mermaid_sequence", ""),
                mermaid_er=spec_payload.get("mermaid_er", ""),
            )
            db_local.add(doc)
            db_local.commit()
            db_local.refresh(doc)

            emit_run_event(
                db_local,
                run_id=run.id,
                event_type="specs.generated",
                message=f"Spec v{doc.version} generated",
                payload={"spec_id": str(doc.id)},
            )
            run.status = RunStatus.completed
            db_local.commit()

            await websocket.send_json(
                {
                    "type": "specs.summary",
                    "spec_id": str(doc.id),
                    "story_id": story_id,
                    "version": doc.version,
                    "status": doc.status.value,
                    "constraints": doc.constraints,
                    "feedback": doc.feedback,
                    "mermaid_sequence": doc.mermaid_sequence,
                    "mermaid_er": doc.mermaid_er,
                }
            )
        finally:
            db_local.close()

    try:
        while True:
            try:
                msg = await websocket.receive_json()
            except WebSocketDisconnect:
                break
            except Exception:
                # Hardened against empty or non-JSON frames (same pattern used in other WS routes)
                await websocket.send_json({"type": "error", "message": "Invalid JSON message"})
                continue

            t = str(msg.get("type") or "").strip()

            if t in ("specs.generate", "specs.regenerate"):
                await _generate_or_regenerate(
                    story_id=str(msg.get("story_id") or ""),
                    constraints=str(msg.get("constraints") or ""),
                    feedback=str(msg.get("feedback") or ""),
                )
                continue

            if t == "specs.get":
                story_id = str(msg.get("story_id") or "")
                if not story_id:
                    await websocket.send_json({"type": "error", "message": "story_id is required"})
                    continue
                db_local = SessionLocal()
                try:
                    doc = (
                        db_local.query(SpecDocument)
                        .filter(SpecDocument.story_id == story_id)
                        .order_by(SpecDocument.version.desc())
                        .first()
                    )
                    if not doc:
                        await websocket.send_json({"type": "specs.none", "story_id": story_id})
                        continue
                    await websocket.send_json(
                        {
                            "type": "specs.summary",
                            "spec_id": str(doc.id),
                            "story_id": story_id,
                            "version": doc.version,
                            "status": doc.status.value,
                            "constraints": doc.constraints,
                            "feedback": doc.feedback,
                            "mermaid_sequence": doc.mermaid_sequence,
                            "mermaid_er": doc.mermaid_er,
                        }
                    )
                finally:
                    db_local.close()
                continue

            if t == "specs.approve":
                spec_id = str(msg.get("spec_id") or "")
                if not spec_id:
                    await websocket.send_json({"type": "error", "message": "spec_id is required"})
                    continue
                db_local = SessionLocal()
                try:
                    doc = db_local.get(SpecDocument, spec_id)
                    if not doc or str(doc.project_id) != str(project_id):
                        await websocket.send_json({"type": "error", "message": "spec not found"})
                        continue
                    doc.status = SpecStatus.approved
                    db_local.commit()
                    await websocket.send_json({"type": "specs.approved", "spec_id": spec_id, "version": doc.version})
                finally:
                    db_local.close()
                continue

            if t == "specs.reject":
                spec_id = str(msg.get("spec_id") or "")
                feedback = str(msg.get("feedback") or "")
                if not spec_id:
                    await websocket.send_json({"type": "error", "message": "spec_id is required"})
                    continue
                db_local = SessionLocal()
                try:
                    doc = db_local.get(SpecDocument, spec_id)
                    if not doc or str(doc.project_id) != str(project_id):
                        await websocket.send_json({"type": "error", "message": "spec not found"})
                        continue
                    doc.status = SpecStatus.rejected
                    doc.feedback = feedback
                    db_local.commit()
                    await websocket.send_json(
                        {"type": "specs.rejected", "spec_id": spec_id, "version": doc.version, "feedback": feedback}
                    )
                finally:
                    db_local.close()
                continue

            if t == "runs.attach":
                run_id = str(msg.get("run_id") or "").strip()
                if not run_id:
                    await websocket.send_json({"type": "error", "message": "run_id is required"})
                    continue
                await _start_forwarding(run_id)
                continue

            if t == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            await websocket.send_json({"type": "error", "message": f"Unknown command: {t}"})

    finally:
        try:
            await _stop_forwarding()
        except asyncio.CancelledError:
            pass
        try:
            await websocket.close()
        except Exception:
            pass
