
from __future__ import annotations

from fastapi.testclient import TestClient

def _login(client: TestClient, email: str, password: str) -> str:
    res = client.post("/auth/login", data={"username": email, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]

def _signup(client: TestClient, email: str, password: str) -> None:
    res = client.post("/auth/signup", json={"email": email, "password": password})
    assert res.status_code == 201

def test_admin_list_and_promote_demote_delete(client: TestClient) -> None:
    # Login as seeded admin
    admin_token = _login(client, "admin@example.com", "adminpass")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Create two normal users
    _signup(client, "a@example.com", "pass")
    _signup(client, "b@example.com", "pass")

    # List users (admin only)
    res = client.get("/admin/users", headers=admin_headers)
    assert res.status_code == 200
    users = res.json()
    assert any(u["email"] == "a@example.com" for u in users)

    # Promote A to admin
    target = next(u for u in users if u["email"] == "a@example.com")
    res = client.post(f"/admin/users/{target['id']}/promote", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["is_admin"] is True

    # Non-admin cannot list users
    user_token = _login(client, "b@example.com", "pass")
    user_headers = {"Authorization": f"Bearer {user_token}"}
    res = client.get("/admin/users", headers=user_headers)
    assert res.status_code == 403

    # Try to demote last admin — should fail
    # First, delete the second admin to ensure we test the guard
    res = client.delete(f"/admin/users/{target['id']}", headers=admin_headers)
    assert res.status_code == 200
    # Now only seed admin remains; attempt to demote seed admin should fail
    res = client.post(f"/admin/users/{users[0]['id']}/demote", headers=admin_headers)
    assert res.status_code in (400, 403)

def test_admin_cannot_self_delete_or_self_demote(client: TestClient) -> None:
    admin_token = _login(client, "admin@example.com", "adminpass")
    headers = {"Authorization": f"Bearer {admin_token}"}

    res = client.get("/admin/users", headers=headers)
    me = next(u for u in res.json() if u["email"] == "admin@example.com")

    # Self demote should fail
    res = client.post(f"/admin/users/{me['id']}/demote", headers=headers)
    assert res.status_code in (400, 403)

    # Self delete should fail
    res = client.delete(f"/admin/users/{me['id']}", headers=headers)
    assert res.status_code in (400, 403)
