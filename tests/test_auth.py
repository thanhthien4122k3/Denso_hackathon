"""Kiểm thử đăng nhập, phân quyền và audit."""

import pytest
from fastapi.testclient import TestClient

from app.database import get_connection
from app.main import app
from app.services.auth_service import AuthService

PASS = "test-pass-123"


def _create_user(username, roles):
    svc = AuthService()
    if svc.repository.find_by_username(username) is None:
        svc.create_user(username, username, PASS, list(roles), is_simulated=False)


def _client_for(username):
    tc = TestClient(app)
    r = tc.post("/api/auth/login", json={"username": username, "password": PASS})
    assert r.status_code == 200, r.text
    return tc


def test_login_wrong_password_401(client):
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "sai"})
    assert resp.status_code == 401
    # Thông báo không tiết lộ tài khoản có tồn tại hay không.
    assert "Sai tài khoản hoặc mật khẩu" in resp.json()["message"]


def test_login_and_me(client):
    _create_user("rec1", ["OPERATOR"])
    tc = _client_for("rec1")
    me = tc.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["data"]["username"] == "rec1"
    assert "OPERATOR" in me.json()["data"]["roles"]
    tc.close()


def test_logout_invalidates_session(client):
    _create_user("rec2", ["OPERATOR"])
    tc = _client_for("rec2")
    assert tc.get("/api/auth/me").status_code == 200
    tc.post("/api/auth/logout")
    assert tc.get("/api/auth/me").status_code == 401
    tc.close()


def test_disabled_account_blocks_existing_session(client):
    _create_user("rec3", ["OPERATOR"])
    tc = _client_for("rec3")
    assert tc.get("/api/auth/me").status_code == 200
    svc = AuthService()
    u = svc.repository.find_by_username("rec3")
    svc.set_user_active(u["id"], False)
    assert tc.get("/api/auth/me").status_code == 401
    tc.close()


def test_direct_api_requires_auth(client):
    tc = TestClient(app)  # không đăng nhập
    assert tc.get("/api/incidents").status_code == 401
    tc.close()


def test_recorder_cannot_confirm_cause_or_close(client):
    _create_user("rec4", ["OPERATOR"])
    tc = _client_for("rec4")
    inc = tc.post("/api/incidents", json={
        "code": "INC-REC4", "title": "Test", "incident_type": "OTHER",
        "request_id": "550e8400-e29b-41d4-a716-446655440004",
    })
    assert inc.status_code == 201
    iid = inc.json()["data"]["id"]
    assert tc.post(f"/api/incidents/{iid}/causes", json={
        "content": "Nguyên nhân xác nhận", "kind": "CONFIRMED"}).status_code == 403
    assert tc.post(f"/api/incidents/{iid}/close", json={
        "resolution_summary": "xong"}).status_code == 403
    tc.close()


def test_coordinator_can_close(client):
    _create_user("coord1", ["COORDINATOR"])
    tc = _client_for("coord1")
    inc = tc.post("/api/incidents", json={
        "code": "INC-COORD1", "title": "Test", "incident_type": "OTHER",
        "request_id": "550e8400-e29b-41d4-a716-446655440005",
    })
    iid = inc.json()["data"]["id"]
    r = tc.post(f"/api/incidents/{iid}/close", json={"resolution_summary": "Đã xử lý"})
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "RESOLVED"
    tc.close()


def test_audit_uses_session_user(client):
    _create_user("rec5", ["OPERATOR"])
    tc = _client_for("rec5")
    tc.post("/api/incidents", json={
        "code": "INC-REC5", "title": "Test", "incident_type": "OTHER",
        "request_id": "550e8400-e29b-41d4-a716-446655440006",
    })
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT h.changed_by FROM production.incident_history h "
            "JOIN production.incidents i ON i.id = h.incident_id "
            "WHERE i.code = 'INC-REC5' ORDER BY h.id LIMIT 1"
        )
        row = cur.fetchone()
    assert row is not None and row["changed_by"] == "rec5"
    tc.close()
