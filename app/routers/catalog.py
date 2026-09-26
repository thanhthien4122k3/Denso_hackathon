"""API danh mục nghiệp vụ (CRUD chung cho 9 đối tượng)."""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.catalog import CATALOG_ENTITIES, CATALOG_KEYS
from app.services.catalog_service import CatalogService
from app.settings import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

router = APIRouter(prefix="/api/catalog", tags=["catalog"])


def get_service() -> CatalogService:
    return CatalogService()


@router.get("/keys")
def list_keys():
    keys = [{"key": k, "label": v.label} for k, v in CATALOG_ENTITIES.items()]
    return {"success": True, "message": "OK", "data": keys}


def _ensure_key(key: str):
    if key not in CATALOG_KEYS:
        raise HTTPException(status_code=404, detail=f"Danh mục không tồn tại: {key}")


@router.get("/{key}")
def list_entities(
    key: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    search: str | None = Query(None),
    active: bool | None = Query(None),
    service: CatalogService = Depends(get_service),
):
    _ensure_key(key)
    rows, total = service.list(key, page, page_size, search, active)
    return {
        "success": True, "message": "OK",
        "data": {"items": rows, "pagination": {
            "page": page, "page_size": page_size, "total": total,
            "total_pages": (total + page_size - 1) // page_size}},
    }


@router.get("/{key}/{record_id}")
def get_entity(key: str, record_id: int, service: CatalogService = Depends(get_service)):
    _ensure_key(key)
    row = service.get(key, record_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi.")
    return {"success": True, "message": "OK", "data": row}


@router.post("/{key}", status_code=201)
def create_entity(key: str, payload: dict, service: CatalogService = Depends(get_service)):
    _ensure_key(key)
    row = service.create(key, payload)
    return {"success": True, "message": "Đã tạo.", "data": row}


@router.put("/{key}/{record_id}")
def update_entity(key: str, record_id: int, payload: dict,
                  service: CatalogService = Depends(get_service)):
    _ensure_key(key)
    row = service.update(key, record_id, payload)
    if row is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi.")
    return {"success": True, "message": "Đã cập nhật.", "data": row}


@router.post("/{key}/{record_id}/deactivate")
def deactivate_entity(key: str, record_id: int,
                      service: CatalogService = Depends(get_service)):
    _ensure_key(key)
    row = service.deactivate(key, record_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi.")
    return {"success": True, "message": "Đã ngừng sử dụng.", "data": row}
