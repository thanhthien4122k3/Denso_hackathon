"""Nghiệp vụ danh mục: kiểm tra dữ liệu, tham chiếu và CRUD chung."""

from app.catalog import all_fields, get_entity
from app.exceptions import ValidationFailedError
from app.repositories.catalog_repository import CatalogRepository


class CatalogService:
    def __init__(self, repository: CatalogRepository | None = None):
        self.repository = repository or CatalogRepository()

    def clean_payload(self, key: str, data, partial: bool = False) -> dict:
        spec = get_entity(key)
        fields = all_fields(spec)

        if not isinstance(data, dict):
            raise ValidationFailedError("Dữ liệu phải là đối tượng JSON.")

        cleaned: dict = {}
        for name, value in data.items():
            if name not in fields:
                raise ValidationFailedError(f"Trường không hợp lệ: {name}.")
            fs = fields[name]

            if value is None or value == "":
                if fs.required:
                    raise ValidationFailedError(f"{fs.label} là bắt buộc.")
                continue

            if fs.type == "str":
                if not isinstance(value, str):
                    raise ValidationFailedError(f"{fs.label} phải là chuỗi.")
                value = value.strip()
                if fs.required and not value:
                    raise ValidationFailedError(f"{fs.label} là bắt buộc.")
                if fs.max_length and len(value) > fs.max_length:
                    raise ValidationFailedError(f"{fs.label} tối đa {fs.max_length} ký tự.")
            elif fs.type == "int":
                if isinstance(value, bool) or not isinstance(value, int):
                    raise ValidationFailedError(f"{fs.label} phải là số nguyên.")
                if value <= 0:
                    raise ValidationFailedError(f"{fs.label} phải lớn hơn 0.")
            elif fs.type == "bool":
                if not isinstance(value, bool):
                    raise ValidationFailedError(f"{fs.label} phải là true/false.")

            cleaned[name] = value

        if not partial:
            for req in ("code", "name"):
                if req not in cleaned:
                    raise ValidationFailedError(f"{fields[req].label} là bắt buộc.")

        for fk_name, target_key in spec.fk.items():
            if fk_name in cleaned:
                if not self.repository.exists(target_key, cleaned[fk_name]):
                    raise ValidationFailedError(
                        f"Tham chiếu {fk_name}={cleaned[fk_name]} không tồn tại."
                    )
        return cleaned

    def list(self, key, page, page_size, search, active):
        return self.repository.list(key, page, page_size, search, active)

    def get(self, key, record_id):
        return self.repository.get(key, record_id)

    def create(self, key, data):
        cleaned = self.clean_payload(key, data, partial=False)
        return self.repository.create(key, cleaned)

    def update(self, key, record_id, data):
        existing = self.repository.get(key, record_id)
        if existing is None:
            return None
        data = {k: v for k, v in data.items() if k != "code"}
        cleaned = self.clean_payload(key, data, partial=True)
        return self.repository.update(key, record_id, cleaned)

    def deactivate(self, key, record_id):
        return self.repository.deactivate(key, record_id)
