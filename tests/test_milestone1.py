from __future__ import annotations

from fastapi.testclient import TestClient


def _signup(client: TestClient, email: str, password: str) -> None:
    res = client.post("/auth/signup", json={"email": email, "password": password})
    assert res.status_code == 201, res.text


def _login(client: TestClient, email: str, password: str) -> str:
    res = client.post("/auth/login", data={"username": email, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def test_milestone1_user_can_start_flow(client: TestClient) -> None:
    _signup(client, "m1@example.com", "password123")
    token = _login(client, "m1@example.com", "password123")
    headers = {"Authorization": f"Bearer {token}"}

    # Create project (product request as text)
    res = client.post("/projects", json={"product_request": "Build a simple todo app"}, headers=headers)
    assert res.status_code == 201, res.text
    project_id = res.json()["id"]

    # List projects should include it
    res = client.get("/projects", headers=headers)
    assert res.status_code == 200, res.text
    assert any(p["id"] == project_id for p in res.json())


def test_milestone1_invalid_empty_product_request(client: TestClient) -> None:
    _signup(client, "m1b@example.com", "password123")
    token = _login(client, "m1b@example.com", "password123")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post("/projects", json={"product_request": "   "}, headers=headers)
    assert res.status_code == 400
    assert "cannot be empty" in res.json()["detail"].lower()
