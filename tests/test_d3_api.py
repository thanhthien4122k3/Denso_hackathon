"""Integration test cho D3 (chạy trên database test, skip nếu không có PostgreSQL)."""

import pytest

from app.database import get_connection

ALL_TABLES = (
    "production_records", "departments", "production_lines", "processes", "machines",
    "materials", "products", "production_orders", "lots", "shifts", "data_sources",
    "datasets", "dataset_fields", "data_flows", "graph_edges", "machine_states",
    "machine_downtimes", "qc_results", "material_statuses", "incidents",
    "incident_causes", "incident_links", "analysis_runs", "analysis_impacts",
    "analysis_hypotheses", "analysis_actions", "action_tasks", "survey_items",
)


@pytest.fixture(scope="module")
def demo(client):
    qualified = ", ".join(f"production.{t}" for t in ALL_TABLES)
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"TRUNCATE TABLE {qualified} RESTART IDENTITY CASCADE")
        conn.commit()
    client.post("/api/scenarios/load")
    return client


def _incident_id(client, code):
    d = client.get("/api/incidents?page_size=100").json()
    for i in d["data"]["items"]:
        if i["code"] == code:
            return i["id"]
    raise AssertionError(f"không tìm thấy sự cố {code}")


def test_catalog_crud_and_deactivate(demo):
    resp = demo.post("/api/catalog/department", json={"code": "TST", "name": "Test Dept"})
    assert resp.status_code == 201
    did = resp.json()["data"]["id"]

    listing = demo.get("/api/catalog/department?search=TST").json()
    assert listing["data"]["pagination"]["total"] >= 1

    deact = demo.post(f"/api/catalog/department/{did}/deactivate")
    assert deact.status_code == 200
    assert deact.json()["data"]["active"] is False


def test_catalog_duplicate_code_conflict(demo):
    demo.post("/api/catalog/department", json={"code": "DUP", "name": "A"})
    resp = demo.post("/api/catalog/department", json={"code": "DUP", "name": "B"})
    assert resp.status_code == 409


def test_catalog_unknown_key_404(demo):
    assert demo.get("/api/catalog/nope").status_code == 404


def test_load_demo_idempotent(demo):
    r = demo.post("/api/scenarios/load")
    assert r.json()["data"]["loaded"] is False  # đã nạp từ trước


def test_graph_map_has_nodes_and_edges(demo):
    d = demo.get("/api/graph/map").json()["data"]
    assert len(d["nodes"]) > 0
    assert len(d["edges"]) > 0


def test_graph_edge_validation(demo):
    resp = demo.post("/api/graph/edges", json={
        "source_type": "machine", "source_id": 1,
        "target_type": "machine", "target_id": 2,
        "kind": "data_mapping",
    })
    assert resp.status_code == 422  # data_mapping không hợp lệ giữa 2 node nghiệp vụ


def test_graph_edge_self_loop_rejected(demo):
    resp = demo.post("/api/graph/edges", json={
        "source_type": "process", "source_id": 1,
        "target_type": "process", "target_id": 1,
        "kind": "production_dependency",
    })
    assert resp.status_code == 422
    assert "tự nối" in resp.json()["message"]


def test_graph_edge_duplicate_conflict(demo):
    d = demo.get("/api/graph/map").json()["data"]

    def node_id(ntype, code):
        for n in d["nodes"]:
            if n["type"] == ntype and n["code"] == code:
                return n["id"]
        return None

    p1 = node_id("process", "ASSY-01")
    p2 = node_id("process", "TEST-01")
    payload = {
        "source_type": "process", "source_id": p2, "target_type": "process",
        "target_id": p1, "kind": "production_dependency",
    }
    first = demo.post("/api/graph/edges", json=payload)
    assert first.status_code == 201
    second = demo.post("/api/graph/edges", json=payload)
    assert second.status_code == 409
    assert "tồn tại" in second.json()["message"]


def test_incident_idempotent_create(demo):
    payload = {"code": "INC-TST", "title": "Test", "incident_type": "OTHER",
               "request_id": "550e8400-e29b-41d4-a716-446655440000"}
    first = demo.post("/api/incidents", json=payload)
    assert first.status_code == 201
    second = demo.post("/api/incidents", json=payload)
    assert second.status_code == 200
    assert second.json()["data"]["id"] == first.json()["data"]["id"]


def test_analysis_machine_stop(demo):
    rid = _incident_id(demo, "INC-001")
    d = demo.post("/api/analysis/run", json={"incident_id": rid, "max_depth": 5}).json()["data"]
    types = {i["impact_type"] for i in d["impacts"]}
    assert "DIRECT" in types and "INDIRECT" in types
    assert d["hypotheses"]
    assert d["actions"]


def test_analysis_quality_hypothesis(demo):
    rid = _incident_id(demo, "INC-002")
    d = demo.post("/api/analysis/run", json={"incident_id": rid}).json()["data"]
    assert any(h["rule_id"] == "H_MATERIAL_BATCH" for h in d["hypotheses"])


def test_quantification_only_for_machine_stop(demo):
    machine = _incident_id(demo, "INC-001")
    quality = _incident_id(demo, "INC-002")

    d1 = demo.post("/api/analysis/run", json={"incident_id": machine,
                                              "duration_minutes": 30, "rate_per_minute": 2}).json()["data"]
    assert d1["quantification"]["available"] is True
    assert d1["quantification"]["lost_quantity"] == 60

    d2 = demo.post("/api/analysis/run", json={"incident_id": quality,
                                              "duration_minutes": 30, "rate_per_minute": 2}).json()["data"]
    assert d2["quantification"]["available"] is False


def test_analysis_terminates_on_cycle(demo):
    # thêm cạnh tạo chu trình process(1)->process(2)->process(1)
    d = demo.get("/api/graph/map").json()["data"]
    def node_id(ntype, code):
        for n in d["nodes"]:
            if n["type"] == ntype and n["code"] == code:
                return n["id"]
        return None
    p1, p2 = node_id("process", "ASSY-01"), node_id("process", "TEST-01")
    demo.post("/api/graph/edges", json={
        "source_type": "process", "source_id": p2, "target_type": "process",
        "target_id": p1, "kind": "production_dependency", "is_simulated": True,
    })
    rid = _incident_id(demo, "INC-001")
    resp = demo.post("/api/analysis/run", json={"incident_id": rid, "max_depth": 10})
    assert resp.status_code == 200


def test_demo_separation(demo):
    d = demo.get("/api/incidents?page_size=100").json()["data"]["items"]
    demo_incidents = [i for i in d if i["code"] in ("INC-001", "INC-002", "INC-003")]
    assert len(demo_incidents) == 3
    assert all(i["is_simulated"] for i in demo_incidents)


def test_tasks_flow(demo):
    created = demo.post("/api/tasks", json={"title": "Kiểm tra máy", "priority": "HIGH"})
    assert created.status_code == 201
    tid = created.json()["data"]["id"]
    upd = demo.post(f"/api/tasks/{tid}/status", json={"status": "DONE"})
    assert upd.json()["data"]["status"] == "DONE"


def test_survey_seeded(demo):
    d = demo.get("/api/survey").json()["data"]
    groups = {i["group_code"] for i in d}
    assert "G1" in groups and "G9" in groups


def test_production_records_still_works(demo):
    from tests.helpers import make_payload
    resp = demo.post("/api/production-records", json=make_payload())
    assert resp.status_code == 201
