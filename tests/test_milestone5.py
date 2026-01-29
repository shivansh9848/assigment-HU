from __future__ import annotations

import time

from fastapi.testclient import TestClient


def _auth_headers_and_token(client: TestClient, email: str) -> tuple[dict[str, str], str]:
    res = client.post("/auth/signup", json={"email": email, "password": "password123"})
    assert res.status_code == 201, res.text
    res = client.post("/auth/login", data={"username": email, "password": "password123"})
    assert res.status_code == 200, res.text
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, token


def _setup_story(client: TestClient, headers: dict[str, str]) -> tuple[str, str]:
    # Project + research
    res = client.post("/projects", json={"product_request": "Build a planning tool"}, headers=headers)
    assert res.status_code == 201, res.text
    project_id = res.json()["id"]

    res = client.post(f"/projects/{project_id}/runs/backlog", headers=headers)
    assert res.status_code == 202, res.text
    run_id = res.json()["id"]

    for _ in range(50):
        rr = client.get(f"/runs/{run_id}/research", headers=headers)
        if rr.status_code == 200:
            break
        time.sleep(0.01)
    else:
        assert False, "Research appendix not created in time"

    # Epics generate + approve
    res = client.post(f"/projects/{project_id}/epics/generate", json={"constraints": "", "count": 2}, headers=headers)
    assert res.status_code == 201, res.text
    batch_id = res.json()["batch_id"]
    epic_id = res.json()["epics"][0]["id"]

    res = client.post(f"/projects/{project_id}/epics/{batch_id}/approve", json={"approve_all": True}, headers=headers)
    assert res.status_code == 200, res.text

    # Stories generate + approve
    res = client.post(
        f"/projects/{project_id}/stories/generate",
        json={"epic_id": epic_id, "constraints": "", "count": 2},
        headers=headers,
    )
    assert res.status_code == 201, res.text
    story_batch_id = res.json()["batch_id"]
    story_id = res.json()["stories"][0]["id"]

    res = client.post(f"/projects/{project_id}/stories/{story_batch_id}/approve", json={"approve_all": True}, headers=headers)
    assert res.status_code == 200, res.text

    return project_id, story_id


def test_milestone5_spec_generation_requires_explicit_approval_over_ws(client: TestClient) -> None:
    headers, token = _auth_headers_and_token(client, "m5@example.com")
    project_id, story_id = _setup_story(client, headers)

    with client.websocket_connect(f"/ws/projects/{project_id}/specs?token={token}") as ws:
        first = ws.receive_json()
        assert first["type"] == "ws.connected"
        assert first["scope"] == "specs"

        ws.send_json({"type": "specs.generate", "story_id": story_id, "constraints": "need rate limiting"})

        # Server emits multiple messages; wait until we get spec summary.
        summary = None
        for _ in range(20):
            msg = ws.receive_json()
            if msg.get("type") == "specs.summary":
                summary = msg
                break
        assert summary is not None
        assert summary["story_id"] == story_id
        assert "sequenceDiagram" in (summary.get("mermaid_sequence") or "")
        assert "erDiagram" in (summary.get("mermaid_er") or "")

        spec_id = summary["spec_id"]
        ws.send_json({"type": "specs.approve", "spec_id": spec_id})
        approved = ws.receive_json()
        assert approved["type"] == "specs.approved"
        assert approved["spec_id"] == spec_id
