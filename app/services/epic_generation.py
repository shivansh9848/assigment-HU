from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, List
import httpx
from openai import OpenAI
from app.core.config import get_settings


@dataclass(frozen=True)
class GeneratedEpic:
    title: str
    goal: str
    in_scope: str
    out_of_scope: str
    priority: str
    priority_reason: str
    dependencies: list[str]
    risks: str
    assumptions: str
    open_questions: str
    success_metrics: str


def _heuristic_epics(*, product_request: str, constraints: str, count: int) -> list[GeneratedEpic]:
    # Deterministic fallback so Milestone 3 works without an LLM key.
    base = [
        ("Authentication & Roles", "Users can sign up/login and roles are enforced."),
        ("Core Domain CRUD", "Create/read/update/delete the main domain objects."),
        ("Search & Filtering", "Users can search/filter/sort core objects."),
        ("Notifications", "Notify users for important events (basic)."),
        ("Admin & Settings", "Admins manage users/config; basic settings."),
        ("Observability & Audit", "Logs, basic audit trail, error handling."),
    ]

    if constraints and "sso" in constraints.lower():
        base[0] = ("Authentication (SSO + Local)", "Support SSO plus local auth; enforce roles.")

    selected = base[: max(1, min(count, len(base)))]

    epics: list[GeneratedEpic] = []
    for idx, (title, goal) in enumerate(selected, start=1):
        deps = []
        if idx > 1:
            deps.append(selected[idx - 2][0])
        epics.append(
            GeneratedEpic(
                title=title,
                goal=goal,
                in_scope=f"MVP scope for: {title}",
                out_of_scope=f"Later improvements for: {title}",
                priority="P0" if idx <= 2 else "P1" if idx <= 4 else "P2",
                priority_reason="Earlier epics unblock later delivery.",
                dependencies=deps,
                risks="TBD - validate assumptions during implementation.",
                assumptions=f"Assumes: {product_request[:160].strip()}" if product_request else "Assumes product request is valid.",
                open_questions="What integrations and constraints exist?",
                success_metrics="Feature works end-to-end for primary flows.",
            )
        )
    return epics

def _openai_generate_epics(
    *,
    product_request: str,
    research_summary: str,
    citations: list[str],
    constraints: str,
    count: int,
) -> list[GeneratedEpic]:
    settings = get_settings()
    if not settings.openai_api_key:
        return _heuristic_epics(product_request=product_request, constraints=constraints, count=count)

    client = OpenAI(api_key=settings.openai_api_key)

    system = (
        "You are a product planning assistant. "
        "Generate a prioritized epic backlog grounded in the provided research. "
        "Return STRICT JSON ONLY using the schema: "
        "{ \"epics\": [ {"
        "\"title\": str, \"goal\": str, \"in_scope\": str, \"out_of_scope\": str, "
        "\"priority\": str, \"priority_reason\": str, "
        "\"dependencies\": [str], \"risks\": str, \"assumptions\": str, "
        "\"open_questions\": str, \"success_metrics\": str } ] }"
    )

    user_payload = {
        "product_request": product_request,
        "research_summary": research_summary,
        "citations": citations,
        "constraints": constraints,
        "count": count,
        "notes": "Prioritize epics that unblock others. Use P0/P1/P2. Keep dependencies as titles of prerequisite epics.",
    }

    # Use Chat Completions for broad compatibility. If you prefer, move to Responses API.
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
        # Defensive: fall back to heuristic to avoid breaking the flow
        return _heuristic_epics(product_request=product_request, constraints=constraints, count=count)

    items: List[dict[str, Any]] = list(data.get("epics") or [])
    if not items:
        return _heuristic_epics(product_request=product_request, constraints=constraints, count=count)

    out: list[GeneratedEpic] = []
    for e in items[: max(1, count)]:
        out.append(
            GeneratedEpic(
                title=str(e.get("title", "")).strip(),
                goal=str(e.get("goal", "")).strip(),
                in_scope=str(e.get("in_scope", "")).strip(),
                out_of_scope=str(e.get("out_of_scope", "")).strip(),
                priority=str(e.get("priority", "P1")).strip(),
                priority_reason=str(e.get("priority_reason", "")).strip(),
                dependencies=[str(x).strip() for x in (e.get("dependencies") or [])],
                risks=str(e.get("risks", "")).strip(),
                assumptions=str(e.get("assumptions", "")).strip(),
                open_questions=str(e.get("open_questions", "")).strip(),
                success_metrics=str(e.get("success_metrics", "")).strip(),
            )
        )
    return out


