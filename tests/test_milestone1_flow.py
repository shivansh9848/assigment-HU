from __future__ import annotations


def test_milestone1_demo_flow(client):
    # signup
    r = client.post("/auth/signup", json={"email": "u@example.com", "password": "password123"})
    assert r.status_code == 201, r.text

    # login
    r = client.post("/auth/login", data={"username": "u@example.com", "password": "password123"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # create project
    r = client.post("/projects", json={"product_request": "Build a simple todo app"}, headers=headers)
    assert r.status_code == 201, r.text
    project_id = r.json()["id"]

    # start run
    r = client.post(f"/projects/{project_id}/runs/backlog", headers=headers)
    assert r.status_code == 202, r.text
    assert r.json()["message"] == "Backlog Generation Started"


def test_invalid_empty_product_request(client):
    r = client.post("/auth/signup", json={"email": "u2@example.com", "password": "password123"})
    assert r.status_code == 201

    r = client.post("/auth/login", data={"username": "u2@example.com", "password": "password123"})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post("/projects", json={"product_request": "   "}, headers=headers)
    assert r.status_code == 400
    assert "cannot be empty" in r.json()["detail"].lower()
