"""Nghiệp vụ sự cố: tạo (chống trùng), cập nhật, nguyên nhân, liên kết."""

from datetime import datetime
from uuid import UUID

from app.exceptions import DuplicateCodeError, NotFoundError, ValidationFailedError
from app.graph import NODE_TYPES
from app.repositories.catalog_repository import CatalogRepository
from app.repositories.graph_repository import GraphRepository
from app.repositories.incident_repository import IncidentRepository

INCIDENT_TYPES = {"MACHINE_STOP", "QUALITY", "MATERIAL_SHORTAGE", "DATA_DELAY", "OTHER"}
SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
STATUSES = {"OPEN", "INVESTIGATING", "MITIGATING", "RESOLVED"}
CAUSE_KINDS = {"HYPOTHESIS", "CONFIRMED"}
LINK_TYPES = {"machine_state", "downtime", "qc", "material_status", "production_record"}


def _dt(value):
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            raise ValidationFailedError("Thời gian không hợp lệ.") from None
    raise ValidationFailedError("Thời gian không hợp lệ.")


class IncidentService:
    def __init__(self, repository: IncidentRepository | None = None):
        self.repository = repository or IncidentRepository()
        self.catalog = CatalogRepository()
        self.graph = GraphRepository()

    def _clean(self, data) -> dict:
        if not isinstance(data, dict):
            raise ValidationFailedError("Dữ liệu phải là đối tượng JSON.")

        code = (data.get("code") or "").strip()
        title = (data.get("title") or "").strip()
        if not code:
            raise ValidationFailedError("code là bắt buộc.")
        if not title:
            raise ValidationFailedError("title là bắt buộc.")
        if data.get("incident_type") not in INCIDENT_TYPES:
            raise ValidationFailedError(f"incident_type phải thuộc {sorted(INCIDENT_TYPES)}.")

        severity = data.get("severity", "MEDIUM")
        if severity not in SEVERITIES:
            raise ValidationFailedError(f"severity phải thuộc {sorted(SEVERITIES)}.")
        status = data.get("status", "OPEN")
        if status not in STATUSES:
            raise ValidationFailedError(f"status phải thuộc {sorted(STATUSES)}.")

        try:
            request_id = UUID(str(data.get("request_id")))
        except (ValueError, TypeError):
            raise ValidationFailedError("request_id phải là UUID hợp lệ.") from None

        source_type = (data.get("source_object_type") or "").strip() or None
        source_id = data.get("source_object_id")
        if source_type and source_type not in NODE_TYPES:
            raise ValidationFailedError(f"source_object_type không hợp lệ: {source_type}.")
        if source_type and not source_id:
            raise ValidationFailedError("source_object_id là bắt buộc khi có source_object_type.")

        assigned = data.get("assigned_department_id")
        if isinstance(assigned, str) and assigned.isdigit():
            assigned = int(assigned)
        if assigned is not None and not self.catalog.exists("department", assigned):
            raise ValidationFailedError("Bộ phận phụ trách không tồn tại.")

        return {
            "code": code,
            "title": title,
            "incident_type": data["incident_type"],
            "source_object_type": source_type,
            "source_object_id": source_id,
            "start_time": _dt(data.get("start_time")),
            "end_time": _dt(data.get("end_time")),
            "severity": severity,
            "description": (data.get("description") or "").strip() or None,
            "status": status,
            "assigned_department_id": assigned,
            "request_id": request_id,
            "is_simulated": bool(data.get("is_simulated", False)),
        }

    def create(self, data):
        cleaned = self._clean(data)
        existing = self.repository.get_by_request_id(cleaned["request_id"])
        if existing is not None:
            return existing, False
        try:
            row = self.repository.create(cleaned)
        except DuplicateCodeError:
            existing = self.repository.get_by_request_id(cleaned["request_id"])
            if existing is not None:
                return existing, False
            raise
        return row, True

    def update(self, incident_id, data):
        if self.repository.get(incident_id) is None:
            raise NotFoundError("Sự cố không tồn tại.")
        # Chỉ cho phép cập nhật một số trường, không đổi code/request_id.
        allowed = {}
        mapping = {
            "title": "str", "incident_type": "enum_type", "source_object_type": "str",
            "source_object_id": "int", "start_time": "dt", "end_time": "dt",
            "severity": "enum_sev", "status": "enum_status", "description": "str",
            "assigned_department_id": "int",
        }
        for field, ftype in mapping.items():
            if field not in data:
                continue
            value = data[field]
            if field == "incident_type" and value not in INCIDENT_TYPES:
                raise ValidationFailedError(f"incident_type phải thuộc {sorted(INCIDENT_TYPES)}.")
            if field == "severity" and value not in SEVERITIES:
                raise ValidationFailedError(f"severity phải thuộc {sorted(SEVERITIES)}.")
            if field == "status" and value not in STATUSES:
                raise ValidationFailedError(f"status phải thuộc {sorted(STATUSES)}.")
            if ftype == "dt":
                value = _dt(value)
            elif ftype == "int":
                if isinstance(value, str) and value.isdigit():
                    value = int(value)
                if isinstance(value, bool) or not isinstance(value, int):
                    raise ValidationFailedError(f"{field} phải là số nguyên.")
            elif ftype == "str" and value is not None:
                value = value.strip() or None
            allowed[field] = value
        if "assigned_department_id" in allowed and allowed["assigned_department_id"] is not None:
            if not self.catalog.exists("department", allowed["assigned_department_id"]):
                raise ValidationFailedError("Bộ phận phụ trách không tồn tại.")
        return self.repository.update(incident_id, allowed)

    def list(self, page, page_size, status, incident_type, search):
        return self.repository.list(page, page_size, status, incident_type, search)

    def get(self, incident_id):
        return self.repository.get(incident_id)

    # causes
    def create_cause(self, incident_id, data):
        if self.repository.get(incident_id) is None:
            raise NotFoundError("Sự cố không tồn tại.")
        content = (data.get("content") or "").strip()
        if not content:
            raise ValidationFailedError("content là bắt buộc.")
        kind = data.get("kind", "HYPOTHESIS")
        if kind not in CAUSE_KINDS:
            raise ValidationFailedError(f"kind phải thuộc {sorted(CAUSE_KINDS)}.")
        return self.repository.create_cause({
            "incident_id": incident_id,
            "content": content,
            "kind": kind,
            "evidence": (data.get("evidence") or "").strip() or None,
            "rule_id": (data.get("rule_id") or "").strip() or None,
            "priority": (data.get("priority") or "").strip() or None,
            "confirmed_by": (data.get("confirmed_by") or "").strip() or None,
            "confirmed_at": _dt(data.get("confirmed_at")),
        })

    def list_causes(self, incident_id):
        return self.repository.list_causes(incident_id)

    def update_cause(self, cause_id, data):
        return self.repository.update_cause(cause_id, data)

    def delete_cause(self, cause_id):
        return self.repository.delete_cause(cause_id)

    # links
    def create_link(self, incident_id, data):
        if self.repository.get(incident_id) is None:
            raise NotFoundError("Sự cố không tồn tại.")
        source_type = (data.get("source_type") or "").strip()
        if source_type not in LINK_TYPES:
            raise ValidationFailedError(f"source_type phải thuộc {sorted(LINK_TYPES)}.")
        source_id = data.get("source_id")
        if isinstance(source_id, bool) or not isinstance(source_id, int) or source_id <= 0:
            raise ValidationFailedError("source_id phải là số nguyên dương.")
        return self.repository.create_link({
            "incident_id": incident_id, "source_type": source_type, "source_id": source_id,
        })

    def list_links(self, incident_id):
        return self.repository.list_links(incident_id)

    def delete_link(self, link_id):
        return self.repository.delete_link(link_id)
