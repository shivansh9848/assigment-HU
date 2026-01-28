from __future__ import annotations

import json

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.errors import bad_request
from app.core.errors import forbidden, not_found
from app.db.models import Project, ResearchAppendix, Run, RunStatus, User
from app.db.session import SessionLocal, get_db
from app.schemas.runs import RunResponse
from app.services.research import build_research_appendix_markdown, tavily_search
from app.services.run_events import emit_run_event
from app.services.storage import project_root


router = APIRouter(prefix="/projects", tags=["runs"])


def _run_research_job(*, project_id: str, run_id: str, product_request: str) -> None:
    settings = get_settings()
    if not settings.tavily_api_key:
        # Mandatory in Milestone 2.
        db = SessionLocal()
        try:
            emit_run_event(
                db,
                run_id=run_id,
                event_type="research.error",
                message="TAVILY_API_KEY is not configured; research cannot run.",
            )
            run = db.get(Run, run_id)
            if run:
                run.status = RunStatus.failed
                db.commit()
        finally:
            db.close()
        return

    db = SessionLocal()
    try:
        emit_run_event(db, run_id=run_id, event_type="research.started", message="Research in progress")

        queries = [
            f"Best practices, security, and common requirements for: {product_request}",
            f"Risks, constraints, and edge cases for: {product_request}",
        ]

        searches = [
            tavily_search(
                api_key=settings.tavily_api_key,
                query=q,
                max_results=settings.research_max_results,
                search_depth=settings.research_search_depth,
                include_answer="basic",
            )
            for q in queries
        ]

        md, urls, summary, impact = build_research_appendix_markdown(product_request=product_request, searches=searches)

        # Persist markdown to filesystem
        run_dir = project_root(project_id) / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        md_path = run_dir / "research.md"
        md_path.write_text(md, encoding="utf-8")

        # Persist appendix row
        appendix = ResearchAppendix(
            project_id=project_id,
            run_id=run_id,
            markdown_path=str(md_path.relative_to(settings.storage_root).as_posix()),
            urls_json=json.dumps(urls, ensure_ascii=False),
            summary=summary,
            impact=impact,
        )
        db.add(appendix)
        db.commit()
        db.refresh(appendix)

        emit_run_event(
            db,
            run_id=run_id,
            event_type="research.completed",
            message="Research complete",
            payload={"url_count": len(urls)},
        )
        emit_run_event(db, run_id=run_id, event_type="epics.pending", message="Epic generation will start in Milestone 3")
        run = db.get(Run, run_id)
        if run:
            run.status = RunStatus.completed
            db.commit()
    except Exception as ex:
        emit_run_event(
            db,
            run_id=run_id,
            event_type="research.error",
            message=f"Research failed: {type(ex).__name__}",
        )
        run = db.get(Run, run_id)
        if run:
            run.status = RunStatus.failed
            db.commit()
    finally:
        db.close()


@router.post("/{project_id}/runs/backlog", response_model=RunResponse, status_code=status.HTTP_202_ACCEPTED)
def start_backlog_generation(
    project_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RunResponse:
    project = db.get(Project, project_id)
    if not project:
        raise not_found("Project not found")
    if project.owner_id != user.id:
        raise forbidden("You can only start runs for your own projects")

    settings = get_settings()
    if not settings.tavily_api_key:
        raise bad_request("Milestone 2 requires web research: set TAVILY_API_KEY in .env")

    run = Run(project_id=project_id, run_type="backlog_generation", status=RunStatus.started)
    db.add(run)
    db.commit()
    db.refresh(run)

    emit_run_event(db, run_id=run.id, event_type="run.started", message="Backlog Generation Started")
    background_tasks.add_task(
        _run_research_job,
        project_id=project_id,
        run_id=run.id,
        product_request=project.product_request,
    )

    return RunResponse(
        id=run.id,
        project_id=run.project_id,
        run_type=run.run_type,
        status=run.status,
        message="Backlog Generation Started",
    )
