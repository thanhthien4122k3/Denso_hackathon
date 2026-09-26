"""API nguồn dữ liệu, dataset, trường và luồng dữ liệu."""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.services.system_service import SystemService

router = APIRouter(prefix="/api/system", tags=["system-layer"])


def get_service() -> SystemService:
    return SystemService()


def _page(page, page_size, total):
    return {"page": page, "page_size": page_size, "total": total,
            "total_pages": (total + page_size - 1) // page_size}


# sources
@router.get("/sources")
def list_sources(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                 search: str | None = Query(None), service: SystemService = Depends(get_service)):
    rows, total = service.list_sources(page, page_size, search)
    return {"success": True, "message": "OK", "data": {"items": rows, "pagination": _page(page, page_size, total)}}


@router.post("/sources", status_code=201)
def create_source(payload: dict, service: SystemService = Depends(get_service)):
    return {"success": True, "message": "Đã tạo.", "data": service.create_source(payload)}


@router.put("/sources/{source_id}")
def update_source(source_id: int, payload: dict, service: SystemService = Depends(get_service)):
    return {"success": True, "message": "Đã cập nhật.", "data": service.update_source(source_id, payload)}


@router.delete("/sources/{source_id}")
def delete_source(source_id: int, service: SystemService = Depends(get_service)):
    service.delete_source(source_id)
    return {"success": True, "message": "Đã xóa.", "data": None}


# datasets
@router.get("/datasets")
def list_datasets(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                  source_id: int | None = Query(None), search: str | None = Query(None),
                  service: SystemService = Depends(get_service)):
    rows, total = service.list_datasets(page, page_size, source_id, search)
    return {"success": True, "message": "OK", "data": {"items": rows, "pagination": _page(page, page_size, total)}}


@router.post("/datasets", status_code=201)
def create_dataset(payload: dict, service: SystemService = Depends(get_service)):
    return {"success": True, "message": "Đã tạo.", "data": service.create_dataset(payload)}


@router.put("/datasets/{dataset_id}")
def update_dataset(dataset_id: int, payload: dict, service: SystemService = Depends(get_service)):
    return {"success": True, "message": "Đã cập nhật.", "data": service.update_dataset(dataset_id, payload)}


@router.delete("/datasets/{dataset_id}")
def delete_dataset(dataset_id: int, service: SystemService = Depends(get_service)):
    service.delete_dataset(dataset_id)
    return {"success": True, "message": "Đã xóa.", "data": None}


# fields
@router.get("/datasets/{dataset_id}/fields")
def list_fields(dataset_id: int, service: SystemService = Depends(get_service)):
    return {"success": True, "message": "OK", "data": service.list_fields(dataset_id)}


@router.post("/fields", status_code=201)
def create_field(payload: dict, service: SystemService = Depends(get_service)):
    return {"success": True, "message": "Đã tạo.", "data": service.create_field(payload)}


@router.put("/fields/{field_id}")
def update_field(field_id: int, payload: dict, service: SystemService = Depends(get_service)):
    return {"success": True, "message": "Đã cập nhật.", "data": service.update_field(field_id, payload)}


@router.delete("/fields/{field_id}")
def delete_field(field_id: int, service: SystemService = Depends(get_service)):
    service.delete_field(field_id)
    return {"success": True, "message": "Đã xóa.", "data": None}


# flows
@router.get("/flows")
def list_flows(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
               service: SystemService = Depends(get_service)):
    rows, total = service.list_flows(page, page_size)
    return {"success": True, "message": "OK", "data": {"items": rows, "pagination": _page(page, page_size, total)}}


@router.post("/flows", status_code=201)
def create_flow(payload: dict, service: SystemService = Depends(get_service)):
    return {"success": True, "message": "Đã tạo.", "data": service.create_flow(payload)}


@router.delete("/flows/{flow_id}")
def delete_flow(flow_id: int, service: SystemService = Depends(get_service)):
    service.delete_flow(flow_id)
    return {"success": True, "message": "Đã xóa.", "data": None}
