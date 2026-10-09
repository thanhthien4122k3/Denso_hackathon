"""Nghiệp vụ lớp logic hệ thống: nguồn, dataset, trường, luồng dữ liệu."""

from datetime import datetime

from app.exceptions import NotFoundError, ValidationFailedError
from app.repositories.catalog_repository import CatalogRepository
from app.repositories.system_repository import SystemRepository


def _clean(spec: dict, data) -> dict:
    if not isinstance(data, dict):
        raise ValidationFailedError("Dữ liệu phải là đối tượng JSON.")
    cleaned = {}
    for name, value in data.items():
        if name not in spec:
            raise ValidationFailedError(f"Trường không hợp lệ: {name}.")
        ftype, required, maxlen = spec[name]
        if value is None or value == "":
            if required:
                raise ValidationFailedError(f"{name} là bắt buộc.")
            continue
        if ftype == "str":
            if not isinstance(value, str):
                raise ValidationFailedError(f"{name} phải là chuỗi.")
            value = value.strip()
            if required and not value:
                raise ValidationFailedError(f"{name} là bắt buộc.")
            if maxlen and len(value) > maxlen:
                raise ValidationFailedError(f"{name} tối đa {maxlen} ký tự.")
        elif ftype == "int":
            if isinstance(value, str) and value.isdigit():
                value = int(value)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValidationFailedError(f"{name} phải là số nguyên dương.")
        elif ftype == "bool":
            if not isinstance(value, bool):
                raise ValidationFailedError(f"{name} phải là true/false.")
        elif ftype == "datetime":
            if isinstance(value, str):
                value = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if not isinstance(value, datetime):
                raise ValidationFailedError(f"{name} phải là thời gian hợp lệ.")
        cleaned[name] = value

    for name, (_, required, _) in spec.items():
        if required and name not in cleaned:
            raise ValidationFailedError(f"{name} là bắt buộc.")
    return cleaned


_SOURCE = {
    "code": ("str", True, 50), "name": ("str", True, 200),
    "source_type": ("str", True, 30), "collection_method": ("str", False, 30),
    "owner_department_id": ("int", False, 0), "location_metadata": ("str", False, 0),
    "confirmed": ("bool", False, 0), "is_simulated": ("bool", False, 0),
}
_DATASET = {
    "code": ("str", True, 50), "name": ("str", True, 200),
    "source_id": ("int", False, 0), "dataset_type": ("str", False, 30),
    "storage_location": ("str", False, 0), "collection_method": ("str", False, 30),
    "owner_department_id": ("int", False, 0), "generation_unit": ("str", False, 30),
    "update_schedule": ("str", False, 30), "event_time_field": ("str", False, 100),
    "timezone": ("str", False, 50), "update_frequency": ("str", False, 100),
    "expected_latency": ("str", False, 100), "last_received_at": ("datetime", False, 0),
    "confirmed": ("bool", False, 0), "is_simulated": ("bool", False, 0),
}
_FIELD = {
    "dataset_id": ("int", True, 0), "code": ("str", True, 100),
    "name": ("str", True, 200), "description": ("str", False, 0),
    "data_type": ("str", False, 30), "is_key": ("bool", False, 0),
    "confirmed": ("bool", False, 0),
}
_FLOW = {
    "code": ("str", True, 50), "name": ("str", True, 200),
    "source_dataset_id": ("int", True, 0), "target_dataset_id": ("int", True, 0),
    "description": ("str", False, 0), "confirmed": ("bool", False, 0),
    "is_simulated": ("bool", False, 0),
}


