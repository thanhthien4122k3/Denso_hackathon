"""API tổng quan."""

from fastapi import APIRouter, Depends

from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def get_service() -> DashboardService:
    return DashboardService()


@router.get("")
def summary(service: DashboardService = Depends(get_service)):
    return {"success": True, "message": "OK", "data": service.summary()}
