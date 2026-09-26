"""Hàm tạo payload hợp lệ dùng chung cho các bài kiểm thử."""

from uuid import uuid4


def make_payload(**overrides) -> dict:
    data = {
        "request_id": str(uuid4()),
        "production_date": "2026-09-26",
        "shift": "CA_1",
        "line_code": "LINE-01",
        "process_code": "ASSY-01",
        "product_code": "PROD-001",
        "lot_code": "LOT-20260926-001",
        "good_quantity": 100,
        "defect_quantity": 3,
        "operator_name": "Thanh Thiên",
        "note": "Kiểm tra cuối công đoạn",
    }
    data.update(overrides)
    return data
