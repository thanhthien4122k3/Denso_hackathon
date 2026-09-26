"""Nghiệp vụ ghi nhận vận hành: kiểm tra dữ liệu và tham chiếu."""

from datetime import datetime

from app.exceptions import ValidationFailedError
from app.repositories.catalog_repository import CatalogRepository
from app.repositories.operations_repository import OperationsRepository

STATES = {"RUNNING", "STOPPED", "MAINTENANCE", "UNKNOWN"}
QC_RESULTS = {"PASS", "FAIL", "HOLD"}


def _dt(value):
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            raise ValidationFailedError("Thời gian không hợp lệ.") from None
    raise ValidationFailedError("Thời gian không hợp lệ.")


class OperationsService:
    def __init__(self, repository: OperationsRepository | None = None):
        self.repository = repository or OperationsRepository()
        self.catalog = CatalogRepository()

    def _require_entity(self, key: str, record_id, label: str):
        if record_id is None:
            return
        if not self.catalog.exists(key, record_id):
            raise ValidationFailedError(f"{label} không tồn tại.")

    def create_state(self, data):
        if not isinstance(data, dict):
            raise ValidationFailedError("Dữ liệu phải là đối tượng JSON.")
        machine_id = data.get("machine_id")
        if not machine_id:
            raise ValidationFailedError("machine_id là bắt buộc.")
        self._require_entity("machine", machine_id, "Máy")
        state = data.get("state")
        if state not in STATES:
            raise ValidationFailedError(f"state phải thuộc {sorted(STATES)}.")
        event_time = _dt(data.get("event_time"))
        cleaned = {
            "machine_id": machine_id,
            "event_time": event_time,
            "state": state,
            "error_code": (data.get("error_code") or "").strip() or None,
            "note": (data.get("note") or "").strip() or None,
            "is_simulated": bool(data.get("is_simulated", False)),
        }
        return self.repository.create_state(cleaned)

    def create_downtime(self, data):
        if not isinstance(data, dict):
            raise ValidationFailedError("Dữ liệu phải là đối tượng JSON.")
        machine_id = data.get("machine_id")
        if not machine_id:
            raise ValidationFailedError("machine_id là bắt buộc.")
        self._require_entity("machine", machine_id, "Máy")
        start_time = _dt(data.get("start_time"))
        end_time = _dt(data.get("end_time")) if data.get("end_time") else None
        if end_time is not None and end_time < start_time:
            raise ValidationFailedError("Thời gian kết thúc không thể trước lúc bắt đầu.")
        cleaned = {
            "machine_id": machine_id,
            "start_time": start_time,
            "end_time": end_time,
            "reason": (data.get("reason") or "").strip() or None,
            "error_code": (data.get("error_code") or "").strip() or None,
            "operator_name": (data.get("operator_name") or "").strip() or None,
            "is_simulated": bool(data.get("is_simulated", False)),
        }
        return self.repository.create_downtime(cleaned)

    def close_downtime(self, downtime_id, end_time):
        return self.repository.update_downtime_end(downtime_id, _dt(end_time))

    def create_qc(self, data):
        if not isinstance(data, dict):
            raise ValidationFailedError("Dữ liệu phải là đối tượng JSON.")
        lot_id = data.get("lot_id")
        if not lot_id:
            raise ValidationFailedError("lot_id là bắt buộc.")
        self._require_entity("lot", lot_id, "Lot")
        self._require_entity("product", data.get("product_id"), "Sản phẩm")
        self._require_entity("process", data.get("process_id"), "Công đoạn")
        result = data.get("result")
        if result not in QC_RESULTS:
            raise ValidationFailedError(f"result phải thuộc {sorted(QC_RESULTS)}.")
        inspected = data.get("inspected_qty")
        defect = data.get("defect_qty")
        if isinstance(inspected, bool) or not isinstance(inspected, int) or inspected < 0:
            raise ValidationFailedError("inspected_qty phải là số nguyên >= 0.")
        if isinstance(defect, bool) or not isinstance(defect, int) or defect < 0:
            raise ValidationFailedError("defect_qty phải là số nguyên >= 0.")
        if defect > inspected:
            raise ValidationFailedError("Số lượng lỗi không thể vượt số lượng kiểm tra.")
        cleaned = {
            "lot_id": lot_id,
            "product_id": data.get("product_id"),
            "process_id": data.get("process_id"),
            "check_time": _dt(data.get("check_time")),
            "inspected_qty": inspected,
            "defect_qty": defect,
            "defect_type": (data.get("defect_type") or "").strip() or None,
            "result": result,
            "note": (data.get("note") or "").strip() or None,
            "is_simulated": bool(data.get("is_simulated", False)),
        }
        return self.repository.create_qc(cleaned)

    def create_material(self, data):
        if not isinstance(data, dict):
            raise ValidationFailedError("Dữ liệu phải là đối tượng JSON.")
        material_id = data.get("material_id")
        if not material_id:
            raise ValidationFailedError("material_id là bắt buộc.")
        self._require_entity("material", material_id, "Vật tư")
        available = data.get("available_qty")
        if isinstance(available, bool) or not isinstance(available, (int, float)):
            raise ValidationFailedError("available_qty phải là số.")
        if available < 0:
            raise ValidationFailedError("available_qty không thể âm.")
        cleaned = {
            "material_id": material_id,
            "recorded_at": _dt(data.get("recorded_at")),
            "available_qty": available,
            "unit": (data.get("unit") or "").strip() or None,
            "scope": (data.get("scope") or "").strip() or None,
            "is_simulated": bool(data.get("is_simulated", False)),
        }
        return self.repository.create_material(cleaned)

    def list_states(self, page, page_size, machine_id, from_time, to_time):
        return self.repository.list_states(page, page_size, machine_id, from_time, to_time)

    def list_downtimes(self, page, page_size, machine_id, from_time, to_time):
        return self.repository.list_downtimes(page, page_size, machine_id, from_time, to_time)

    def list_qc(self, page, page_size, lot_id, result):
        return self.repository.list_qc(page, page_size, lot_id, result)

    def list_material(self, page, page_size, material_id):
        return self.repository.list_material(page, page_size, material_id)
