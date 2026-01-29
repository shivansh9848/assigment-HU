
from __future__ import annotations

import asyncio
import json
from typing import Any

import anyio
from sqlalchemy.orm import Session

from app.core.events import broker  # your EventBroker
from app.db.models import RunEvent


def emit_run_event(
    db: Session,
    *,
    run_id: str,
    event_type: str,
    message: str,
    payload: dict[str, Any] | None = None,
) -> RunEvent:
    # Persist first (RunEvent.payload_json is Text)
    row = RunEvent(
        run_id=str(run_id),
        event_type=event_type,
        message=message,
        payload_json=None if payload is None else json.dumps(payload, ensure_ascii=False),
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    event = {
        "id": row.id,
        "run_id": row.run_id,
        "event_type": row.event_type,
        "message": row.message,
        "payload": payload or {},
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }

    # Publish in both sync-thread and async-loop contexts.
    try:
        # Works when called from FastAPI sync endpoints (threadpool / AnyIO worker)
        anyio.from_thread.run(broker.publish, str(run_id), event)
        return row
    except Exception:
        pass

    try:
        # Works when called from async (e.g., WebSocket handlers)
        loop = asyncio.get_running_loop()
        loop.create_task(broker.publish(str(run_id), event))
    except Exception:
        pass

    return row
