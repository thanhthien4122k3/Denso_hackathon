"""Kiểm thử nghiệp vụ ProductionService với repository giả - không cần database."""

from datetime import date, datetime, timezone

import pytest

from app.exceptions import DuplicateRequestError, RecordConflictError
from app.schemas import ProductionRecordCreate
from app.services.production_service import ProductionService
from tests.helpers import make_payload


class FakeRepository:
    def __init__(self, existing=None, insert_raises_dup=False):
        self.existing = existing
        self.insert_raises_dup = insert_raises_dup
        self.inserted = None

    def find_by_request_id(self, request_id):
        return self.existing

    def insert(self, params):
        if self.insert_raises_dup:
            raise DuplicateRequestError()
        self.inserted = params
        return {**params, "id": 1, "created_at": datetime.now(timezone.utc)}

    def find_by_id(self, record_id):
        return None

    def list_records(self, **kwargs):
        return []

    def count_records(self, **kwargs):
        return 0

    def health_check(self):
        return True


def _row(payload: dict) -> dict:
    return {
        "id": 7,
        "request_id": payload["request_id"],
        "production_date": date.fromisoformat(payload["production_date"]),
        "shift": payload["shift"],
        "line_code": payload["line_code"],
        "process_code": payload["process_code"],
        "product_code": payload["product_code"],
        "lot_code": payload["lot_code"],
        "good_quantity": payload["good_quantity"],
        "defect_quantity": payload["defect_quantity"],
        "operator_name": payload["operator_name"],
        "note": payload["note"],
        "created_at": datetime.now(timezone.utc),
    }


def test_create_new_record_computes_derived_values():
    payload = make_payload()
    repo = FakeRepository()
    service = ProductionService(repo)

    result = service.create_record(ProductionRecordCreate(**payload))

    assert result.created is True
    assert result.record["total_quantity"] == 103
    assert result.record["defect_rate"] == pytest.approx(2.91, abs=0.01)


def test_idempotent_replay_returns_existing():
    payload = make_payload()
    repo = FakeRepository(existing=_row(payload))
    service = ProductionService(repo)

    result = service.create_record(ProductionRecordCreate(**payload))

    assert result.created is False
    assert result.record["id"] == 7
    assert repo.inserted is None


def test_same_request_id_different_content_conflicts():
    payload = make_payload()
    changed = dict(payload, good_quantity=200)
    repo = FakeRepository(existing=_row(payload))
    service = ProductionService(repo)

    with pytest.raises(RecordConflictError):
        service.create_record(ProductionRecordCreate(**changed))


def test_concurrent_duplicate_insert_returns_existing():
    payload = make_payload()
    repo = FakeRepository(existing=None, insert_raises_dup=True)
    repo.existing = _row(payload)
    service = ProductionService(repo)

    result = service.create_record(ProductionRecordCreate(**payload))

    assert result.created is False
    assert result.record["id"] == 7


def test_format_record_zero_total_rate_is_zero():
    row = _row(make_payload(good_quantity=1, defect_quantity=0))
    row["good_quantity"] = 0
    row["defect_quantity"] = 0
    formatted = ProductionService.format_record(row)
    assert formatted["total_quantity"] == 0
    assert formatted["defect_rate"] == 0.0
