"""API phân tích tác động & nguyên nhân, lưu vết kết quả."""

from fastapi import APIRouter, Depends, Query

from app.exceptions import ValidationFailedError
from app.services.analysis_service import AnalysisService
from app.settings import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

MAX_DEPTH_LIMIT = 20


def get_service() -> AnalysisService:
    return AnalysisService()


def _require_int(payload: dict, key: str, positive: bool = True) -> int | None:
    value = payload.get(key)
    if value is None:
        raise ValidationFailedError(f"{key} là bắt buộc.")
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationFailedError(f"{key} phải là số nguyên.")
    if positive and value <= 0:
        raise ValidationFailedError(f"{key} phải là số nguyên dương.")
    return value


def _require_number(payload: dict, key: str, non_negative: bool = True) -> float | None:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationFailedError(f"{key} phải là số.")
    if non_negative and value < 0:
        raise ValidationFailedError(f"{key} không được âm.")
    return float(value)


def _max_depth(payload: dict) -> int:
    value = payload.get("max_depth", 3)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationFailedError("max_depth phải là số nguyên.")
    if not 1 <= value <= MAX_DEPTH_LIMIT:
        raise ValidationFailedError(f"max_depth phải nằm trong khoảng 1-{MAX_DEPTH_LIMIT}.")
    return value


@router.post("/run")
def run_for_incident(payload: dict, service: AnalysisService = Depends(get_service)):
    if not isinstance(payload, dict):
        raise ValidationFailedError("Dữ liệu phải là đối tượng JSON.")
    return {
        "success": True, "message": "OK",
        "data": service.run_for_incident(
            incident_id=_require_int(payload, "incident_id"),
            max_depth=_max_depth(payload),
            duration_minutes=_require_number(payload, "duration_minutes"),
            rate_per_minute=_require_number(payload, "rate_per_minute"),
            assumptions=payload.get("assumptions"),
        ),
    }


@router.post("/whatif")
def run_whatif(payload: dict, service: AnalysisService = Depends(get_service)):
    if not isinstance(payload, dict):
        raise ValidationFailedError("Dữ liệu phải là đối tượng JSON.")
    incident_type = payload.get("incident_type")
    source_type = payload.get("source_type")
    if not incident_type or not source_type:
        raise ValidationFailedError("incident_type và source_type là bắt buộc.")
    return {
        "success": True, "message": "OK",
        "data": service.run_whatif(
            incident_type=incident_type,
            source_type=source_type,
            source_id=_require_int(payload, "source_id"),
            max_depth=_max_depth(payload),
            duration_minutes=_require_number(payload, "duration_minutes"),
            rate_per_minute=_require_number(payload, "rate_per_minute"),
            assumptions=payload.get("assumptions"),
            at_time=payload.get("at_time"),
        ),
    }


@router.get("/runs")
def list_runs(page: int = Query(1, ge=1), page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
              source_type: str | None = Query(None), source_id: int | None = Query(None),
              service: AnalysisService = Depends(get_service)):
    rows, total = service.list_runs(page, page_size, source_type, source_id)
    return {"success": True, "message": "OK", "data": {"items": rows, "pagination": {
        "page": page, "page_size": page_size, "total": total,
        "total_pages": (total + page_size - 1) // page_size}}}


@router.get("/runs/{run_id}")
def get_run(run_id: int, service: AnalysisService = Depends(get_service)):
    return {"success": True, "message": "OK", "data": service.get_run(run_id)}


@router.get("/action-matrix")
def action_matrix(simulated: bool = Query(False), service: AnalysisService = Depends(get_service)):
    return {"success": True, "message": "OK", "data": service.action_matrix(simulated)}
