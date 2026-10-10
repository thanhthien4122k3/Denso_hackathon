"""Pydantic models cho request/response.

Backend là nơi quyết định cuối cùng về tính hợp lệ dữ liệu:
- Trim chuỗi, cấm chuỗi bắt buộc chỉ chứa khoảng trắng.
- Số lượng là số nguyên >= 0, không chấp nhận số âm, số thập phân hay boolean.
- Tổng (đạt + lỗi) phải lớn hơn 0.
"""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator

from app.settings import MAX_QUANTITY

Shift = Literal["CA_1", "CA_2", "CA_3"]


class ProductionRecordCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    request_id: UUID
    production_date: date
    shift: Shift
    line_code: str = Field(min_length=1, max_length=50)
    process_code: str = Field(min_length=1, max_length=50)
    product_code: str = Field(min_length=1, max_length=100)
    lot_code: str = Field(min_length=1, max_length=100)
    good_quantity: StrictInt = Field(ge=0, le=MAX_QUANTITY)
    defect_quantity: StrictInt = Field(ge=0, le=MAX_QUANTITY)
    operator_name: str = Field(min_length=1, max_length=100)
    note: str | None = Field(default=None, max_length=1000)

    @field_validator("note")
    @classmethod
    def _normalize_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @model_validator(mode="after")
    def _check_total_positive(self) -> "ProductionRecordCreate":
        if self.good_quantity + self.defect_quantity <= 0:
            raise ValueError("Tổng số lượng (đạt + lỗi) phải lớn hơn 0.")
        return self


class RecordData(BaseModel):
    id: int
    request_id: UUID
    production_date: date
    shift: str
    line_code: str
    process_code: str
    product_code: str
    lot_code: str
    good_quantity: int
    defect_quantity: int
    operator_name: str
    note: str | None
    total_quantity: int
    defect_rate: float
    created_at: datetime


class CreateResponse(BaseModel):
    success: bool
    message: str
    data: RecordData


class DetailResponse(BaseModel):
    success: bool
    message: str
    data: RecordData


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class ListData(BaseModel):
    items: list[RecordData]
    pagination: PaginationMeta


class ListResponse(BaseModel):
    success: bool
    message: str
    data: ListData


class HealthResponse(BaseModel):
    status: str
    database: str


# ---- Đồ thị (graph) ----
class GraphEdgeCreate(BaseModel):
    source_type: str
    source_id: int
    target_type: str
    target_id: int
    kind: str
    label: str | None = None
    description: str | None = None
    source_confirmation: str | None = None
    valid_from: str | None = None
    valid_to: str | None = None
    is_simulated: bool = False


class GraphEdgeUpdate(BaseModel):
    label: str | None = None
    description: str | None = None
    source_confirmation: str | None = None
    valid_from: str | None = None
    valid_to: str | None = None
    is_simulated: bool | None = None


# ---- Danh mục (catalog) ----
class CatalogUpsert(BaseModel):
    model_config = ConfigDict(extra="allow")
    code: str
    name: str


# ---- Vận hành (operations) ----
class MachineStateCreate(BaseModel):
    model_config = ConfigDict(extra="allow")
    machine_id: int
    event_time: str
    state: str


class DowntimeCreate(BaseModel):
    model_config = ConfigDict(extra="allow")
    machine_id: int
    start_time: str


class DowntimeClose(BaseModel):
    end_time: str | None = None


class ReportMachineError(BaseModel):
    model_config = ConfigDict(extra="allow")
    machine_id: int
    event_time: str


class QcCreate(BaseModel):
    model_config = ConfigDict(extra="allow")
    lot_id: int
    result: str


class MaterialCreate(BaseModel):
    model_config = ConfigDict(extra="allow")
    material_id: int
    available_qty: float
