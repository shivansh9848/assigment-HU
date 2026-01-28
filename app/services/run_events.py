from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import RunEvent, RunEventLevel


def emit_run_event(
    db: Session,
    *,
    run_id: str,
    event_type: str,
    message: str,
    level: RunEventLevel = RunEventLevel.info,
    payload: dict[str, Any] | None = None,
) -> RunEvent:
    evt = RunEvent(
        run_id=run_id,
        level=level,
        event_type=event_type,
        message=message,
        payload_json=json.dumps(payload, ensure_ascii=False) if payload is not None else None,
    )
    db.add(evt)
    db.commit()
    db.refresh(evt)
    return evt
