"""API tích hợp nguồn ngoài: kết nối, khám phá, nhập file/bảng, batch."""

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile

from app.auth import current_user, require_roles
from app.exceptions import ValidationFailedError
from app.settings import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.services.integration_service import TARGETS, IntegrationService

router = APIRouter(prefix="/api/integration", tags=["integration"])


def get_service() -> IntegrationService:
    return IntegrationService()


def _page(page, page_size, total):
    return {"page": page, "page_size": page_size, "total": total,
            "total_pages": (total + page_size - 1) // page_size}


@router.get("/targets")
def list_targets():
    return {"success": True, "message": "OK", "data": TARGETS}


# ---- connection profiles ----
@router.get("/connections")
def list_connections(page: int = Query(1, ge=1),
                     page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
                     service: IntegrationService = Depends(get_service),
                     _user: dict = Depends(current_user)):
    rows, total = service.list_profiles(page, page_size)
    return {"success": True, "message": "OK",
            "data": {"items": rows, "pagination": _page(page, page_size, total)}}


@router.post("/connections", status_code=201)
def create_connection(payload: dict, service: IntegrationService = Depends(get_service),
                      _admin: dict = Depends(require_roles("ADMIN"))):
    return {"success": True, "message": "Đã tạo.", "data": service.create_profile(payload)}


@router.put("/connections/{profile_id}")
def update_connection(profile_id: int, payload: dict,
                      service: IntegrationService = Depends(get_service),
                      _admin: dict = Depends(require_roles("ADMIN"))):
    return {"success": True, "message": "Đã cập nhật.",
            "data": service.update_profile(profile_id, payload)}


@router.delete("/connections/{profile_id}")
def delete_connection(profile_id: int, service: IntegrationService = Depends(get_service),
                      _admin: dict = Depends(require_roles("ADMIN"))):
    service.delete_profile(profile_id)
    return {"success": True, "message": "Đã xóa.", "data": None}


@router.post("/connections/{profile_id}/test")
def test_connection(profile_id: int, service: IntegrationService = Depends(get_service),
                    _admin: dict = Depends(require_roles("ADMIN"))):
    return {"success": True, "message": "OK", "data": service.test_connection(profile_id)}


@router.get("/connections/{profile_id}/schemas")
def list_schemas(profile_id: int, service: IntegrationService = Depends(get_service),
                 _admin: dict = Depends(require_roles("ADMIN"))):
    return {"success": True, "message": "OK", "data": service.list_schemas(profile_id)}


@router.get("/connections/{profile_id}/tables")
def list_tables(profile_id: int, schema: str = Query(...),
                service: IntegrationService = Depends(get_service),
                _admin: dict = Depends(require_roles("ADMIN"))):
    return {"success": True, "message": "OK", "data": service.list_tables(profile_id, schema)}


@router.get("/connections/{profile_id}/columns")
def list_columns(profile_id: int, schema: str = Query(...), table: str = Query(...),
                 service: IntegrationService = Depends(get_service),
                 _admin: dict = Depends(require_roles("ADMIN"))):
    return {"success": True, "message": "OK",
            "data": service.list_columns(profile_id, schema, table)}


@router.get("/connections/{profile_id}/preview")
def preview_table(profile_id: int, schema: str = Query(...), table: str = Query(...),
                  limit: int = Query(100, ge=1, le=100),
                  service: IntegrationService = Depends(get_service),
                  _admin: dict = Depends(require_roles("ADMIN"))):
    return {"success": True, "message": "OK",
            "data": service.preview_table(profile_id, schema, table, limit=limit)}


# ---- file upload ----
@router.post("/files/preview")
async def upload_file(file: UploadFile = File(...),
                      sheet: str | None = Query(None),
                      service: IntegrationService = Depends(get_service),
                      _user: dict = Depends(current_user)):
    raw = await file.read()
    try:
        return {"success": True, "message": "OK",
                "data": service.upload_file(file.filename or "upload", raw, sheet=sheet)}
    except ValidationFailedError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise ValidationFailedError(str(exc)) from exc


# ---- ingestion batches ----
@router.post("/batches", status_code=201)
def create_batch(payload: dict, service: IntegrationService = Depends(get_service),
                 user: dict = Depends(current_user)):
    token = payload.get("token")
    profile_id = payload.get("connection_id")
    target_type = payload.get("target_type")
    mapping = payload.get("mapping") or {}
    sheet = payload.get("sheet")
    source_id = payload.get("source_id")
    dataset_id = payload.get("dataset_id")
    created_by = user.get("username")
    if token:
        batch = service.create_file_batch(token, target_type, mapping, sheet=sheet,
                                          source_id=source_id, dataset_id=dataset_id,
                                          created_by=created_by)
    elif profile_id:
        schema = payload.get("schema")
        table = payload.get("table")
        if not schema or not table:
            raise ValidationFailedError("schema và table là bắt buộc khi nhập từ database.")
        batch = service.create_table_batch(profile_id, schema, table, target_type, mapping,
                                           source_id=source_id, dataset_id=dataset_id,
                                           created_by=created_by)
    else:
        raise ValidationFailedError("Cần token file hoặc connection_id để tạo batch.")
    return {"success": True, "message": "Đã tạo batch.", "data": batch}


@router.get("/batches")
def list_batches(page: int = Query(1, ge=1),
                 page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
                 service: IntegrationService = Depends(get_service),
                 _user: dict = Depends(current_user)):
    rows, total = service.list_batches(page, page_size)
    return {"success": True, "message": "OK",
            "data": {"items": rows, "pagination": _page(page, page_size, total)}}


@router.get("/batches/{batch_id}")
def get_batch(batch_id: int, service: IntegrationService = Depends(get_service),
              _user: dict = Depends(current_user)):
    return {"success": True, "message": "OK", "data": service.get_batch(batch_id)}


@router.post("/batches/{batch_id}/confirm")
def confirm_batch(batch_id: int, service: IntegrationService = Depends(get_service),
                  user: dict = Depends(current_user)):
    return {"success": True, "message": "Đã xác nhận nhập.",
            "data": service.confirm_batch(batch_id, username=user.get("username"))}
