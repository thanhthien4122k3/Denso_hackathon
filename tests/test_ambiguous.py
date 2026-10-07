"""Kiểm thử bối cảnh mơ hồ (AMBIGUOUS) và xác minh bối cảnh."""

import pytest
from fastapi.testclient import TestClient

from app.database import get_connection
from app.main import app
from app.services.auth_service import AuthService

ALL_TABLES = (
    "production_records", "departments", "production_lines", "processes", "machines",
    "materials", "products", "production_orders", "lots", "shifts", "data_sources",
    "datasets", "dataset_fields", "data_flows", "graph_edges", "machine_states",
    "machine_downtimes", "qc_results", "material_statuses", "incidents",
    "incident_causes", "incident_links", "analysis_runs", "analysis_impacts",
    "analysis_hypotheses", "analysis_actions", "action_tasks", "survey_items",
    "users", "user_roles", "sessions", "production_operations", "buffer_snapshots",
    "capacity_profiles", "source_object_mappings", "ingestion_records",
    "incident_experiences", "incident_history", "analysis_related_incidents",
    "incident_context_verifications",
)


@pytest.fixture(scope="module")
def amb(client):
    qualified = ", ".join(f"production.{t}" for t in ALL_TABLES)
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"TRUNCATE TABLE {qualified} RESTART IDENTITY CASCADE")
        conn.commit()
    svc = AuthService()
    if svc.repository.find_by_username("admin") is None:
        svc.create_user("admin", "Admin Test", "admin-test-password", ["ADMIN"], is_simulated=False)
    client.post("/api/auth/login", json={"username": "admin", "password": "admin-test-password"})
    assert client.post("/api/scenarios/d3-ambiguous/load").json()["data"]["loaded"] is True
    return client


def _incident_id(client, code):
    d = client.get("/api/incidents?search=" + code).json()["data"]["items"]
    return d[0]["id"]


def test_ambiguous_context_reported(client, amb):
    iid = _incident_id(amb, "INC-AMB-01")
    res = amb.post("/api/analysis/run", json={"incident_id": iid, "max_depth": 5}).json()["data"]
    ctx = res["context"]
    assert ctx["status"] == "AMBIGUOUS"
    assert len(ctx["candidates"]) == 2
    assert ctx["resolved"] is False
    assert ctx["selected_operation_id"] is None
    # Vẫn phân tích được ở mức máy/công đoạn.
    types = {i["impact_type"] for i in res["impacts"]}
    assert "DIRECT" in types


def test_verify_context_then_analysis_uses_selection(client, amb):
    iid = _incident_id(amb, "INC-AMB-01")
    ctx = amb.get(f"/api/incidents/{iid}/context").json()["data"]
    assert ctx["status"] == "AMBIGUOUS"
    candidates = ctx["candidates"]
    chosen = candidates[0]
    r = amb.post(f"/api/incidents/{iid}/context/verify", json={
        "operation_ids": [chosen["operation_id"]],
        "reason": "Theo nhật ký, lô này đang chạy tại thời điểm dừng.",
    })
    assert r.status_code == 201

    res = amb.post("/api/analysis/run", json={"incident_id": iid, "max_depth": 5}).json()["data"]
    assert res["context"]["status"] == "CONFIRMED"
    assert res["context"]["lot_code"] == chosen["lot_code"]


def test_verify_conflict_when_candidates_change(client, amb):
    iid = _incident_id(amb, "INC-AMB-01")
    # Gửi operation_id không nằm trong ứng viên -> conflict (422).
    r = amb.post(f"/api/incidents/{iid}/context/verify", json={
        "operation_ids": [999999], "reason": "sai id",
    })
    assert r.status_code == 422
