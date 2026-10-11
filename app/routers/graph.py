"""API đồ thị liên kết hai lớp: cạnh và bản đồ."""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.graph import EDGE_KINDS, NODE_LABELS, NODE_TYPES
from app.schemas import GraphEdgeCreate, GraphEdgeUpdate
from app.services.graph_service import GraphService
from app.settings import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

router = APIRouter(prefix="/api/graph", tags=["graph"])


def get_service() -> GraphService:
    return GraphService()


@router.get("/meta")
def meta():
    return {
        "success": True, "message": "OK",
        "data": {
            "node_types": [{"type": t, "label": l} for t, l in NODE_LABELS.items()],
            "edge_kinds": [{"kind": k, "label": v} for k, v in EDGE_KINDS.items()],
        },
    }


@router.get("/map")
def map_graph(types: str | None = Query(None),
              center: str | None = Query(None),
              depth: int | None = Query(None, ge=1, le=10),
              limit: int | None = Query(None, ge=1, le=500),
              service: GraphService = Depends(get_service)):
    selected = [t for t in (types.split(",") if types else []) if t in NODE_TYPES] or None
    return {"success": True, "message": "OK", "data": service.get_map(selected, center, depth, limit)}


@router.get("/edges")
def list_edges(page: int = Query(1, ge=1), page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
               kind: str | None = Query(None), is_simulated: bool | None = Query(None),
               service: GraphService = Depends(get_service)):
    rows, total = service.list_edges(page, page_size, kind, is_simulated)
    return {"success": True, "message": "OK", "data": {"items": rows, "pagination": {
        "page": page, "page_size": page_size, "total": total,
        "total_pages": (total + page_size - 1) // page_size}}}


@router.post("/edges", status_code=201)
def create_edge(payload: GraphEdgeCreate, service: GraphService = Depends(get_service)):
    return {"success": True, "message": "Đã tạo.", "data": service.create_edge(payload.model_dump())}


@router.put("/edges/{edge_id}")
def update_edge(edge_id: int, payload: GraphEdgeUpdate, service: GraphService = Depends(get_service)):
    return {"success": True, "message": "Đã cập nhật.", "data": service.update_edge(edge_id, payload.model_dump())}


@router.delete("/edges/{edge_id}")
def delete_edge(edge_id: int, service: GraphService = Depends(get_service)):
    if not service.delete_edge(edge_id):
        raise HTTPException(status_code=404, detail="Không tìm thấy quan hệ.")
    return {"success": True, "message": "Đã xóa.", "data": None}
