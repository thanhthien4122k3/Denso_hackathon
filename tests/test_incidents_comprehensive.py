"""Comprehensive integration tests for Incidents (TC-INC-01 to TC-INC-17)."""

import uuid
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


def test_tc_inc_01_create_incident_success(demo):
    req_id = str(uuid.uuid4())
    payload = {
        "code": "INC-TEST-001",
        "title": "Dừng máy M-01 đột ngột",
        "incident_type": "MACHINE_STOP",
        "severity": "HIGH",
        "status": "OPEN",
        "source_object_type": "machine",
        "source_object_id": 1,
        "start_time": "2026-10-09T08:00:00+07:00",
        "description": "Lỗi servo điều khiển trục X",
        "request_id": req_id,
    }
    resp = demo.post("/api/incidents", json=payload)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["code"] == "INC-TEST-001"
    assert data["title"] == "Dừng máy M-01 đột ngột"
    assert data["incident_type"] == "MACHINE_STOP"
    assert data["severity"] == "HIGH"
    assert data["status"] == "OPEN"
    assert data["request_id"] == req_id


def test_tc_inc_02_validation_missing_or_invalid_fields(demo):
    # Missing code
    r1 = demo.post("/api/incidents", json={"title": "No Code", "incident_type": "OTHER", "request_id": str(uuid.uuid4())})
    assert r1.status_code == 422

    # Missing title
    r2 = demo.post("/api/incidents", json={"code": "INC-NO-TITLE", "incident_type": "OTHER", "request_id": str(uuid.uuid4())})
    assert r2.status_code == 422

    # Invalid incident_type
    r3 = demo.post("/api/incidents", json={"code": "INC-BAD-TYPE", "title": "Bad Type", "incident_type": "INVALID_TYPE", "request_id": str(uuid.uuid4())})
    assert r3.status_code == 422

    # Invalid severity
    r4 = demo.post("/api/incidents", json={"code": "INC-BAD-SEV", "title": "Bad Sev", "incident_type": "OTHER", "severity": "SUPER_HIGH", "request_id": str(uuid.uuid4())})
    assert r4.status_code == 422


def test_tc_inc_03_duplicate_code_conflict(demo):
    req_id1 = str(uuid.uuid4())
    req_id2 = str(uuid.uuid4())
    payload1 = {"code": "INC-DUP-CODE", "title": "Incident 1", "incident_type": "OTHER", "request_id": req_id1}
    r1 = demo.post("/api/incidents", json=payload1)
    assert r1.status_code == 201

    payload2 = {"code": "INC-DUP-CODE", "title": "Incident 2", "incident_type": "OTHER", "request_id": req_id2}
    r2 = demo.post("/api/incidents", json=payload2)
    assert r2.status_code in (400, 409, 422)


def test_tc_inc_04_source_object_validation(demo):
    # source_object_type provided but source_object_id missing
    payload1 = {
        "code": "INC-SRC-1",
        "title": "Missing source ID",
        "incident_type": "QUALITY",
        "source_object_type": "lot",
        "request_id": str(uuid.uuid4()),
    }
    r1 = demo.post("/api/incidents", json=payload1)
    assert r1.status_code == 422

    # Invalid source_object_type
    payload2 = {
        "code": "INC-SRC-2",
        "title": "Invalid source type",
        "incident_type": "QUALITY",
        "source_object_type": "unknown_object_type",
        "source_object_id": 1,
        "request_id": str(uuid.uuid4()),
    }
    r2 = demo.post("/api/incidents", json=payload2)
    assert r2.status_code == 422


def test_tc_inc_05_idempotency_request_id(demo):
    req_id = str(uuid.uuid4())
    payload = {
        "code": "INC-IDEM-01",
        "title": "Idempotency Test",
        "incident_type": "MATERIAL_SHORTAGE",
        "request_id": req_id,
    }
    r1 = demo.post("/api/incidents", json=payload)
    assert r1.status_code == 201
    id1 = r1.json()["data"]["id"]

    # Post exact same payload with same request_id
    r2 = demo.post("/api/incidents", json=payload)
    assert r2.status_code == 200
    assert r2.json()["data"]["id"] == id1
    assert "Sự cố đã tồn tại" in r2.json()["message"]


def test_tc_inc_06_search_by_keyword(demo):
    r = demo.get("/api/incidents?search=INC-TEST-001")
    assert r.status_code == 200
    items = r.json()["data"]["items"]
    assert any(i["code"] == "INC-TEST-001" for i in items)

    r_title = demo.get("/api/incidents?search=Dừng máy")
    assert r_title.status_code == 200
    assert len(r_title.json()["data"]["items"]) >= 1


def test_tc_inc_07_filtering_by_status_and_type(demo):
    r1 = demo.get("/api/incidents?status=OPEN")
    assert r1.status_code == 200
    assert all(i["status"] == "OPEN" for i in r1.json()["data"]["items"])

    r2 = demo.get("/api/incidents?incident_type=MACHINE_STOP")
    assert r2.status_code == 200
    assert all(i["incident_type"] == "MACHINE_STOP" for i in r2.json()["data"]["items"])


def test_tc_inc_08_empty_search(demo):
    r = demo.get("/api/incidents?search=NON_EXISTENT_KEYWORD_XYZ_999")
    assert r.status_code == 200
    assert len(r.json()["data"]["items"]) == 0
    assert r.json()["data"]["pagination"]["total"] == 0


