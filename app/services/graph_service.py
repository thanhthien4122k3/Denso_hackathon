"""Nghiệp vụ đồ thị: kiểm tra quan hệ hợp lệ và endpoint tồn tại."""

from collections import defaultdict
from datetime import datetime

from app.exceptions import NotFoundError, ValidationFailedError
from app.graph import validate_edge
from app.repositories.graph_repository import GraphRepository

_EDGE_FIELDS = {
    "source_type": "str",
    "source_id": "int",
    "target_type": "str",
    "target_id": "int",
    "kind": "str",
    "label": "str",
    "description": "str",
    "source_confirmation": "str",
    "valid_from": "datetime",
    "valid_to": "datetime",
    "is_simulated": "bool",
}


class GraphService:
    def __init__(self, repository: GraphRepository | None = None):
        self.repository = repository or GraphRepository()

    def _clean(self, data: dict, required_ids: bool = True) -> dict:
        cleaned = {}
        for name, value in data.items():
            if name not in _EDGE_FIELDS:
                raise ValueError(f"Trường không hợp lệ: {name}.")
            ftype = _EDGE_FIELDS[name]
            if value is None or value == "":
                continue
            if ftype == "int":
                if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                    raise ValueError(f"{name} phải là số nguyên dương.")
            elif ftype == "bool":
                if not isinstance(value, bool):
                    raise ValueError(f"{name} phải là true/false.")
            elif ftype == "str":
                if not isinstance(value, str):
                    raise ValueError(f"{name} phải là chuỗi.")
                value = value.strip()
                if not value:
                    continue
            elif ftype == "datetime":
                if isinstance(value, str):
                    value = datetime.fromisoformat(value.replace("Z", "+00:00"))
                if not isinstance(value, datetime):
                    raise ValueError(f"{name} phải là thời gian hợp lệ.")
            cleaned[name] = value

        if required_ids:
            for req in ("source_type", "source_id", "target_type", "target_id", "kind"):
                if req not in cleaned:
                    raise ValueError(f"Thiếu trường bắt buộc: {req}.")
        return cleaned

    def create_edge(self, data: dict) -> dict:
        cleaned = self._clean(data, required_ids=True)
        validate_edge(cleaned["source_type"], cleaned["target_type"], cleaned["kind"])
        if (cleaned["source_type"] == cleaned["target_type"]
                and cleaned["source_id"] == cleaned["target_id"]):
            raise ValidationFailedError("Không thể tạo quan hệ tự nối (đối tượng trỏ tới chính nó).")
        if not self.repository.node_exists(cleaned["source_type"], cleaned["source_id"]):
            raise NotFoundError("Node nguồn không tồn tại.")
        if not self.repository.node_exists(cleaned["target_type"], cleaned["target_id"]):
            raise NotFoundError("Node đích không tồn tại.")
        cleaned.setdefault("is_simulated", False)
        return self.repository.create_edge(cleaned)

    def update_edge(self, edge_id: int, data: dict) -> dict:
        existing = self.repository.get_edge(edge_id)
        if existing is None:
            raise NotFoundError("Quan hệ không tồn tại.")
        cleaned = self._clean(data, required_ids=False)
        return self.repository.update_edge(edge_id, cleaned)

    def delete_edge(self, edge_id: int) -> bool:
        return self.repository.delete_edge(edge_id)

    def list_edges(self, page, page_size, kind, is_simulated):
        return self.repository.list_edges(page, page_size, kind, is_simulated)

    def get_map(self, types=None, center=None, depth=None, limit=None):
        nodes = self.repository.list_nodes(types)
        edges = self.repository.all_edges()
        if center and depth:
            try:
                ctype, cid = center.split(":", 1)
                cid = int(cid)
            except (ValueError, AttributeError):
                raise ValidationFailedError("center phải có dạng 'type:id'.")
            nodes, edges = self._neighborhood(nodes, edges, ctype, cid, depth)
        limited = False
        if limit and len(nodes) > limit:
            limited = True
            keep = {(n["type"], n["id"]) for n in nodes[:limit]}
            nodes = nodes[:limit]
            edges = [
                e for e in edges
                if (e["source_type"], e["source_id"]) in keep
                and (e["target_type"], e["target_id"]) in keep
            ]
        return {"nodes": nodes, "edges": edges, "limited": limited}

    @staticmethod
    def _neighborhood(nodes, edges, center_type, center_id, depth):
        node_set = {(n["type"], n["id"]) for n in nodes}
        adj = defaultdict(set)
        for e in edges:
            s = (e["source_type"], e["source_id"])
            t = (e["target_type"], e["target_id"])
            if s in node_set and t in node_set:
                adj[s].add(t)
                adj[t].add(s)
        start = (center_type, center_id)
        if start not in node_set:
            return [], []
        visited = {start}
        frontier = {start}
        for _ in range(depth):
            nxt = set()
            for n in frontier:
                for m in adj.get(n, ()):
                    if m not in visited:
                        visited.add(m)
                        nxt.add(m)
            frontier = nxt
        nodes_out = [n for n in nodes if (n["type"], n["id"]) in visited]
        edges_out = [
            e for e in edges
            if (e["source_type"], e["source_id"]) in visited
            and (e["target_type"], e["target_id"]) in visited
        ]
        return nodes_out, edges_out
