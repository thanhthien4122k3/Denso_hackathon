"""Nghiệp vụ ghi nhận sản lượng.

Backend tự tính tổng sản lượng và tỷ lệ lỗi, không tin giá trị do frontend gửi.
"""

from dataclasses import dataclass

from app.exceptions import DuplicateRequestError, RecordConflictError
from app.repositories.production_repository import ProductionRepository
from app.schemas import ProductionRecordCreate

_BUSINESS_FIELDS = (
    "production_date",
    "shift",
    "line_code",
    "process_code",
    "product_code",
    "lot_code",
    "good_quantity",
    "defect_quantity",
    "operator_name",
    "note",
)


@dataclass
class CreateResult:
    created: bool
    record: dict


class ProductionService:
    def __init__(self, repository: ProductionRepository | None = None):
        self.repository = repository or ProductionRepository()

    def _to_params(self, data: ProductionRecordCreate) -> dict:
        return {
            "request_id": data.request_id,
            "production_date": data.production_date,
            "shift": data.shift,
            "line_code": data.line_code,
            "process_code": data.process_code,
            "product_code": data.product_code,
            "lot_code": data.lot_code,
            "good_quantity": data.good_quantity,
            "defect_quantity": data.defect_quantity,
            "operator_name": data.operator_name,
            "note": data.note,
        }

    @staticmethod
    def format_record(row: dict) -> dict:
        total = row["good_quantity"] + row["defect_quantity"]
        rate = 0.0 if total == 0 else round(row["defect_quantity"] / total * 100, 2)
        return {**row, "total_quantity": total, "defect_rate": rate}

    @staticmethod
    def _matches(existing: dict, incoming: dict) -> bool:
        return all(existing.get(f) == incoming.get(f) for f in _BUSINESS_FIELDS)

    def create_record(self, data: ProductionRecordCreate) -> CreateResult:
        params = self._to_params(data)

        existing = self.repository.find_by_request_id(data.request_id)
        if existing is not None:
            if self._matches(existing, params):
                return CreateResult(created=False, record=self.format_record(existing))
            raise RecordConflictError()

        try:
            row = self.repository.insert(params)
        except DuplicateRequestError:
            existing = self.repository.find_by_request_id(data.request_id)
            if existing is not None and self._matches(existing, params):
                return CreateResult(created=False, record=self.format_record(existing))
            raise RecordConflictError()

        return CreateResult(created=True, record=self.format_record(row))

    def get_record(self, record_id: int) -> dict | None:
        row = self.repository.find_by_id(record_id)
        return self.format_record(row) if row else None

    def list_records(
        self,
        date_from=None,
        date_to=None,
        line_code=None,
        lot_code=None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        line_code = line_code.strip() if line_code else None
        lot_code = lot_code.strip() if lot_code else None
        offset = (page - 1) * page_size

        rows = self.repository.list_records(
            date_from=date_from,
            date_to=date_to,
            line_code=line_code,
            lot_code=lot_code,
            limit=page_size,
            offset=offset,
        )
        total = self.repository.count_records(
            date_from=date_from,
            date_to=date_to,
            line_code=line_code,
            lot_code=lot_code,
        )
        return [self.format_record(r) for r in rows], total

    def health_check(self) -> bool:
        return self.repository.health_check()
