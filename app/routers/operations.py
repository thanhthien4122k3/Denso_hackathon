"""API ghi nhận vận hành (trạng thái máy, dừng máy, QC, vật tư)."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.services.operations_service import OperationsService
from app.settings import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

router = APIRouter(prefix="/api/operations", tags=["operations"])


def get_service() -> OperationsService:
    return OperationsService()


def _page(page, page_size, total):
    return {"page": page, "page_size": page_size, "total": total,
            "total_pages": (total + page_size - 1) // page_size}


def _parse_time(value):
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@router.get("/machine-states")
def list_states(page: int = Query(1, ge=1),     page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
                machine_id: int | None = Query(None), from_time: str | None = Query(None),
                to_time: str | None = Query(None), service: OperationsService = Depends(get_service)):
    rows, total = service.list_states(page, page_size, machine_id, _parse_time(from_time), _parse_time(to_time))
    return {"success": True, "message": "OK", "data": {"items": rows, "pagination": _page(page, page_size, total)}}


@router.post("/machine-states", status_code=201)
def create_state(payload: dict, service: OperationsService = Depends(get_service)):
    return {"success": True, "message": "Đã ghi nhận.", "data": service.create_state(payload)}


@router.get("/downtimes")
def list_downtimes(page: int = Query(1, ge=1),     page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
                   machine_id: int | None = Query(None), from_time: str | None = Query(None),
                   to_time: str | None = Query(None), service: OperationsService = Depends(get_service)):
    rows, total = service.list_downtimes(page, page_size, machine_id, _parse_time(from_time), _parse_time(to_time))
    return {"success": True, "message": "OK", "data": {"items": rows, "pagination": _page(page, page_size, total)}}


@router.post("/downtimes", status_code=201)
def create_downtime(payload: dict, service: OperationsService = Depends(get_service)):
    return {"success": True, "message": "Đã ghi nhận.", "data": service.create_downtime(payload)}


@router.post("/report-machine-error", status_code=201)
def report_machine_error(payload: dict, service: OperationsService = Depends(get_service)):
    return {"success": True, "message": "Đã ghi nhận sự cố máy.",
            "data": service.report_machine_error(payload)}


@router.post("/downtimes/{downtime_id}/close")
def close_downtime(downtime_id: int, payload: dict, service: OperationsService = Depends(get_service)):
    return {"success": True, "message": "Đã đóng.", "data": service.close_downtime(downtime_id, payload.get("end_time"))}


@router.get("/qc")
def list_qc(page: int = Query(1, ge=1),     page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
            lot_id: int | None = Query(None), result: str | None = Query(None),
            service: OperationsService = Depends(get_service)):
    rows, total = service.list_qc(page, page_size, lot_id, result)
    return {"success": True, "message": "OK", "data": {"items": rows, "pagination": _page(page, page_size, total)}}


@router.post("/qc", status_code=201)
def create_qc(payload: dict, service: OperationsService = Depends(get_service)):
    return {"success": True, "message": "Đã ghi nhận.", "data": service.create_qc(payload)}


@router.get("/material")
def list_material(page: int = Query(1, ge=1),     page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
                  material_id: int | None = Query(None),
                  service: OperationsService = Depends(get_service)):
    rows, total = service.list_material(page, page_size, material_id)
    return {"success": True, "message": "OK", "data": {"items": rows, "pagination": _page(page, page_size, total)}}


@router.post("/material", status_code=201)
def create_material(payload: dict, service: OperationsService = Depends(get_service)):
    return {"success": True, "message": "Đã ghi nhận.", "data": service.create_material(payload)}
