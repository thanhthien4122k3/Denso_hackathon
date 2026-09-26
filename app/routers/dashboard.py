"""API tổng quan."""

from datetime import date

from fastapi import APIRouter, Depends, Query

from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def get_service() -> DashboardService:
    return DashboardService()


@router.get("")
def summary(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    simulated: bool | None = Query(None),
    service: DashboardService = Depends(get_service),
):
    return {"success": True, "message": "OK",
            "data": service.summary(date_from=date_from, date_to=date_to, simulated=simulated)}
