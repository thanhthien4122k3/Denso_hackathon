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


def test_run_snapshot_contract_and_action_ids(d3):
    machine = _by_code(d3, "/api/catalog/machine", "M10")
    inc = d3.post("/api/incidents", json={
        "code": "INC-SNAP-01", "title": "Snapshot", "incident_type": "MACHINE_STOP",
        "source_object_type": "machine", "source_object_id": machine["id"],
        "start_time": "2026-10-06T10:00:00+07:00", "severity": "HIGH",
        "description": "test snapshot", "status": "OPEN",
        "request_id": "550e8400-e29b-41d4-a716-4466554400aa",
        "is_simulated": True,
    })
    assert inc.status_code == 201
    iid = inc.json()["data"]["id"]
    res = d3.post("/api/analysis/run", json={
        "incident_id": iid, "max_depth": 5, "duration_minutes": 15,
    }).json()["data"]
    assert res["snapshot_available"] is True
    assert res["run_id"]
    assert res["actions"] and all(a.get("id") for a in res["actions"])

    # Đọc lại lịch sử: cùng cấu trúc, giữ ID action và bối cảnh/ước tính.
    got = d3.get(f"/api/analysis/runs/{res['run_id']}").json()["data"]
    assert got["snapshot_available"] is True
    assert got["incident_id"] == iid
    assert got["context"] is not None
    assert got["capacity_estimate"] is not None
    assert got["actions"] and all(a.get("id") for a in got["actions"])

    # Lọc lịch sử phân tích theo sự cố ở backend (không lọc toàn hệ thống ở frontend).
    filtered = d3.get(f"/api/analysis/runs?source_type=INCIDENT&source_id={iid}").json()["data"]["items"]
    assert any(r["id"] == res["run_id"] for r in filtered)


def test_scope_isolates_simulated_from_real_operations(d3):
    from app.repositories.context_repository import ContextRepository
    from app.scenario_d3 import dt

    machine = _by_code(d3, "/api/catalog/machine", "M10")
    lot = _by_code(d3, "/api/catalog/lot", "LOT-B")
    process = _by_code(d3, "/api/catalog/process", "P10")

    # Thêm một operation THẬT (is_simulated=False) trùng máy/thời điểm.
    ContextRepository().create_operation({
        "lot_id": lot["id"], "process_id": process["id"], "machine_id": machine["id"],
        "started_at": dt("2026-10-06T09:55:00+07:00"), "ended_at": None,
        "status": "IN_PROGRESS", "is_simulated": False,
    })

    inc = d3.post("/api/incidents", json={
        "code": "INC-SCOPE-01", "title": "scope", "incident_type": "MACHINE_STOP",
        "source_object_type": "machine", "source_object_id": machine["id"],
        "start_time": "2026-10-06T10:00:00+07:00", "severity": "HIGH",
        "description": "scope", "status": "OPEN",
        "request_id": "550e8400-e29b-41d4-a716-4466554400bb",
        "is_simulated": True,
    })
    assert inc.status_code == 201
    iid = inc.json()["data"]["id"]
    res = d3.post("/api/analysis/run", json={"incident_id": iid, "max_depth": 5}).json()["data"]
    # Sự cố mô phỏng chỉ thấy operation mô phỏng (LOT-B), không bị AMBIGUOUS vì operation thật.
    assert res["context"]["status"] == "MATCHED"
    assert res["context"]["lot_code"] == "LOT-B"


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


def test_d3_graph_no_isolated_nodes_and_system_edges(d3):
    d = d3.get("/api/graph/map").json()["data"]
    nodes, edges = d["nodes"], d["edges"]
    connected = set()
    for e in edges:
        connected.add((e["source_type"], e["source_id"]))
        connected.add((e["target_type"], e["target_id"]))
    isolated = [(n["type"], n["code"]) for n in nodes if (n["type"], n["id"]) not in connected]
    assert isolated == [], f"node bị cô lập: {isolated}"

    kinds = {e["kind"] for e in edges}
    assert "data_flow" in kinds
    assert "data_mapping" in kinds

    # Nạp lại không tạo cạnh trùng (idempotent).
    edge_count = len(edges)
    assert d3.post("/api/scenarios/d3/load").json()["data"]["loaded"] is False
    d2 = d3.get("/api/graph/map").json()["data"]
    assert len(d2["edges"]) == edge_count


def test_d3_impact_set_unchanged_after_enrichment(d3):
    machine = _by_code(d3, "/api/catalog/machine", "M10")
    inc = d3.post("/api/incidents", json={
        "code": "INC-IMPACT-01", "title": "impact", "incident_type": "MACHINE_STOP",
        "source_object_type": "machine", "source_object_id": machine["id"],
        "start_time": "2026-10-06T10:00:00+07:00", "severity": "HIGH",
        "description": "test", "status": "OPEN",
        "request_id": "550e8400-e29b-41d4-a716-4466554400cc",
        "is_simulated": True,
    })
    assert inc.status_code == 201
    iid = inc.json()["data"]["id"]
    res = d3.post("/api/analysis/run", json={
        "incident_id": iid, "max_depth": 5, "duration_minutes": 15,
    }).json()["data"]

    # Bối cảnh + con số chuẩn không đổi.
    assert res["context"]["status"] == "MATCHED"
    assert res["context"]["lot_code"] == "LOT-B"
    assert res["context"]["process_code"] == "P10"
    assert res["buffer_estimate"]["depletion_minutes"] == 6.0
    assert res["capacity_estimate"]["estimated_quantity"] == 180.0
    assert "INC-HIST-001" in [x["code"] for x in res["related_past_incidents"]]

    # Tập tác động từ M10 không đổi dù đã làm giàu dữ liệu.
    impacts = res["impacts"]
    process_impacts = {(i["node_name"], i["impact_type"]) for i in impacts if i["node_type"] == "process"}
    assert process_impacts == {
        ("Gia công", "DIRECT"), ("Kiểm tra", "INDIRECT"), ("Đóng gói", "INDIRECT"),
    }
    lot_impacts = {(i["node_name"], i["impact_type"]) for i in impacts if i["node_type"] == "lot"}
    assert lot_impacts == {("LOT-B", "OBSERVED")}
    # Không có node khác (vật tư/chuyền/lệnh/sản phẩm) bị lan truyền từ M10.
    assert all(i["node_type"] in ("process", "lot") for i in impacts)


def test_d3_graph_map_center_depth(d3):
    machine = _by_code(d3, "/api/catalog/machine", "M10")
    p10 = _by_code(d3, "/api/catalog/process", "P10")
    p20 = _by_code(d3, "/api/catalog/process", "P20")
    d = d3.get(f"/api/graph/map?center=machine:{machine['id']}&depth=1").json()["data"]
    keys = {(n["type"], n["id"]) for n in d["nodes"]}
    assert ("machine", machine["id"]) in keys
    assert ("process", p10["id"]) in keys       # kề 1 bước
    assert ("process", p20["id"]) not in keys   # cách 2 bước


def test_d3_graph_map_limit(d3):
    d = d3.get("/api/graph/map?limit=5").json()["data"]
    assert len(d["nodes"]) <= 5
    assert d.get("limited") is True
    # Mỗi cạnh trả về có hai đầu nằm trong tập node trả về.
    keys = {(n["type"], n["id"]) for n in d["nodes"]}
    for e in d["edges"]:
        assert (e["source_type"], e["source_id"]) in keys
        assert (e["target_type"], e["target_id"]) in keys
