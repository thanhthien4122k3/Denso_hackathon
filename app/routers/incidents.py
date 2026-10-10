"""API quản lý sự cố, nguyên nhân và liên kết bản ghi vận hành."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from app.auth import current_user
from app.repositories.context_repository import ContextRepository
from app.services.context_verification_service import ContextVerificationService
from app.services.incident_service import IncidentService
from app.settings import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


def _require_role(request: Request, allowed: tuple):
    roles = set(getattr(request.state, "roles", []))
    if "ADMIN" in roles or roles & set(allowed):
        return
    raise HTTPException(status_code=403, detail="Không có quyền thực hiện hành động này.")


def get_service() -> IncidentService:
    return IncidentService()


def get_context_service() -> ContextVerificationService:
    return ContextVerificationService()


def get_context_repo() -> ContextRepository:
    return ContextRepository()


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
                    service: IncidentService = Depends(get_service),
                    user: dict = Depends(current_user),
                    ctx: ContextRepository = Depends(get_context_repo)):
    row, created = service.create(payload)
    if created:
        ctx.add_history(row["id"], "CREATED", user["username"], {"code": row.get("code")})
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
def update_incident(incident_id: int, payload: dict,
                    request: Request,
                    service: IncidentService = Depends(get_service),
                    user: dict = Depends(current_user),
                    ctx: ContextRepository = Depends(get_context_repo)):
    closing = payload.get("status") == "RESOLVED" or "closed_at" in payload
    if closing:
        _require_role(request, ("COORDINATOR",))
    row = service.update(incident_id, payload)
    ctx.add_history(incident_id, "UPDATED", user["username"], {"status": payload.get("status")})
    return {"success": True, "message": "Đã cập nhật.", "data": row}


# causes
@router.get("/{incident_id}/causes")
def list_causes(incident_id: int, service: IncidentService = Depends(get_service)):
    return {"success": True, "message": "OK", "data": service.list_causes(incident_id)}


@router.post("/{incident_id}/causes", status_code=201)
def create_cause(incident_id: int, payload: dict, request: Request,
                 service: IncidentService = Depends(get_service),
                 user: dict = Depends(current_user),
                 ctx: ContextRepository = Depends(get_context_repo)):
    if payload.get("kind") == "CONFIRMED":
        _require_role(request, ("COORDINATOR",))
    row = service.create_cause(incident_id, payload, user=user)
    ctx.add_history(incident_id, "CAUSE_" + str(payload.get("kind", "HYPOTHESIS")),
                    user["username"], {"content": payload.get("content")})
    return {"success": True, "message": "Đã thêm.", "data": row}


@router.put("/causes/{cause_id}")
def update_cause(cause_id: int, payload: dict, request: Request,
                 service: IncidentService = Depends(get_service),
                 user: dict = Depends(current_user),
                 ctx: ContextRepository = Depends(get_context_repo)):
    current = service.get_cause(cause_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy nguyên nhân.")
    # Cần quyền khi sửa nguyên nhân đã xác nhận (kể cả không gửi trường kind)
    # hoặc khi xác nhận một nguyên nhân mới.
    if current.get("kind") == "CONFIRMED" or payload.get("kind") == "CONFIRMED":
        _require_role(request, ("COORDINATOR",))
    row = service.update_cause(cause_id, payload, user=user)
    ctx.add_history(current["incident_id"], "CAUSE_UPDATED", user["username"],
                    {"cause_id": cause_id, "kind": payload.get("kind", current.get("kind")),
                     "content": payload.get("content")})
    return {"success": True, "message": "Đã cập nhật.", "data": row}


@router.delete("/causes/{cause_id}")
def delete_cause(cause_id: int, request: Request,
                 service: IncidentService = Depends(get_service),
                 user: dict = Depends(current_user)):
    _require_role(request, ("COORDINATOR",))
    current = service.get_cause(cause_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy nguyên nhân.")
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


# ---- bối cảnh sản xuất cần xác minh ----
@router.get("/{incident_id}/context")
def get_context(incident_id: int,
                service: ContextVerificationService = Depends(get_context_service)):
    return {"success": True, "message": "OK", "data": service.get_context(incident_id)}


@router.post("/{incident_id}/context/verify", status_code=201)
def verify_context(incident_id: int, payload: dict, request: Request,
                   service: ContextVerificationService = Depends(get_context_service),
                   user: dict = Depends(current_user),
                   ctx: ContextRepository = Depends(get_context_repo)):
    _require_role(request, ("COORDINATOR",))
    row = service.verify(incident_id, payload.get("operation_ids"), payload.get("reason"),
                         payload.get("evidence"), user)
    ctx.add_history(incident_id, "CONTEXT_VERIFIED", user["username"],
                    {"operation_ids": payload.get("operation_ids"), "reason": payload.get("reason")})
    return {"success": True, "message": "Đã xác minh bối cảnh.", "data": row}


# ---- khôi phục và đóng hồ sơ ----
@router.post("/{incident_id}/recover")
def recover(incident_id: int, payload: dict, request: Request,
            service: IncidentService = Depends(get_service),
            user: dict = Depends(current_user),
            ctx: ContextRepository = Depends(get_context_repo)):
    _require_role(request, ("COORDINATOR",))
    row = service.recover(incident_id, payload.get("recovered_at"), user)
    ctx.add_history(incident_id, "RECOVERED", user["username"],
                    {"recovered_at": payload.get("recovered_at"), "note": payload.get("note")})
    return {"success": True, "message": "Đã xác nhận khôi phục.", "data": row}


@router.post("/{incident_id}/close")
def close(incident_id: int, payload: dict, request: Request,
          service: IncidentService = Depends(get_service),
          user: dict = Depends(current_user),
          ctx: ContextRepository = Depends(get_context_repo)):
    _require_role(request, ("COORDINATOR",))
    row = service.close(incident_id, payload.get("resolution_summary"),
                        payload.get("root_cause_status", "UNKNOWN"), user,
                        payload.get("closed_at"))
    ctx.add_history(incident_id, "CLOSED", user["username"],
                    {"resolution_summary": payload.get("resolution_summary")})
    return {"success": True, "message": "Đã đóng hồ sơ.", "data": row}
