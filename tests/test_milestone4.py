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


def _setup_approved_epic(client: TestClient, headers: dict[str, str]) -> tuple[str, str]:
    res = client.post("/projects", json={"product_request": "Build a planning tool"}, headers=headers)
    assert res.status_code == 201, res.text
    project_id = res.json()["id"]

    # Research prerequisite
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

    # Generate epics
    res = client.post(
        f"/projects/{project_id}/epics/generate",
        json={"constraints": "", "count": 3},
        headers=headers,
    )
    assert res.status_code == 201, res.text
    batch_id = res.json()["batch_id"]
    epic_id = res.json()["epics"][0]["id"]

    # Approve epics
    res = client.post(
        f"/projects/{project_id}/epics/{batch_id}/approve",
        json={"approve_all": True},
        headers=headers,
    )
    assert res.status_code == 200, res.text

    return project_id, epic_id


def test_milestone4_generate_stories_with_acceptance_criteria_and_approve(client: TestClient) -> None:
    headers = _auth_headers(client, "m4@example.com")
    project_id, epic_id = _setup_approved_epic(client, headers)

    # Generate stories for the approved epic
    res = client.post(
        f"/projects/{project_id}/stories/generate",
        json={"epic_id": epic_id, "constraints": "must be GDPR compliant", "count": 5},
        headers=headers,
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["project_id"] == project_id
    assert body["epic_id"] == epic_id
    assert len(body["stories"]) == 5

    # Stories should include Given/When/Then acceptance criteria strings
    ac_lists = [s["acceptance_criteria"] for s in body["stories"]]
    assert all(isinstance(ac, list) and len(ac) >= 1 for ac in ac_lists)

    # Approve batch
    batch_id = body["batch_id"]
    res = client.post(
        f"/projects/{project_id}/stories/{batch_id}/approve",
        json={"approve_all": True},
        headers=headers,
    )
    assert res.status_code == 200, res.text

    # Latest stories should now be approved
    res = client.get(f"/projects/{project_id}/stories", params={"epic_id": epic_id}, headers=headers)
    assert res.status_code == 200, res.text
    statuses = {s["status"] for s in res.json()["stories"]}
    assert statuses == {"approved"}
