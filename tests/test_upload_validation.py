from __future__ import annotations

from io import BytesIO


def test_reject_non_pdf_extension(client):
    client.post("/auth/signup", json={"email": "u3@example.com", "password": "password123"})
    r = client.post("/auth/login", data={"username": "u3@example.com", "password": "password123"})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post("/projects", json={"product_request": "X"}, headers=headers)
    project_id = r.json()["id"]

    files = {"file": ("note.txt", b"hello", "text/plain")}
    r = client.post(f"/projects/{project_id}/documents", files=files, headers=headers)
    assert r.status_code == 400


def test_reject_corrupted_pdf(client):
    client.post("/auth/signup", json={"email": "u4@example.com", "password": "password123"})
    r = client.post("/auth/login", data={"username": "u4@example.com", "password": "password123"})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post("/projects", json={"product_request": "X"}, headers=headers)
    project_id = r.json()["id"]

    # Not a real PDF
    files = {"file": ("bad.pdf", b"%PDF-1.4\nnotreally", "application/pdf")}
    r = client.post(f"/projects/{project_id}/documents", files=files, headers=headers)
    assert r.status_code == 400
