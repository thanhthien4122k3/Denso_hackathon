"""Nghiệp vụ tích hợp nguồn ngoài: profile, test, khám phá, preview, batch nhập."""

from __future__ import annotations

import threading
import time
import uuid
from datetime import date, datetime
from uuid import UUID

from app.exceptions import NotFoundError, ValidationFailedError
from app.integration import crypto
from app.integration.connectors import (
    PREVIEW_LIMIT,
    SUPPORTED_DB_TYPES,
    SourceConnectionError,
    build_connector,
    sanitize_error,
)
from app.integration.files import MAX_ROWS, FileParseError, parse_preview, read_rows
from app.repositories.integration_repository import IntegrationRepository
from app.repositories.system_repository import SystemRepository
from app.schemas import ProductionRecordCreate
from app.services.production_service import ProductionService

_BATCH_STATUSES = {"PENDING", "VALID", "INVALID", "FAILED", "IMPORTED", "PARTIAL"}

# Mục tiêu nhập nghiệp vụ được hỗ trợ (ánh xạ cột nguồn -> trường đích).
TARGETS = {
    "production_records": {
        "label": "Sản lượng",
        "identity": ["production_date", "shift", "line_code", "process_code", "lot_code"],
        "fields": {
            "production_date": {"label": "Ngày sản xuất", "required": True, "type": "date"},
            "shift": {"label": "Ca sản xuất", "required": True, "type": "enum",
                      "values": ["CA_1", "CA_2", "CA_3"]},
            "line_code": {"label": "Mã chuyền", "required": True},
            "process_code": {"label": "Mã công đoạn", "required": True},
            "product_code": {"label": "Mã sản phẩm", "required": True},
            "lot_code": {"label": "Mã lot", "required": True},
            "good_quantity": {"label": "Số lượng đạt", "required": True, "type": "int"},
            "defect_quantity": {"label": "Số lượng lỗi", "required": True, "type": "int"},
            "operator_name": {"label": "Người nhập", "required": True},
            "note": {"label": "Ghi chú", "required": False},
        },
    },
}

_NAMESPACE = uuid.UUID("4b8f9c2e-1d3a-4f6e-9b7a-2c5e8f0a6d11")

# Bộ nhớ tạm cho file tải lên (bytes), dùng token ngắn hạn.
_upload_cache: dict[str, tuple[bytes, float, str]] = {}
_upload_lock = threading.Lock()
_UPLOAD_TTL = 1800  # 30 phút


def _cache_put(raw: bytes, filename: str) -> str:
    token = uuid.uuid4().hex
    with _upload_lock:
        _upload_cache[token] = (raw, time.time(), filename)
        now = time.time()
        for k in [k for k, v in _upload_cache.items() if now - v[1] > _UPLOAD_TTL]:
            _upload_cache.pop(k, None)
    return token


def _cache_get(token: str) -> tuple[bytes, str]:
    with _upload_lock:
        item = _upload_cache.get(token)
        if item is None or time.time() - item[1] > _UPLOAD_TTL:
            raise ValidationFailedError("Phiên tải file đã hết hạn. Vui lòng tải lại file.")
        return item[0], item[2]


