"""Kiểm tra sức khỏe ứng dụng và kết nối database."""

from fastapi import APIRouter, Depends

from app.schemas import HealthResponse
from app.services.production_service import ProductionService

router = APIRouter(tags=["health"])


def get_service() -> ProductionService:
    return ProductionService()


@router.get("/api/health", response_model=HealthResponse, summary="Kiểm tra sức khỏe")
def health(service: ProductionService = Depends(get_service)):
    service.health_check()
    return HealthResponse(status="ok", database="up")
