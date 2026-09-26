"""Integration test API chạy trên database test riêng (sẽ skip nếu không có DB)."""

import pytest

from app.database import get_connection
from tests.helpers import make_payload


@pytest.fixture(autouse=True)
def clean_table(client):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE production.production_records")
        conn.commit()


def test_health_ok(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_create_record_201(client):
    resp = client.post("/api/production-records", json=make_payload())
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["id"] >= 1
    assert body["data"]["total_quantity"] == 103
    assert body["data"]["defect_rate"] == pytest.approx(2.91, abs=0.01)


def test_same_request_id_same_content_returns_existing(client):
    payload = make_payload()
    first = client.post("/api/production-records", json=payload)
    assert first.status_code == 201

    second = client.post("/api/production-records", json=payload)
    assert second.status_code == 200
    assert second.json()["data"]["id"] == first.json()["data"]["id"]

    listing = client.get("/api/production-records").json()
    assert listing["data"]["pagination"]["total"] == 1


def test_same_request_id_different_content_conflicts(client):
    payload = make_payload()
    assert client.post("/api/production-records", json=payload).status_code == 201

    changed = dict(payload, good_quantity=500)
    resp = client.post("/api/production-records", json=changed)
    assert resp.status_code == 409


def test_total_zero_rejected(client):
    resp = client.post(
        "/api/production-records",
        json=make_payload(good_quantity=0, defect_quantity=0),
    )
    assert resp.status_code == 422


def test_invalid_shift_rejected(client):
    resp = client.post("/api/production-records", json=make_payload(shift="CA_4"))
    assert resp.status_code == 422


def test_list_pagination_and_filter(client):
    for i in range(3):
        payload = make_payload(
            lot_code=f"LOT-{i}",
            line_code="LINE-01",
            production_date="2026-09-26",
        )
        assert client.post("/api/production-records", json=payload).status_code == 201

    resp = client.get(
        "/api/production-records",
        params={"page": 1, "page_size": 2, "line_code": "LINE-01"},
    )
    body = resp.json()
    assert resp.status_code == 200
    assert body["data"]["pagination"]["total"] == 3
    assert body["data"]["pagination"]["total_pages"] == 2
    assert len(body["data"]["items"]) == 2

    filtered = client.get(
        "/api/production-records", params={"lot_code": "LOT-1"}
    ).json()
    assert filtered["data"]["pagination"]["total"] == 1


def test_date_range_validation(client):
    resp = client.get(
        "/api/production-records",
        params={"date_from": "2026-09-27", "date_to": "2026-09-26"},
    )
    assert resp.status_code == 422


def test_get_detail_and_not_found(client):
    created = client.post("/api/production-records", json=make_payload())
    record_id = created.json()["data"]["id"]

    detail = client.get(f"/api/production-records/{record_id}")
    assert detail.status_code == 200
    assert detail.json()["data"]["id"] == record_id

    missing = client.get("/api/production-records/999999")
    assert missing.status_code == 404
