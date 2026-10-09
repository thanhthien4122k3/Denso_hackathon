"""Nghiệp vụ công việc theo bộ phận."""

from app.exceptions import NotFoundError, ValidationFailedError
from app.repositories.catalog_repository import CatalogRepository
from app.repositories.task_repository import TaskRepository

STATUSES = {"TODO", "IN_PROGRESS", "DONE", "DISMISSED"}


class TaskService:
    def __init__(self, repository: TaskRepository | None = None):
        self.repository = repository or TaskRepository()
        self.catalog = CatalogRepository()

    def _clean(self, data, partial=False):
        if not isinstance(data, dict):
            raise ValidationFailedError("Dữ liệu phải là đối tượng JSON.")
        cleaned = {}
        for name, value in data.items():
            if name in ("title", "description", "priority"):
                if value is None or value == "":
                    if name == "title" and not partial:
                        raise ValidationFailedError("title là bắt buộc.")
                    continue
                if not isinstance(value, str):
                    raise ValidationFailedError(f"{name} phải là chuỗi.")
                cleaned[name] = value.strip()
            elif name == "status":
                if value not in STATUSES:
                    raise ValidationFailedError(f"status phải thuộc {sorted(STATUSES)}.")
                cleaned[name] = value
            elif name in ("department_id", "source_incident_id", "source_analysis_run_id"):
                if value is None:
                    continue
                if isinstance(value, str) and value.isdigit():
                    value = int(value)
                if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                    raise ValidationFailedError(f"{name} phải là số nguyên dương.")
                cleaned[name] = value
            elif name == "rule_id":
                cleaned[name] = (value or "").strip() or None
            elif name == "is_simulated":
                cleaned[name] = bool(value)
        if "title" in data and not cleaned.get("title") and not partial:
            raise ValidationFailedError("title là bắt buộc.")
        return cleaned

    def create(self, data):
        cleaned = self._clean(data, partial=False)
        if not cleaned.get("title"):
            raise ValidationFailedError("title là bắt buộc.")
        if cleaned.get("department_id") and not self.catalog.exists("department", cleaned["department_id"]):
            raise ValidationFailedError("Bộ phận không tồn tại.")
        cleaned.setdefault("status", "TODO")
        cleaned.setdefault("is_simulated", False)
        return self.repository.create(cleaned)

    def update(self, task_id, data):
        if self.repository.get(task_id) is None:
            raise NotFoundError("Công việc không tồn tại.")
        cleaned = self._clean(data, partial=True)
        return self.repository.update(task_id, cleaned)

    def set_status(self, task_id, status):
        if status not in STATUSES:
            raise ValidationFailedError(f"status phải thuộc {sorted(STATUSES)}.")
        if self.repository.get(task_id) is None:
            raise NotFoundError("Công việc không tồn tại.")
        return self.repository.update_status(task_id, status)

    def list(self, page, page_size, department_id, status):
        return self.repository.list(page, page_size, department_id, status)

    def get(self, task_id):
        return self.repository.get(task_id)
