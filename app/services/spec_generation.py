
from __future__ import annotations

from typing import Any, Dict, List
import json
from app.core.config import get_settings


def _heuristic_spec(*, story_statement: str, acceptance_criteria: List[str], constraints: str, feedback: str) -> Dict[str, Any]:
    fr = [{"requirement": ac, "mapped_to": "AC"} for ac in acceptance_criteria[:8]]
    seq = f"""sequenceDiagram
    participant U as User
    participant API as FastAPI Backend
    participant DB as PostgreSQL
    U->>API: {story_statement}
    API->>DB: Validate and persist
    DB-->>API: OK / Error
    API-->>U: Response
    """
    er = """erDiagram
    USER ||--o{ SESSION : has
    PROJECT ||--o{ STORY : contains
    STORY ||--o{ SPEC_DOCUMENT : versions
    """
    return {
        "overview": f"This spec operationalizes the story: {story_statement}",
        "goals": "Deliver functionality aligned to acceptance criteria and constraints.",
        "functional_requirements": fr,
        "api_contracts": [],
        "data_model_changes": [],
        "security_considerations": "Apply authN/Z via JWT and role checks; input validation; rate limiting if applicable.",
        "error_handling": "Consistent error model with HTTP codes; structured problem details.",
        "observability": "Emit logs for key steps; counters for success/failure; traces around DB calls.",
        "test_plan": [{"ac": ac, "tests": [f"Test: {ac}"]} for ac in acceptance_criteria[:8]],
        "implementation_plan": [
            {"file": "app/api/routers/<feature>.py", "action": "create/modify"},
            {"file": "app/services/<feature>.py", "action": "create/modify"},
            {"file": "app/db/models.py", "action": "update if DB schema changes"},
        ],
        "mermaid_sequence": seq,
        "mermaid_er": er,
    }


def generate_spec_for_story(
    *,
    product_request: str,
    story_statement: str,
    acceptance_criteria: List[str],
    constraints: str,
    feedback: str,
) -> Dict[str, Any]:
    """
    If OPENAI key is configured, use it; otherwise produce a deterministic spec.
    Produces keys: overview, goals, functional_requirements[], api_contracts[], data_model_changes[],
    security_considerations, error_handling, observability, test_plan[], implementation_plan[],
    mermaid_sequence, mermaid_er.
    """
    settings = get_settings()
    if settings.openai_api_key:
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)
        system = (
            "You are a software architect. Produce a formal implementation spec as strict JSON. "
            "Keys: overview, goals, functional_requirements[], api_contracts[], data_model_changes[], "
            "security_considerations, error_handling, observability, test_plan[], implementation_plan[], "
            "mermaid_sequence, mermaid_er. Keep diagrams as Mermaid strings. "
            "REQUIREMENTS: mermaid_sequence MUST include 'sequenceDiagram' and be non-empty. "
            "mermaid_er MUST include 'erDiagram' and be non-empty. "
        )
        user_payload = {
            "product_request": product_request,
            "story": {"statement": story_statement, "acceptance_criteria": acceptance_criteria},
            "constraints": constraints,
            "feedback": feedback,
        }
        resp = client.chat.completions.create(
            model=settings.openai_model,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": system}, {"role": "user", "content": json.dumps(user_payload)}],
        )
        content = resp.choices[0].message.content or "{}"
        try:
            return json.loads(content)
        except Exception:
            pass
    # Fallback (deterministic)
    return _heuristic_spec(
        story_statement=story_statement,
        acceptance_criteria=acceptance_criteria,
        constraints=constraints,
        feedback=feedback,
    )


def _ensure_two_mermaid_diagrams(
    spec: Dict[str, Any],
    *,
    story_statement: str,
    acceptance_criteria: List[str],
    constraints: str,
    feedback: str,
) -> Dict[str, Any]:
    """
    Guarantees spec has BOTH:
      - mermaid_sequence containing 'sequenceDiagram'
      - mermaid_er containing 'erDiagram'
    If missing/invalid, fills from heuristic diagrams.
    """
    h = _heuristic_spec(
        story_statement=story_statement,
        acceptance_criteria=acceptance_criteria,
        constraints=constraints,
        feedback=feedback,
    )

    seq = spec.get("mermaid_sequence")
    er = spec.get("mermaid_er")

    if not isinstance(seq, str) or "sequenceDiagram" not in seq:
        spec["mermaid_sequence"] = h["mermaid_sequence"]

    if not isinstance(er, str) or "erDiagram" not in er:
        spec["mermaid_er"] = h["mermaid_er"]

    return spec

