"""API công việc theo bộ phận."""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.services.task_service import TaskService
from app.settings import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def get_service() -> TaskService:
    return TaskService()


@router.get("")
def list_tasks(page: int = Query(1, ge=1), page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
               department_id: int | None = Query(None), status: str | None = Query(None),
               service: TaskService = Depends(get_service)):
    rows, total = service.list(page, page_size, department_id, status)
    return {"success": True, "message": "OK", "data": {"items": rows, "pagination": {
        "page": page, "page_size": page_size, "total": total,
        "total_pages": (total + page_size - 1) // page_size}}}


@router.get("/{task_id}")
def get_task(task_id: int, service: TaskService = Depends(get_service)):
    row = service.get(task_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc.")
    return {"success": True, "message": "OK", "data": row}


@router.post("", status_code=201)
def create_task(payload: dict, service: TaskService = Depends(get_service)):
    return {"success": True, "message": "Đã tạo.", "data": service.create(payload)}


@router.put("/{task_id}")
def update_task(task_id: int, payload: dict, service: TaskService = Depends(get_service)):
    return {"success": True, "message": "Đã cập nhật.", "data": service.update(task_id, payload)}


@router.post("/{task_id}/status")
def set_status(task_id: int, payload: dict, service: TaskService = Depends(get_service)):
    return {"success": True, "message": "Đã cập nhật trạng thái.",
            "data": service.set_status(task_id, payload.get("status"))}
