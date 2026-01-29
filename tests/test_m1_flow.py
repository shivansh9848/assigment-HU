
from __future__ import annotations

from fastapi.testclient import TestClient

def _signup(client: TestClient, email: str, password: str) -> None:
    res = client.post("/auth/signup", json={"email": email, "password": password})
    assert res.status_code == 201, res.text

def _login(client: TestClient, email: str, password: str) -> str:
    res = client.post("/auth/login", data={"username": email, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]

def test_m1_happy_path(client: TestClient) -> None:
    # Seed admin exists via startup; create normal user
    _signup(client, "u1@example.com", "userpass")
    token = _login(client, "u1@example.com", "userpass")
    headers = {"Authorization": f"Bearer {token}"}

    # Create project with product request
    res = client.post("/projects", json={"product_request": "Build backlog system"}, headers=headers)
    assert res.status_code == 201, res.text
    project_id = res.json()["id"]

    # Start backlog generation
    res = client.post(f"/projects/{project_id}/runs/backlog", headers=headers)
    assert res.status_code == 202
    assert "Backlog Generation Started" in res.json().get("message", "")