class IntegrationService:
    def __init__(self, repository: IntegrationRepository | None = None):
        self.repository = repository or IntegrationRepository()
        self.system = SystemRepository()

    # ---- connection profiles ----
    def list_profiles(self, page, page_size):
        return self.repository.list_profiles(page, page_size)

    def get_profile(self, profile_id):
        profile = self.repository.get_profile(profile_id)
        if profile is None:
            raise NotFoundError("Cấu hình kết nối không tồn tại.")
        return profile

    def create_profile(self, data):
        cleaned = self._clean_profile(data, partial=False)
        row = self.repository.create_profile(cleaned)
        return self.repository.get_profile(row["id"])

    def update_profile(self, profile_id, data):
        if self.repository.get_profile(profile_id) is None:
            raise NotFoundError("Cấu hình kết nối không tồn tại.")
        cleaned = self._clean_profile(data, partial=True)
        self.repository.update_profile(profile_id, cleaned)
        return self.repository.get_profile(profile_id)

    def delete_profile(self, profile_id):
        if self.repository.get_profile(profile_id) is None:
            raise NotFoundError("Cấu hình kết nối không tồn tại.")
        return self.repository.delete_profile(profile_id)

    def _clean_profile(self, data, partial):
        if not isinstance(data, dict):
            raise ValidationFailedError("Dữ liệu phải là đối tượng JSON.")
        cleaned = {}
        if "db_type" in data:
            if data["db_type"] not in SUPPORTED_DB_TYPES:
                raise ValidationFailedError(
                    f"db_type phải thuộc {sorted(SUPPORTED_DB_TYPES)}.")
            cleaned["db_type"] = data["db_type"]
        if "host" in data:
            host = (data["host"] or "").strip()
            if not host:
                raise ValidationFailedError("host là bắt buộc.")
            cleaned["host"] = host
        if "port" in data:
            port = data["port"]
            if port is not None and (isinstance(port, bool) or not isinstance(port, int)
                                     or not 1 <= port <= 65535):
                raise ValidationFailedError("port phải là số nguyên 1-65535.")
            cleaned["port"] = port
        if "database_name" in data:
            cleaned["database_name"] = (data["database_name"] or "").strip() or None
        if "username" in data:
            cleaned["username"] = (data["username"] or "").strip() or None
        if "source_id" in data:
            cleaned["source_id"] = data["source_id"] or None
        if "ssl_mode" in data:
            cleaned["ssl_mode"] = (data["ssl_mode"] or "").strip() or None
        if "extra_options" in data:
            opts = data["extra_options"]
            if opts is not None and not isinstance(opts, dict):
                raise ValidationFailedError("extra_options phải là đối tượng JSON.")
            cleaned["extra_options"] = opts or None

        if "password" in data and data["password"] not in (None, ""):
            if not crypto.encryption_available():
                raise ValidationFailedError(
                    "Chưa cấu hình SOURCE_ENCRYPTION_KEY; không thể lưu mật khẩu nguồn.")
            cleaned["password_encrypted"] = crypto.encrypt_secret(data["password"])

        if not partial:
            for required in ("db_type", "host"):
                if required not in cleaned:
                    raise ValidationFailedError(f"{required} là bắt buộc.")
        return cleaned

    def _connect(self, profile_id):
        row = self.repository.get_profile_with_secret(profile_id)
        if row is None:
            raise NotFoundError("Cấu hình kết nối không tồn tại.")
        password = None
        if row.get("password_encrypted"):
            try:
                password = crypto.decrypt_secret(row["password_encrypted"])
            except RuntimeError as exc:
                raise ValidationFailedError(str(exc)) from exc
        return build_connector(
            db_type=row["db_type"], host=row["host"], port=row["port"],
            database=row["database_name"], username=row["username"],
            password=password, ssl_mode=row.get("ssl_mode"),
            options=row.get("extra_options") or {})

    def test_connection(self, profile_id):
        try:
            connector = self._connect(profile_id)
            result = connector.test()
            self.repository.update_profile(profile_id, {
                "last_status": "OK", "last_checked_at": datetime.now(),
                "last_error": None})
            return result
        except SourceConnectionError as exc:
            self.repository.update_profile(profile_id, {
                "last_status": "FAILED", "last_checked_at": datetime.now(),
                "last_error": sanitize_error(exc)})
            raise ValidationFailedError(str(exc)) from exc

    def list_schemas(self, profile_id):
        return self._connect(profile_id).schemas()

    def list_tables(self, profile_id, schema):
        return self._connect(profile_id).tables(schema)

    def list_columns(self, profile_id, schema, table):
        return self._connect(profile_id).columns(schema, table)

    def preview_table(self, profile_id, schema, table, columns=None, limit=PREVIEW_LIMIT):
        return self._connect(profile_id).preview(schema, table, columns, limit)

    # ---- file upload ----
    def upload_file(self, filename: str, raw: bytes, sheet: str | None = None) -> dict:
        preview = parse_preview(filename, raw, sheet=sheet)
        token = _cache_put(raw, filename)
        preview["token"] = token
        return preview

    # ---- batch ----
    def create_file_batch(self, token, target_type, mapping, sheet=None,
                          source_id=None, dataset_id=None, created_by=None):
        raw, filename = _cache_get(token)
        header, rows, fmt = read_rows(filename, raw, sheet)
        return self._create_batch(
            input_type=fmt, source_name=filename,
            target_type=target_type, mapping=mapping,
            header=header, rows=rows,
            source_id=source_id, dataset_id=dataset_id, created_by=created_by)

    def create_table_batch(self, profile_id, schema, table, target_type, mapping,
                           source_id=None, dataset_id=None, created_by=None,
                           columns=None):
        data = self.preview_table(profile_id, schema, table, columns, limit=MAX_ROWS)
        header = data["columns"]
        rows = data["rows"]
        return self._create_batch(
            input_type="database", source_name=f"{schema}.{table}",
            target_type=target_type, mapping=mapping,
            header=header, rows=rows, connection_id=profile_id,
            source_id=source_id, dataset_id=dataset_id, created_by=created_by)

    def _create_batch(self, input_type, source_name, target_type, mapping, header, rows,
                      source_id=None, connection_id=None, dataset_id=None, created_by=None):
        if target_type not in TARGETS:
            raise ValidationFailedError(f"Loại dữ liệu đích không được hỗ trợ: {target_type}.")
        if not isinstance(mapping, dict) or not mapping:
            raise ValidationFailedError("mapping là bắt buộc (cột nguồn -> trường đích).")
        spec = TARGETS[target_type]["fields"]
        header_set = set(header)
        for field, meta in spec.items():
            if meta["required"] and not mapping.get(field):
                raise ValidationFailedError(
                    f"Thiếu ánh xạ cho trường bắt buộc '{meta['label']}' ({field}).")
        for field, src in mapping.items():
            if not src:
                continue
            if field not in spec:
                raise ValidationFailedError(f"Trường đích không hợp lệ: {field}.")
            if src not in header_set:
                raise ValidationFailedError(f"Cột nguồn không tồn tại: {src}.")

        idx = {h: i for i, h in enumerate(header)}
        identity = TARGETS[target_type].get("identity", [])
        valid_rows = []
        error_rows = []
        seen = {}
        for row in rows:
            payload = {field: (row[idx[mapping[field]]] if mapping.get(field) else None)
                       for field in spec}
            ok, value = self._validate_payload(payload, spec)
            if not ok:
                error_rows.append({"row": row, "error": value})
                continue
            key = tuple(value[f] for f in identity if f in value)
            if key in seen:
                seen[key] += 1
                error_rows.append({"row": row, "error": "Trùng bản ghi trong batch."})
                continue
            seen[key] = 1
            valid_rows.append(value)

        total = len(rows)
        status = "VALID" if valid_rows else "INVALID"
        batch = self.repository.create_batch({
            "source_id": source_id, "connection_id": connection_id, "dataset_id": dataset_id,
            "input_type": input_type, "source_name": source_name,
            "target_type": target_type, "created_by": created_by,
            "total_rows": total, "valid_rows": len(valid_rows),
            "error_rows": len(error_rows), "duplicate_rows": 0,
            "imported_rows": 0, "status": status,
            "mapping": mapping, "rows": valid_rows,
            "error_summary": error_rows[:100],
        })
        return batch

    def _validate_payload(self, payload, spec):
        out = {}
        for field, meta in spec.items():
            raw = payload.get(field)
            if raw is None or (isinstance(raw, str) and raw.strip() == ""):
                if meta["required"]:
                    return False, f"Thiếu giá trị trường '{meta['label']}'."
                out[field] = None
                continue
            if isinstance(raw, str):
                raw = raw.strip()
            if meta.get("type") == "int":
                try:
                    value = int(raw)
                except (TypeError, ValueError):
                    return False, f"Trường '{meta['label']}' phải là số nguyên."
                if value < 0:
                    return False, f"Trường '{meta['label']}' không được âm."
                out[field] = value
            elif meta.get("type") == "date":
                if isinstance(raw, date):
                    out[field] = raw
                else:
                    try:
                        out[field] = date.fromisoformat(str(raw))
                    except ValueError:
                        return False, f"Trường '{meta['label']}' phải là ngày (YYYY-MM-DD)."
            elif meta.get("type") == "enum":
                if raw not in meta["values"]:
                    return False, f"Trường '{meta['label']}' phải thuộc {meta['values']}."
                out[field] = raw
            else:
                out[field] = str(raw)
        return True, out

    def list_batches(self, page, page_size):
        return self.repository.list_batches(page, page_size)

    def get_batch(self, batch_id):
        batch = self.repository.get_batch(batch_id)
        if batch is None:
            raise NotFoundError("Batch nhập không tồn tại.")
        return batch

    def confirm_batch(self, batch_id, username=None):
        batch = self.repository.get_batch(batch_id)
        if batch is None:
            raise NotFoundError("Batch nhập không tồn tại.")
        if batch["target_type"] != "production_records":
            raise ValidationFailedError(
                "Loại dữ liệu này chưa có luồng ghi nghiệp vụ; chỉ hỗ trợ Sản lượng.")
        if batch["status"] not in ("VALID", "PARTIAL", "IMPORTED"):
            raise ValidationFailedError("Batch chưa đủ điều kiện để nhập (chưa hợp lệ).")

        rows = batch.get("rows") or []
        service = ProductionService()
        imported = 0
        duplicates = 0
        errors = []
        created_ids = []
        for i, payload in enumerate(rows):
            request_id = uuid.uuid5(_NAMESPACE, f"batch-{batch_id}-row-{i}")
            try:
                result = service.create_record(ProductionRecordCreate(
                    request_id=UUID(str(request_id)),
                    production_date=payload["production_date"],
                    shift=payload["shift"],
                    line_code=payload["line_code"],
                    process_code=payload["process_code"],
                    product_code=payload["product_code"],
                    lot_code=payload["lot_code"],
                    good_quantity=payload["good_quantity"],
                    defect_quantity=payload["defect_quantity"],
                    operator_name=payload["operator_name"],
                    note=payload.get("note"),
                ))
                created_ids.append(result.record["id"])
                if result.created:
                    imported += 1
                else:
                    duplicates += 1
            except Exception as exc:  # noqa: BLE001
                errors.append({"row": payload, "error": sanitize_error(str(exc))})

        status = "IMPORTED" if not errors else "PARTIAL"
        self.repository.update_batch(batch_id, {
            "status": status, "imported_rows": imported,
            "duplicate_rows": duplicates,
            "error_summary": errors[:100],
            "created_business_ids": created_ids,
        })
        return self.repository.get_batch(batch_id)
