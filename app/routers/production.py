"""API nhập và xem báo cáo sản xuất."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi import status

from app.settings import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

from app.schemas import (
    CreateResponse,
    DetailResponse,
    ListData,
    ListResponse,
    PaginationMeta,
    ProductionRecordCreate,
    RecordData,
)
from app.services.production_service import ProductionService

router = APIRouter(prefix="/api/production-records", tags=["production-records"])


def get_service() -> ProductionService:
    return ProductionService()


@router.post(
    "",
    response_model=CreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ghi nhận sản lượng công đoạn",
)
def create_record(
    payload: ProductionRecordCreate,
    response: Response,
    service: ProductionService = Depends(get_service),
):
    result = service.create_record(payload)

    if not result.created:
        response.status_code = status.HTTP_200_OK

    message = (
        "Đã lưu bản ghi mới."
        if result.created
        else "Bản ghi đã tồn tại (cùng request_id), trả về bản ghi cũ."
    )
    return CreateResponse(
        success=True,
        message=message,
        data=RecordData(**result.record),
    )


@router.get("", response_model=ListResponse, summary="Danh sách báo cáo sản xuất")
def list_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    line_code: str | None = Query(None, max_length=50),
    lot_code: str | None = Query(None, max_length=100),
    service: ProductionService = Depends(get_service),
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date_from phải nhỏ hơn hoặc bằng date_to.",
        )

    items, total = service.list_records(
        date_from=date_from,
        date_to=date_to,
        line_code=line_code,
        lot_code=lot_code,
        page=page,
        page_size=page_size,
    )
    total_pages = (total + page_size - 1) // page_size

    return ListResponse(
        success=True,
        message="OK",
        data=ListData(
            items=[RecordData(**item) for item in items],
            pagination=PaginationMeta(
                page=page,
                page_size=page_size,
                total=total,
                total_pages=total_pages,
            ),
        ),
    )


@router.get("/{record_id}", response_model=DetailResponse, summary="Chi tiết bản ghi")
def get_record(
    record_id: int,
    service: ProductionService = Depends(get_service),
):
    record = service.get_record(record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy bản ghi.",
        )
    return DetailResponse(
        success=True,
        message="OK",
        data=RecordData(**record),
    )
