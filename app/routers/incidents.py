"""API quản lý sự cố, nguyên nhân và liên kết bản ghi vận hành."""

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from app.services.incident_service import IncidentService
from app.settings import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


def get_service() -> IncidentService:
    return IncidentService()


def _page(page, page_size, total):
    return {"page": page, "page_size": page_size, "total": total,
            "total_pages": (total + page_size - 1) // page_size}


@router.get("")
def list_incidents(page: int = Query(1, ge=1), page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
                   status: str | None = Query(None), incident_type: str | None = Query(None),
                   search: str | None = Query(None), service: IncidentService = Depends(get_service)):
    rows, total = service.list(page, page_size, status, incident_type, search)
    return {"success": True, "message": "OK", "data": {"items": rows, "pagination": _page(page, page_size, total)}}


@router.post("", status_code=201)
def create_incident(payload: dict, response: Response,
                    service: IncidentService = Depends(get_service)):
    row, created = service.create(payload)
    if not created:
        response.status_code = 200
    return {"success": True,
            "message": "Đã tạo sự cố." if created else "Sự cố đã tồn tại (cùng request_id).",
            "data": row}


@router.get("/{incident_id}")
def get_incident(incident_id: int, service: IncidentService = Depends(get_service)):
    row = service.get(incident_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy sự cố.")
    return {"success": True, "message": "OK", "data": row}


@router.put("/{incident_id}")
def update_incident(incident_id: int, payload: dict, service: IncidentService = Depends(get_service)):
    return {"success": True, "message": "Đã cập nhật.", "data": service.update(incident_id, payload)}


# causes
@router.get("/{incident_id}/causes")
def list_causes(incident_id: int, service: IncidentService = Depends(get_service)):
    return {"success": True, "message": "OK", "data": service.list_causes(incident_id)}


@router.post("/{incident_id}/causes", status_code=201)
def create_cause(incident_id: int, payload: dict, service: IncidentService = Depends(get_service)):
    return {"success": True, "message": "Đã thêm.", "data": service.create_cause(incident_id, payload)}


@router.put("/causes/{cause_id}")
def update_cause(cause_id: int, payload: dict, service: IncidentService = Depends(get_service)):
    return {"success": True, "message": "Đã cập nhật.", "data": service.update_cause(cause_id, payload)}


@router.delete("/causes/{cause_id}")
def delete_cause(cause_id: int, service: IncidentService = Depends(get_service)):
    service.delete_cause(cause_id)
    return {"success": True, "message": "Đã xóa.", "data": None}


# links
@router.get("/{incident_id}/links")
def list_links(incident_id: int, service: IncidentService = Depends(get_service)):
    return {"success": True, "message": "OK", "data": service.list_links(incident_id)}


@router.post("/{incident_id}/links", status_code=201)
def create_link(incident_id: int, payload: dict, service: IncidentService = Depends(get_service)):
    return {"success": True, "message": "Đã thêm.", "data": service.create_link(incident_id, payload)}


@router.delete("/links/{link_id}")
def delete_link(link_id: int, service: IncidentService = Depends(get_service)):
    service.delete_link(link_id)
    return {"success": True, "message": "Đã xóa.", "data": None}
