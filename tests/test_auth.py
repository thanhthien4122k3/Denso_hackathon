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


def test_active_endpoint_does_not_leak_password_hash(client):
    _create_user("rec6", ["OPERATOR"])
    svc = AuthService()
    u = svc.repository.find_by_username("rec6")
    r = client.post(f"/api/auth/users/{u['id']}/active", json={"active": False})
    assert r.status_code == 200
    data = r.json()["data"]
    assert "password_hash" not in data
    assert "locked_until" not in data
    assert "failed_attempts" not in data


def test_context_users_requires_admin(client):
    _create_user("rec7", ["OPERATOR"])
    tc = _client_for("rec7")
    assert tc.get("/api/context/users").status_code == 403
    tc.close()


def _incident(tc, code, request_id, start_time=None):
    payload = {"code": code, "title": "Test", "incident_type": "OTHER",
               "request_id": request_id}
    if start_time:
        payload["start_time"] = start_time
    r = tc.post("/api/incidents", json=payload)
    assert r.status_code == 201, r.text
    return r.json()["data"]["id"]


def test_close_requires_summary(client):
    _create_user("coord2", ["COORDINATOR"])
    tc = _client_for("coord2")
    iid = _incident(tc, "INC-C2", "550e8400-e29b-41d4-a716-446655440007")
    r = tc.post(f"/api/incidents/{iid}/close", json={"root_cause_status": "UNKNOWN"})
    assert r.status_code == 422
    tc.close()


def test_close_actor_from_session_and_server_time(client):
    _create_user("coord3", ["COORDINATOR"])
    tc = _client_for("coord3")
    iid = _incident(tc, "INC-C3", "550e8400-e29b-41d4-a716-446655440008")
    r = tc.post(f"/api/incidents/{iid}/close", json={
        "resolution_summary": "Đã xử lý", "closed_by": "hacker",
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["closed_by"] == "coord3"      # không tin client
    assert data["closed_at"] is not None      # server ghi nhận khi không gửi
    tc.close()


def test_close_time_before_start_rejected(client):
    _create_user("coord4", ["COORDINATOR"])
    tc = _client_for("coord4")
    iid = _incident(tc, "INC-C4", "550e8400-e29b-41d4-a716-446655440009",
                    start_time="2026-10-06T10:00:00+07:00")
    r = tc.post(f"/api/incidents/{iid}/close", json={
        "resolution_summary": "xong", "closed_at": "2020-01-01T00:00:00+00:00",
    })
    assert r.status_code == 422
    tc.close()


def test_recover_actor_from_session(client):
    _create_user("coord5", ["COORDINATOR"])
    tc = _client_for("coord5")
    iid = _incident(tc, "INC-C5", "550e8400-e29b-41d4-a716-446655440010",
                    start_time="2026-10-06T10:00:00+07:00")
    r = tc.post(f"/api/incidents/{iid}/recover", json={
        "recovered_at": "2026-10-06T10:12:00+07:00", "recovered_by": "hacker",
        "note": "Đã thay phôi mới",
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["recovered_by"] == "coord5"   # không tin client
    tc.close()


def test_operator_cannot_update_or_delete_cause(client):
    _create_user("rec8", ["OPERATOR"])
    tc = _client_for("rec8")
    iid = _incident(tc, "INC-C6", "550e8400-e29b-41d4-a716-446655440011")
    c = tc.post(f"/api/incidents/{iid}/causes", json={
        "content": "giả thuyết ban đầu", "kind": "HYPOTHESIS"})
    assert c.status_code == 201
    cause_id = c.json()["data"]["id"]
    # Không được xác nhận nguyên nhân.
    assert tc.put(f"/api/incidents/causes/{cause_id}", json={
        "kind": "CONFIRMED", "content": "đã xác nhận"}).status_code == 403
    # Không được xóa nguyên nhân.
    assert tc.delete(f"/api/incidents/causes/{cause_id}").status_code == 403
    tc.close()


def test_analysis_run_requires_incident_id(client):
    assert client.post("/api/analysis/run", json={}).status_code == 422


def test_analysis_max_depth_bounds(client):
    assert client.post("/api/analysis/run", json={
        "incident_id": 1, "max_depth": 999}).status_code == 422
    assert client.post("/api/analysis/run", json={
        "incident_id": 1, "max_depth": 0}).status_code == 422
    assert client.post("/api/analysis/run", json={
        "incident_id": 1, "max_depth": "abc"}).status_code == 422
