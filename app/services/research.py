from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx


TAVILY_SEARCH_URL = "https://api.tavily.com/search"


@dataclass(frozen=True)
class TavilyResult:
    title: str
    url: str
    content: str
    score: float | None = None


@dataclass(frozen=True)
class ResearchResult:
    query: str
    answer: str | None
    results: list[TavilyResult]


def tavily_search(
    *,
    api_key: str,
    query: str,
    max_results: int = 8,
    search_depth: str = "basic",
    include_answer: str | bool = "basic",
    timeout_seconds: float = 30.0,
) -> ResearchResult:
    headers = {"Authorization": f"Bearer {api_key}"}
    payload: dict[str, Any] = {
        "query": query,
        "max_results": max_results,
        "search_depth": search_depth,
        "include_answer": include_answer,
        "include_raw_content": False,
        "include_images": False,
    }

    with httpx.Client(timeout=timeout_seconds) as client:
        r = client.post(TAVILY_SEARCH_URL, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()

    results: list[TavilyResult] = []
    for item in data.get("results", []) or []:
        results.append(
            TavilyResult(
                title=str(item.get("title", "")),
                url=str(item.get("url", "")),
                content=str(item.get("content", "")),
                score=float(item["score"]) if "score" in item and item["score"] is not None else None,
            )
        )

    return ResearchResult(query=str(data.get("query", query)), answer=data.get("answer"), results=results)


def build_research_appendix_markdown(*, product_request: str, searches: list[ResearchResult]) -> tuple[str, list[str], str, str]:
    # Combine URLs and pick a compact summary/impact.
    urls: list[str] = []
    for s in searches:
        for res in s.results:
            if res.url and res.url not in urls:
                urls.append(res.url)

    # Prefer Tavily's LLM answer (already grounded in search results).
    answers = [s.answer.strip() for s in searches if s.answer and s.answer.strip()]
    summary = "\n\n".join(answers[:2]) if answers else "No summary was returned by the search provider."

    impact = (
        "This research is persisted as a first-class artifact and is intended to inform downstream epic/story/spec decisions. "
        "Examples: confirming best-practice security guidance, identifying common feature expectations, and surfacing risks/constraints. "
        "When generating epics/stories, we will cite these URLs and justify choices (the 'why X was chosen' requirement)."
    )

    md = "\n".join(
        [
            "# Research Appendix",
            "",
            "## Product Request",
            product_request.strip() or "(empty)",
            "",
            "## URLs Consulted (Citations)",
            *(f"- {u}" for u in urls[:50]),
            "",
            "## Key Findings Summary",
            summary,
            "",
            "## How Research Impacts Decisions",
            impact,
            "",
            "## Raw Search Notes",
            "```json",
            json.dumps(
                {
                    "searches": [
                        {
                            "query": s.query,
                            "answer": s.answer,
                            "results": [
                                {"title": r.title, "url": r.url, "score": r.score, "content": r.content}
                                for r in s.results
                            ],
                        }
                        for s in searches
                    ]
                },
                ensure_ascii=False,
                indent=2,
            ),
            "```",
        ]
    )

    return md, urls, summary, impact
