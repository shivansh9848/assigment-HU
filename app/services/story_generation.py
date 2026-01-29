
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, List
import json
from app.core.config import get_settings

@dataclass
class GeneratedStory:
    statement: str
    acceptance_criteria: list[str]
    edge_cases: str
    non_functional: str
    estimate: str
    estimate_reason: str
    dependencies: list[str]

def _heuristic_stories(*, epic_title: str, constraints: str, count: int) -> list[GeneratedStory]:
    base_ac = [
        "Given a valid request, When the user performs the primary action, Then the system responds successfully",
        "Given invalid input, When the system validates, Then the user receives a clear error",
    ]
    out: list[GeneratedStory] = []
    for i in range(count):
        out.append(
            GeneratedStory(
                statement=f"As a developer, I want to implement {epic_title.lower()} part {i+1}, so that the feature works end-to-end",
                acceptance_criteria=base_ac,
                edge_cases="Network failures; malformed payloads; permission errors",
                non_functional="Log failures; enforce basic rate limits; adhere to privacy-by-default.",
                estimate="M",
                estimate_reason="Moderate scope with standard CRUD and validation",
                dependencies=[],
            )
        )
    return out

def _openai_generate_stories(*, product_request: str, epic_title: str, epic_goal: str, constraints: str, count: int) -> list[GeneratedStory]:
    settings = get_settings()
    from openai import OpenAI
    client = OpenAI(api_key=settings.openai_api_key)

    system = (
        "You are a product planning assistant. Generate implementable user stories for the given epic. "
        "Return STRICT JSON only with: stories: [ { statement, acceptance_criteria[], edge_cases, non_functional, estimate, estimate_reason, dependencies[] } ]. "
        "Acceptance criteria must be Given/When/Then bullets. Keep estimate as T-shirt size (XS/S/M/L/XL). No markdown."
    )
    user_payload = {
        "product_request": product_request,
        "epic": {"title": epic_title, "goal": epic_goal},
        "constraints": constraints,
        "count": count,
    }
    resp = client.chat.completions.create(
        model=settings.openai_model,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ],
    )
    content = resp.choices[0].message.content or "{}"
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return _heuristic_stories(epic_title=epic_title, constraints=constraints, count=count)

    items: List[dict[str, Any]] = list(data.get("stories") or [])
    if not items:
        return _heuristic_stories(epic_title=epic_title, constraints=constraints, count=count)

    out: list[GeneratedStory] = []
    for s in items[: max(1, count)]:
        out.append(
            GeneratedStory(
                statement=str(s.get("statement", "")).strip(),
                acceptance_criteria=[str(x).strip() for x in (s.get("acceptance_criteria") or [])],
                edge_cases=str(s.get("edge_cases", "")).strip(),
                non_functional=str(s.get("non_functional", "")).strip(),
                estimate=str(s.get("estimate", "M")).strip(),
                estimate_reason=str(s.get("estimate_reason", "")).strip(),
                dependencies=[str(x).strip() for x in (s.get("dependencies") or [])],
            )
        )
    return out

def generate_stories(*, product_request: str, epic_title: str, epic_goal: str, constraints: str, count: int) -> list[GeneratedStory]:
    settings = get_settings()
    if settings.openai_api_key:
        return _openai_generate_stories(
            product_request=product_request,
            epic_title=epic_title,
            epic_goal=epic_goal,
            constraints=constraints,
            count=count,
        )
    return _heuristic_stories(epic_title=epic_title, constraints=constraints, count=count)