def generate_epics(
    *,
    product_request: str,
    research_summary: str,
    citations: list[str],
    constraints: str,
    count: int,
) -> list[GeneratedEpic]:
    settings = get_settings()
    if settings.openai_api_key:
        return _openai_generate_epics(
            product_request=product_request,
            research_summary=research_summary,
            citations=citations,
            constraints=constraints,
            count=count,
        )
    return _heuristic_epics(product_request=product_request, constraints=constraints, count=count)


def _openai_generate_epics(*, product_request: str, research_summary: str, citations: list[str], constraints: str, count: int) -> list[GeneratedEpic]:
    settings = get_settings()
    if not settings.openai_api_key:
        return _heuristic_epics(product_request=product_request, constraints=constraints, count=count)

    system = (
        "You are a product planning assistant. Generate a prioritized epic backlog grounded in provided research. "
        "Return STRICT JSON only, no markdown."
    )

    user = {
        "product_request": product_request,
        "constraints": constraints,
        "research": {
            "summary": research_summary,
            "citations": citations,
        },
        "output_requirements": {
            "epic_count": count,
            "fields": [
                "title",
                "goal",
                "in_scope",
                "out_of_scope",
                "priority",
                "priority_reason",
                "dependencies",
                "risks",
                "assumptions",
                "open_questions",
                "success_metrics",
            ],
            "priority_values": ["P0", "P1", "P2"],
            "dependencies": "List epic titles this epic depends on (strings).",
        },
    }

    payload: dict[str, Any] = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
        ],
        "temperature": 0.2,
    }

    headers = {"Authorization": f"Bearer {settings.openai_api_key}", "Content-Type": "application/json"}
    with httpx.Client(timeout=60.0) as client:
        r = client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()

    content = data["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    epics_raw = parsed["epics"] if isinstance(parsed, dict) and "epics" in parsed else parsed

    epics: list[GeneratedEpic] = []
    for e in epics_raw[:count]:
        epics.append(
            GeneratedEpic(
                title=str(e.get("title", "")),
                goal=str(e.get("goal", "")),
                in_scope=str(e.get("in_scope", "")),
                out_of_scope=str(e.get("out_of_scope", "")),
                priority=str(e.get("priority", "P1")),
                priority_reason=str(e.get("priority_reason", "")),
                dependencies=list(e.get("dependencies", []) or []),
                risks=str(e.get("risks", "")),
                assumptions=str(e.get("assumptions", "")),
                open_questions=str(e.get("open_questions", "")),
                success_metrics=str(e.get("success_metrics", "")),
            )
        )

    # If model returned too few, pad deterministically.
    if len(epics) < count:
        epics.extend(_heuristic_epics(product_request=product_request, constraints=constraints, count=count - len(epics)))

    return epics


def generate_epics(*, product_request: str, research_summary: str, citations: list[str], constraints: str, count: int) -> list[GeneratedEpic]:
    # Prefer OpenAI if configured; otherwise deterministic fallback.
    return _openai_generate_epics(
        product_request=product_request,
        research_summary=research_summary,
        citations=citations,
        constraints=constraints,
        count=count,
    )



def make_mermaid_dependency_graph(epics: list[GeneratedEpic]) -> str:
    # Emit a clean, Markdown-ready Mermaid graph.
    lines: list[str] = []
    lines.append("flowchart TD")
    lines.append("")

    title_to_id: dict[str, str] = {}
    for idx, e in enumerate(epics, start=1):
        node_id = f"E{idx}"
        title_to_id[e.title] = node_id
        safe_title = e.title.replace('"', "'")
        lines.append(f'  {node_id}["{safe_title}"]')

    lines.append("")

    for e in epics:
        src_id = title_to_id.get(e.title)
        for dep_title in (e.dependencies or []):
            dep_id = title_to_id.get(dep_title)
            if dep_id and src_id:
                lines.append(f"  {dep_id} --> {src_id}")

    lines.append("")
    return "\n".join(lines)
