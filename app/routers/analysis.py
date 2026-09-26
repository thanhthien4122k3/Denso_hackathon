"""API phân tích tác động & nguyên nhân, lưu vết kết quả."""

from fastapi import APIRouter, Depends, Query

from app.services.analysis_service import AnalysisService

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


def get_service() -> AnalysisService:
    return AnalysisService()


@router.post("/run")
def run_for_incident(payload: dict, service: AnalysisService = Depends(get_service)):
    return {
        "success": True, "message": "OK",
        "data": service.run_for_incident(
            incident_id=payload["incident_id"],
            max_depth=payload.get("max_depth", 3),
            duration_minutes=payload.get("duration_minutes"),
            rate_per_minute=payload.get("rate_per_minute"),
            assumptions=payload.get("assumptions"),
        ),
    }


@router.post("/whatif")
def run_whatif(payload: dict, service: AnalysisService = Depends(get_service)):
    return {
        "success": True, "message": "OK",
        "data": service.run_whatif(
            incident_type=payload["incident_type"],
            source_type=payload["source_type"],
            source_id=payload.get("source_id"),
            max_depth=payload.get("max_depth", 3),
            duration_minutes=payload.get("duration_minutes"),
            rate_per_minute=payload.get("rate_per_minute"),
            assumptions=payload.get("assumptions"),
        ),
    }


@router.get("/runs")
def list_runs(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
              source_type: str | None = Query(None),
              service: AnalysisService = Depends(get_service)):
    rows, total = service.list_runs(page, page_size, source_type)
    return {"success": True, "message": "OK", "data": {"items": rows, "pagination": {
        "page": page, "page_size": page_size, "total": total,
        "total_pages": (total + page_size - 1) // page_size}}}


@router.get("/runs/{run_id}")
def get_run(run_id: int, service: AnalysisService = Depends(get_service)):
    return {"success": True, "message": "OK", "data": service.get_run(run_id)}
