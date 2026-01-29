from __future__ import annotations

import time

from fastapi.testclient import TestClient


def _auth_headers(client: TestClient, email: str) -> dict[str, str]:
    res = client.post("/auth/signup", json={"email": email, "password": "password123"})
    assert res.status_code == 201, res.text
    res = client.post("/auth/login", data={"username": email, "password": "password123"})
    assert res.status_code == 200, res.text
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_project_and_research(client: TestClient, headers: dict[str, str]) -> str:
    res = client.post("/projects", json={"product_request": "Build an internal planning tool"}, headers=headers)
    assert res.status_code == 201, res.text
    project_id = res.json()["id"]

    res = client.post(f"/projects/{project_id}/runs/backlog", headers=headers)
    assert res.status_code == 202, res.text
    run_id = res.json()["id"]

    # Poll until research appendix exists (background task)
    for _ in range(50):
        rr = client.get(f"/runs/{run_id}/research", headers=headers)
        if rr.status_code == 200:
            break
        time.sleep(0.01)
    else:
        assert False, "Research appendix not created in time"
    return project_id


def test_milestone3_generate_epics_and_mermaid_and_approve(client: TestClient) -> None:
    headers = _auth_headers(client, "m3@example.com")
    project_id = _create_project_and_research(client, headers)

    # Generate epics (requires research)
    res = client.post(
        f"/projects/{project_id}/epics/generate",
        json={"constraints": "must support SSO", "count": 6},
        headers=headers,
    )
    assert res.status_code == 201, res.text
    body = res.json()

    assert body["project_id"] == project_id
    assert isinstance(body.get("epics"), list)
    assert len(body["epics"]) >= 1
    assert "flowchart" in (body.get("mermaid") or "").lower()

    # Approve the batch (approval gate)
    batch_id = body["batch_id"]
    res = client.post(
        f"/projects/{project_id}/epics/{batch_id}/approve",
        json={"approve_all": True},
        headers=headers,
    )
    assert res.status_code == 200, res.text
    assert res.json()["message"].lower() == "approved"

    # Fetch latest batch and ensure epics are approved
    res = client.get(f"/projects/{project_id}/epics", headers=headers)
    assert res.status_code == 200, res.text
    statuses = {e["status"] for e in res.json()["epics"]}
    assert statuses == {"approved"}