def test_tc_inc_09_pagination(demo):
    r = demo.get("/api/incidents?page=1&page_size=2")
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data["items"]) <= 2
    assert "pagination" in data
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["page_size"] == 2


def test_tc_inc_10_get_detail_and_404(demo):
    # Find existing incident
    d = demo.get("/api/incidents?page_size=1").json()["data"]["items"][0]
    inc_id = d["id"]

    r = demo.get(f"/api/incidents/{inc_id}")
    assert r.status_code == 200
    assert r.json()["data"]["id"] == inc_id

    r_404 = demo.get("/api/incidents/999999")
    assert r_404.status_code == 404


def test_tc_inc_11_update_incident_status_and_fields(demo):
    # Get an incident
    inc = demo.get("/api/incidents?page_size=1").json()["data"]["items"][0]
    inc_id = inc["id"]

    # Update status to INVESTIGATING
    upd1 = demo.put(f"/api/incidents/{inc_id}", json={"status": "INVESTIGATING", "description": "Cần điều tra thêm"})
    assert upd1.status_code == 200
    data = upd1.json()["data"]
    assert data["status"] == "INVESTIGATING"
    assert data["description"] == "Cần điều tra thêm"

    # Invalid status update
    upd2 = demo.put(f"/api/incidents/{inc_id}", json={"status": "INVALID_STATUS"})
    assert upd2.status_code == 422


def test_tc_inc_12_causes_crud(demo):
    inc = demo.get("/api/incidents?page_size=1").json()["data"]["items"][0]
    inc_id = inc["id"]

    # 1. Create cause HYPOTHESIS
    c1 = demo.post(f"/api/incidents/{inc_id}/causes", json={
        "content": "Nghi ngờ hỏng vòng bi",
        "kind": "HYPOTHESIS",
        "evidence": "Tiếng ồn lớn từ động cơ",
        "rule_id": "RULE_BEARING_01",
    })
    assert c1.status_code == 201
    cause_id = c1.json()["data"]["id"]

    # 2. List causes
    causes_list = demo.get(f"/api/incidents/{inc_id}/causes").json()["data"]
    assert any(c["id"] == cause_id for c in causes_list)

    # 3. Update cause to CONFIRMED
    c_upd = demo.put(f"/api/incidents/causes/{cause_id}", json={
        "kind": "CONFIRMED",
        "confirmed_by": "Nguyễn Văn A",
    })
    assert c_upd.status_code == 200
    assert c_upd.json()["data"]["kind"] == "CONFIRMED"
    assert c_upd.json()["data"]["confirmed_by"] == "Nguyễn Văn A"

    # 4. Delete cause
    c_del = demo.delete(f"/api/incidents/causes/{cause_id}")
    assert c_del.status_code == 200

    # 5. Invalid cause kind
    c_invalid = demo.post(f"/api/incidents/{inc_id}/causes", json={"content": "Lỗi", "kind": "UNKNOWN"})
    assert c_invalid.status_code == 422


def test_tc_inc_13_links_crud(demo):
    inc = demo.get("/api/incidents?page_size=1").json()["data"]["items"][0]
    inc_id = inc["id"]

    # 1. Create link
    l1 = demo.post(f"/api/incidents/{inc_id}/links", json={
        "source_type": "machine_state",
        "source_id": 1,
    })
    assert l1.status_code == 201
    link_id = l1.json()["data"]["id"]

    # 2. List links
    links_list = demo.get(f"/api/incidents/{inc_id}/links").json()["data"]
    assert any(l["id"] == link_id for l in links_list)

    # 3. Delete link
    l_del = demo.delete(f"/api/incidents/links/{link_id}")
    assert l_del.status_code == 200

    # 4. Invalid source_type
    l_invalid = demo.post(f"/api/incidents/{inc_id}/links", json={"source_type": "invalid_source", "source_id": 1})
    assert l_invalid.status_code == 422


def test_tc_inc_14_impact_analysis_integration(demo):
    d = demo.get("/api/incidents?page_size=100").json()["data"]["items"]
    inc = next(i for i in d if i["code"] == "INC-001")

    # Trigger analysis run
    run_resp = demo.post("/api/analysis/run", json={"incident_id": inc["id"], "max_depth": 5})
    assert run_resp.status_code == 200
    run_data = run_resp.json()["data"]
    assert run_data["source_incident_id"] == inc["id"]
    assert len(run_data["impacts"]) > 0


def test_tc_inc_15_historical_analysis_runs_filtering(demo):
    d = demo.get("/api/incidents?page_size=100").json()["data"]["items"]
    inc = next(i for i in d if i["code"] == "INC-001")

    runs = demo.get("/api/analysis/runs?page_size=50").json()["data"]["items"]
    inc_runs = [r for r in runs if r.get("source_type") == "INCIDENT" and r.get("source_id") == inc["id"]]
    assert len(inc_runs) >= 1


def test_tc_inc_16_dashboard_stats_integration(demo):
    dash = demo.get("/api/dashboard").json()["data"]
    metrics = dash["metrics"]
    incidents = dash["incidents"]

    assert "open_incidents" in metrics
    assert metrics["open_incidents"] >= 0
    assert isinstance(incidents, list)


def test_tc_inc_17_simulated_incidents_flag(demo):
    d = demo.get("/api/incidents?page_size=100").json()["data"]["items"]
    demo_incidents = [i for i in d if i["code"] in ("INC-001", "INC-002", "INC-003")]
    assert len(demo_incidents) == 3
    assert all(i["is_simulated"] is True for i in demo_incidents)
