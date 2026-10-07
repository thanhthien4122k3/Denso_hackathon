"""Nạp scenario DEMO-D3-AMBIGUOUS-01: nhiều bối cảnh cùng phù hợp.

Một máy có hai lịch sử thực hiện cùng bao phủ thời điểm sự cố (hai lô khác nhau),
chưa xác nhận là xử lý đồng thời. Dùng để kiểm tra trạng thái AMBIGUOUS.
"""

from datetime import datetime
from uuid import uuid4

from app.repositories.catalog_repository import CatalogRepository
from app.repositories.context_repository import ContextRepository
from app.repositories.graph_repository import GraphRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.operations_repository import OperationsRepository

SCENARIO_ID = "DEMO-D3-AMBIGUOUS-01"


def _dt(iso):
    return datetime.fromisoformat(iso)


class ScenarioAmbiguousService:
    def __init__(self, **repos):
        self.catalog = repos.get("catalog") or CatalogRepository()
        self.graph = repos.get("graph") or GraphRepository()
        self.operations = repos.get("operations") or OperationsRepository()
        self.incidents = repos.get("incidents") or IncidentRepository()
        self.context = repos.get("context") or ContextRepository()

    def is_loaded(self) -> bool:
        return self.catalog.find_by_code("machine", "AMB-M01") is not None

    def load(self) -> dict:
        if self.is_loaded():
            return {"loaded": False, "message": "DEMO-D3-AMBIGUOUS-01 đã nạp từ trước."}

        ids = {}

        def nid(t, c):
            return ids[(t, c)]

        def ensure_dept(code, name):
            row = self.catalog.find_by_code("department", code)
            if row is None:
                row = self.catalog.create("department", {"code": code, "name": name, "is_simulated": True})
            ids[("department", code)] = row["id"]
            return row["id"]

        prod = ensure_dept("PROD", "Sản xuất")
        ids[("line", "LINE-01")] = self._ensure_catalog("line", "LINE-01", "Chuyền demo 01", {"department_id": prod})
        ids[("process", "AMB-P10")] = self._ensure_catalog(
            "process", "AMB-P10", "Công đoạn AMB", {"line_id": ids[("line", "LINE-01")]})
        ids[("machine", "AMB-M01")] = self._ensure_catalog(
            "machine", "AMB-M01", "Máy AMB", {"department_id": prod})
        ids[("product", "AMB-PROD")] = self._ensure_catalog(
            "product", "AMB-PROD", "Sản phẩm AMB", {"department_id": prod})
        ids[("order", "AMB-ORDER")] = self._ensure_catalog(
            "order", "AMB-ORDER", "Lệnh AMB", {"product_id": ids[("product", "AMB-PROD")], "status": "IN_PROGRESS"})
        ids[("lot", "AMB-LOT-A")] = self._ensure_catalog(
            "lot", "AMB-LOT-A", "Lô AMB A", {"production_order_id": ids[("order", "AMB-ORDER")]})
        ids[("lot", "AMB-LOT-B")] = self._ensure_catalog(
            "lot", "AMB-LOT-B", "Lô AMB B", {"production_order_id": ids[("order", "AMB-ORDER")]})

        self.graph.create_edge({
            "source_type": "machine", "source_id": nid("machine", "AMB-M01"),
            "target_type": "process", "target_id": nid("process", "AMB-P10"),
            "kind": "production_dependency", "label": "Máy phục vụ công đoạn",
            "source_confirmation": "Demo", "is_simulated": True,
        })

        # Hai lịch sử thực hiện chồng lấn tại 10:00 (chưa xác nhận đồng thời).
        self.context.create_operation({
            "lot_id": nid("lot", "AMB-LOT-A"), "process_id": nid("process", "AMB-P10"),
            "machine_id": nid("machine", "AMB-M01"),
            "started_at": _dt("2026-10-06T08:00:00+07:00"),
            "ended_at": _dt("2026-10-06T10:30:00+07:00"),
            "status": "COMPLETED", "source": "Demo", "scenario_id": SCENARIO_ID, "is_simulated": True,
        })
        self.context.create_operation({
            "lot_id": nid("lot", "AMB-LOT-B"), "process_id": nid("process", "AMB-P10"),
            "machine_id": nid("machine", "AMB-M01"),
            "started_at": _dt("2026-10-06T09:30:00+07:00"),
            "ended_at": _dt("2026-10-06T11:00:00+07:00"),
            "status": "COMPLETED", "source": "Demo", "scenario_id": SCENARIO_ID, "is_simulated": True,
        })

        self.operations.create_state({
            "machine_id": nid("machine", "AMB-M01"),
            "event_time": _dt("2026-10-06T10:00:00+07:00"), "state": "STOPPED",
            "error_code": "E-AMB-01", "is_simulated": True,
        })
        self.operations.create_downtime({
            "machine_id": nid("machine", "AMB-M01"),
            "start_time": _dt("2026-10-06T10:00:00+07:00"), "end_time": None,
            "error_code": "E-AMB-01", "reason": "Dừng tại điểm giao của hai bối cảnh",
            "is_simulated": True,
        })

        self.incidents.create({
            "code": "INC-AMB-01", "title": "Máy AMB-M01 dừng (bối cảnh mơ hồ)",
            "incident_type": "MACHINE_STOP", "source_object_type": "machine",
            "source_object_id": nid("machine", "AMB-M01"),
            "start_time": _dt("2026-10-06T10:00:00+07:00"), "severity": "HIGH",
            "description": "Máy dừng; chưa xác định lô đang chạy.",
            "status": "OPEN", "request_id": uuid4(), "is_simulated": True,
        })

        return {"loaded": True,
                "message": "Đã nạp DEMO-D3-AMBIGUOUS-01 (dữ liệu tổng hợp để kiểm thử)."}

    def _ensure_catalog(self, key, code, name, extra):
        row = self.catalog.find_by_code(key, code)
        if row is None:
            row = self.catalog.create(key, {"code": code, "name": name, "is_simulated": True, **extra})
        return row["id"]
