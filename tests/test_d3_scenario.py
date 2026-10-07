"""Integration test cho bộ dữ liệu mô phỏng DEMO-D3-01 và luồng phân tích mở rộng."""

import pytest

from app.database import get_connection

ALL_TABLES = (
    "production_records", "departments", "production_lines", "processes", "machines",
    "materials", "products", "production_orders", "lots", "shifts", "data_sources",
    "datasets", "dataset_fields", "data_flows", "graph_edges", "machine_states",
    "machine_downtimes", "qc_results", "material_statuses", "incidents",
    "incident_causes", "incident_links", "analysis_runs", "analysis_impacts",
    "analysis_hypotheses", "analysis_actions", "action_tasks", "survey_items",
    "users", "production_operations", "buffer_snapshots", "capacity_profiles",
    "source_object_mappings", "ingestion_records", "incident_experiences",
    "incident_history", "analysis_related_incidents",
)


@pytest.fixture(scope="module")
def d3(client):
    qualified = ", ".join(f"production.{t}" for t in ALL_TABLES)
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"TRUNCATE TABLE {qualified} RESTART IDENTITY CASCADE")
        conn.commit()
    # Truncate xóa tài khoản admin; tạo lại và đăng nhập trước khi nạp seed.
    from app.services.auth_service import AuthService
    svc = AuthService()
    if svc.repository.find_by_username("admin") is None:
        svc.create_user("admin", "Admin Test", "admin-test-password", ["ADMIN"], is_simulated=False)
    client.post("/api/auth/login", json={"username": "admin", "password": "admin-test-password"})
    resp = client.post("/api/scenarios/d3/load")
    assert resp.json()["data"]["loaded"] is True
    return client


def _by_code(client, path, code):
    d = client.get(f"{path}?page_size=100").json()["data"]["items"]
    for i in d:
        if i["code"] == code:
            return i
    raise AssertionError(f"không tìm thấy {code} trong {path}")


def test_d3_load_idempotent(d3):
    assert d3.post("/api/scenarios/d3/load").json()["data"]["loaded"] is False


def test_d3_catalog_seeded(d3):
    dept = _by_code(d3, "/api/catalog/department", "PROD")
    assert dept["is_simulated"] is True
    machine = _by_code(d3, "/api/catalog/machine", "M10")
    assert machine is not None


def test_d3_context_operations_seeded(d3):
    d = d3.get("/api/context/operations?page_size=100").json()["data"]["items"]
    assert len(d) == 3


def test_d3_ingestion_unmapped(d3):
    d = d3.get("/api/context/ingestions?status=NEEDS_MAPPING").json()["data"]["items"]
    assert any(i["error"] and "CNC-UNKNOWN" in i["error"] for i in d)


def test_d3_report_error_and_analysis(d3):
    machine = _by_code(d3, "/api/catalog/machine", "M10")
    # Bước 2: báo lỗi máy tại 10:00.
    r = d3.post("/api/operations/report-machine-error", json={
        "machine_id": machine["id"],
        "event_time": "2026-10-06T10:00:00+07:00",
        "error_code": "E-DEMO-01",
        "observation": "Máy dừng, màn hình báo lỗi bộ phận cấp phôi",
        "is_simulated": True,
    })
    assert r.status_code == 201
    assert r.json()["data"]["state"]["state"] == "STOPPED"

    # Tạo sự cố từ bản ghi.
    inc = d3.post("/api/incidents", json={
        "code": "INC-DEMO-01", "title": "Máy M10 dừng - lỗi cấp phôi",
        "incident_type": "MACHINE_STOP", "source_object_type": "machine",
        "source_object_id": machine["id"],
        "start_time": "2026-10-06T10:00:00+07:00", "severity": "HIGH",
        "description": "Máy dừng, màn hình báo lỗi bộ phận cấp phôi.",
        "status": "OPEN", "request_id": "550e8400-e29b-41d4-a716-446655440001",
        "is_simulated": True,
    })
    assert inc.status_code == 201
    incident_id = inc.json()["data"]["id"]

    # Bước 3: chạy phân tích, giả định dừng 15 phút.
    res = d3.post("/api/analysis/run", json={
        "incident_id": incident_id, "max_depth": 5, "duration_minutes": 15,
    }).json()["data"]

    ctx = res["context"]
    assert ctx["resolved"] is True
    assert ctx["lot_code"] == "LOT-B"   # bối cảnh đang chạy tại 10:00 là LOT-B
    assert ctx["process_code"] == "P10"

    buf = res["buffer_estimate"]
    assert buf["available"] is True
    assert buf["depletion_minutes"] == 6.0   # 60/10 = 6 phút

    cap = res["capacity_estimate"]
    assert cap is not None
    assert cap["estimated_quantity"] == 180.0  # 15 * 12

    # Sự cố tương tự: INC-HIST-001 (cùng máy + mã lỗi).
    related_codes = [x["code"] for x in res["related_past_incidents"]]
    assert "INC-HIST-001" in related_codes

    # Hành động đề xuất gồm MAINT, PROD, PLAN.
    dept_codes = {a["department_code"] for a in res["actions"]}
    assert {"MAINT", "PROD", "PLAN"} <= dept_codes


def test_d3_task_from_action_no_duplicate(d3):
    machine = _by_code(d3, "/api/catalog/machine", "M10")
    incidents = d3.get("/api/incidents?search=INC-DEMO-01").json()["data"]["items"]
    incident_id = incidents[0]["id"]

    runs = d3.get("/api/analysis/runs?page_size=100").json()["data"]["items"]
    run_id = runs[0]["id"]
    actions = d3.get(f"/api/analysis/runs/{run_id}").json()["data"]["actions"]
    maint = next(a for a in actions if a["department_name"] and "Bảo trì" in a["department_name"]
                 or a["department_name"] in ("MAINT", "Bảo trì"))

    payload = {"analysis_action_id": maint["id"], "title": maint["action"],
               "department_id": maint["department_id"], "is_simulated": True}
    first = d3.post("/api/tasks/from-action", json=payload)
    assert first.status_code == 201
    second = d3.post("/api/tasks/from-action", json=payload)
    assert second.status_code == 200
    assert second.json()["data"]["id"] == first.json()["data"]["id"]
