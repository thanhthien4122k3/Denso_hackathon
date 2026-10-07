"""API cho bối cảnh sản xuất, hàng đệm, công suất, mapping, truy vết và kinh nghiệm."""

from fastapi import APIRouter, Depends, Query

from app.repositories.context_repository import ContextRepository
from app.settings import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

router = APIRouter(prefix="/api/context", tags=["context"])


def get_repo() -> ContextRepository:
    return ContextRepository()


def _page(page, page_size, total):
    return {"page": page, "page_size": page_size, "total": total,
            "total_pages": (total + page_size - 1) // page_size}


@router.get("/operations")
def list_operations(page: int = Query(1, ge=1),
                    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
                    machine_id: int | None = Query(None), lot_id: int | None = Query(None),
                    repo: ContextRepository = Depends(get_repo)):
    rows, total = repo.list_operations(page, page_size, machine_id, lot_id)
    return {"success": True, "message": "OK", "data": {"items": rows, "pagination": _page(page, page_size, total)}}


@router.get("/buffers")
def list_buffers(page: int = Query(1, ge=1),
                 page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
                 repo: ContextRepository = Depends(get_repo)):
    rows, total = repo.list_buffers(page, page_size)
    return {"success": True, "message": "OK", "data": {"items": rows, "pagination": _page(page, page_size, total)}}


@router.get("/capacities")
def list_capacities(page: int = Query(1, ge=1),
                    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
                    repo: ContextRepository = Depends(get_repo)):
    rows, total = repo.list_capacities(page, page_size)
    return {"success": True, "message": "OK", "data": {"items": rows, "pagination": _page(page, page_size, total)}}


@router.get("/mappings")
def list_mappings(page: int = Query(1, ge=1),
                  page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
                  repo: ContextRepository = Depends(get_repo)):
    rows, total = repo.list_mappings(page, page_size)
    return {"success": True, "message": "OK", "data": {"items": rows, "pagination": _page(page, page_size, total)}}


@router.get("/ingestions")
def list_ingestions(page: int = Query(1, ge=1),
                    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
                    status: str | None = Query(None),
                    repo: ContextRepository = Depends(get_repo)):
    rows, total = repo.list_ingestions(page, page_size, status)
    return {"success": True, "message": "OK", "data": {"items": rows, "pagination": _page(page, page_size, total)}}


@router.get("/experiences")
def list_experiences(page: int = Query(1, ge=1),
                     page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
                     repo: ContextRepository = Depends(get_repo)):
    rows, total = repo.list_experiences(page, page_size)
    return {"success": True, "message": "OK", "data": {"items": rows, "pagination": _page(page, page_size, total)}}


@router.post("/experiences", status_code=201)
def create_experience(payload: dict, repo: ContextRepository = Depends(get_repo)):
    return {"success": True, "message": "Đã lưu kinh nghiệm.", "data": repo.create_experience(payload)}


@router.get("/users")
def list_users(repo: ContextRepository = Depends(get_repo)):
    return {"success": True, "message": "OK", "data": repo.list_users()}