class SystemService:
    def __init__(self, repository: SystemRepository | None = None):
        self.repository = repository or SystemRepository()
        self.catalog = CatalogRepository()

    def _check_department(self, department_id):
        if department_id is not None and not self.catalog.exists("department", department_id):
            raise ValidationFailedError(f"Bộ phận {department_id} không tồn tại.")

    # sources
    def list_sources(self, page, page_size, search):
        return self.repository.list_sources(page, page_size, search)

    def create_source(self, data):
        cleaned = _clean(_SOURCE, data)
        self._check_department(cleaned.get("owner_department_id"))
        cleaned.setdefault("confirmed", False)
        cleaned.setdefault("is_simulated", False)
        return self.repository.create_source(cleaned)

    def update_source(self, source_id, data):
        if self.repository.get_source(source_id) is None:
            raise NotFoundError("Nguồn không tồn tại.")
        cleaned = _clean(_SOURCE, data)
        self._check_department(cleaned.get("owner_department_id"))
        return self.repository.update_source(source_id, cleaned)

    def delete_source(self, source_id):
        if self.repository.get_source(source_id) is None:
            raise NotFoundError("Nguồn không tồn tại.")
        if self.repository.source_dataset_count(source_id) > 0:
            raise ValidationFailedError("Không thể xóa nguồn đang có dataset.")
        return self.repository.delete_source(source_id)

    # datasets
    def list_datasets(self, page, page_size, source_id, search):
        return self.repository.list_datasets(page, page_size, source_id, search)

    def create_dataset(self, data):
        cleaned = _clean(_DATASET, data)
        if cleaned.get("source_id") and self.repository.get_source(cleaned["source_id"]) is None:
            raise ValidationFailedError("Hệ thống nguồn không tồn tại.")
        self._check_department(cleaned.get("owner_department_id"))
        cleaned.setdefault("confirmed", False)
        cleaned.setdefault("is_simulated", False)
        return self.repository.create_dataset(cleaned)

    def update_dataset(self, dataset_id, data):
        if self.repository.get_dataset(dataset_id) is None:
            raise NotFoundError("Dataset không tồn tại.")
        cleaned = _clean(_DATASET, data)
        self._check_department(cleaned.get("owner_department_id"))
        return self.repository.update_dataset(dataset_id, cleaned)

    def delete_dataset(self, dataset_id):
        if self.repository.get_dataset(dataset_id) is None:
            raise NotFoundError("Dataset không tồn tại.")
        return self.repository.delete_dataset(dataset_id)

    # fields
    def list_fields(self, dataset_id):
        return self.repository.list_fields(dataset_id)

    def create_field(self, data):
        cleaned = _clean(_FIELD, data)
        if self.repository.get_dataset(cleaned["dataset_id"]) is None:
            raise ValidationFailedError("Dataset không tồn tại.")
        cleaned.setdefault("is_key", False)
        cleaned.setdefault("confirmed", False)
        return self.repository.create_field(cleaned)

    def update_field(self, field_id, data):
        if self.repository.get_field(field_id) is None:
            raise NotFoundError("Trường không tồn tại.")
        cleaned = _clean(_FIELD, data)
        return self.repository.update_field(field_id, cleaned)

    def delete_field(self, field_id):
        if self.repository.get_field(field_id) is None:
            raise NotFoundError("Trường không tồn tại.")
        return self.repository.delete_field(field_id)

    # flows
    def list_flows(self, page, page_size):
        return self.repository.list_flows(page, page_size)

    def create_flow(self, data):
        cleaned = _clean(_FLOW, data)
        for key in ("source_dataset_id", "target_dataset_id"):
            if self.repository.get_dataset(cleaned[key]) is None:
                raise ValidationFailedError(f"Dataset {key} không tồn tại.")
        if cleaned["source_dataset_id"] == cleaned["target_dataset_id"]:
            raise ValidationFailedError("Dataset nguồn và đích phải khác nhau.")
        cleaned.setdefault("confirmed", False)
        cleaned.setdefault("is_simulated", False)
        return self.repository.create_flow(cleaned)

    def update_flow(self, flow_id, data):
        cleaned = _clean(_FLOW, data)
        if "source_dataset_id" in cleaned and self.repository.get_dataset(cleaned["source_dataset_id"]) is None:
            raise ValidationFailedError("Dataset nguồn không tồn tại.")
        if "target_dataset_id" in cleaned and self.repository.get_dataset(cleaned["target_dataset_id"]) is None:
            raise ValidationFailedError("Dataset đích không tồn tại.")
        return self.repository.update_flow(flow_id, cleaned)

    def delete_flow(self, flow_id):
        return self.repository.delete_flow(flow_id)
