from __future__ import annotations

import time

from fastapi.testclient import TestClient


def _signup_and_login(client: TestClient, email: str = "m2@example.com") -> dict[str, str]:
    res = client.post("/auth/signup", json={"email": email, "password": "password123"})
    assert res.status_code == 201, res.text
    res = client.post("/auth/login", data={"username": email, "password": "password123"})
    assert res.status_code == 200, res.text
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_milestone2_research_artifact_and_events(client: TestClient) -> None:
    headers = _signup_and_login(client)

    # Create project
    res = client.post("/projects", json={"product_request": "Build backlog generation with research"}, headers=headers)
    assert res.status_code == 201, res.text
    project_id = res.json()["id"]

    # Start backlog generation (Milestone 2: research runs in background)
    res = client.post(f"/projects/{project_id}/runs/backlog", headers=headers)
    assert res.status_code == 202, res.text
    run_id = res.json()["id"]

    # Events should include research lifecycle (background task; poll briefly)
    event_types: list[str] = []
    for _ in range(50):
        res = client.get(f"/runs/{run_id}/events", headers=headers)
        assert res.status_code == 200, res.text
        event_types = [e["event_type"] for e in res.json()]
        if "research.completed" in event_types:
            break
        time.sleep(0.01)

    assert "run.started" in event_types
    assert "research.started" in event_types
    assert "research.completed" in event_types

    # Research appendix should be persisted and retrievable
    res = client.get(f"/runs/{run_id}/research", headers=headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["run_id"] == run_id
    assert isinstance(body.get("urls"), list)
    assert len(body["urls"]) >= 1
    assert "research appendix" in (body.get("markdown") or "").lower()
