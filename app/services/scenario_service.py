"""Nạp dữ liệu demo cho 3 kịch bản mô phỏng (chủ động, không tự động)."""

from uuid import uuid4

from app import scenarios as s
from app.repositories.catalog_repository import CatalogRepository
from app.repositories.graph_repository import GraphRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.operations_repository import OperationsRepository
from app.repositories.system_repository import SystemRepository


class ScenarioService:
    def __init__(self, **repos):
        self.catalog = repos.get("catalog") or CatalogRepository()
        self.graph = repos.get("graph") or GraphRepository()
        self.system = repos.get("system") or SystemRepository()
        self.operations = repos.get("operations") or OperationsRepository()
        self.incidents = repos.get("incidents") or IncidentRepository()

    def is_loaded(self) -> bool:
        return self.catalog.find_by_code("department", "MAINTENANCE") is not None

    def load_demo(self) -> dict:
        if self.is_loaded():
            return {"loaded": False, "message": "Dữ liệu demo đã được nạp từ trước."}

        ids = {}  # (node_type, code) -> id

        def node_id(ntype, code):
            return ids[(ntype, code)]

        # Danh mục
        for dept in s.DEPARTMENTS:
            row = self.catalog.create("department", {**dept, "is_simulated": True})
            ids[("department", dept["code"])] = row["id"]
        for shift in s.SHIFTS:
            row = self.catalog.create("shift", {**shift, "is_simulated": True})
            ids[("shift", shift["code"])] = row["id"]
        for line in s.LINES:
            row = self.catalog.create("line", {
                **line, "is_simulated": True,
                "department_id": node_id("department", "PLANNING"),
            })
            ids[("line", line["code"])] = row["id"]
        for proc in s.PROCESSES:
            row = self.catalog.create("process", {
                **proc, "is_simulated": True,
                "line_id": node_id("line", "LINE-01"),
            })
            ids[("process", proc["code"])] = row["id"]
        for machine in s.MACHINES:
            row = self.catalog.create("machine", {
                **machine, "is_simulated": True,
                "department_id": node_id("department", "MAINTENANCE"),
            })
            ids[("machine", machine["code"])] = row["id"]
        for material in s.MATERIALS:
            row = self.catalog.create("material", {
                **material, "is_simulated": True,
                "department_id": node_id("department", "WAREHOUSE"),
            })
            ids[("material", material["code"])] = row["id"]
        for product in s.PRODUCTS:
            row = self.catalog.create("product", {
                **product, "is_simulated": True,
                "department_id": node_id("department", "PLANNING"),
            })
            ids[("product", product["code"])] = row["id"]
        for order in s.ORDERS:
            row = self.catalog.create("order", {
                **order, "is_simulated": True,
                "product_id": node_id("product", "PROD-001"),
            })
            ids[("order", order["code"])] = row["id"]
        for lot in s.LOTS:
            row = self.catalog.create("lot", {
                **lot, "is_simulated": True,
                "production_order_id": node_id("order", "ORD-001"),
            })
            ids[("lot", lot["code"])] = row["id"]

        # Cạnh đồ thị
        for edge in s.build_edges(ids):
            self.graph.create_edge(edge)

        # Lớp hệ thống
        source_ids = {}
        for src in s.DATA_SOURCES:
            row = self.system.create_source({
                "code": src["code"], "name": src["name"],
                "source_type": src["source_type"],
                "collection_method": src["collection_method"],
                "owner_department_id": node_id("department", "IT_DATA"),
                "confirmed": src.get("confirmed", False), "is_simulated": True,
            })
            source_ids[src["code"]] = row["id"]
        dataset_ids = {}
        for ds in s.DATASETS:
            row = self.system.create_dataset({
                "code": ds["code"], "name": ds["name"],
                "source_id": source_ids[ds["source_code"]],
                "dataset_type": ds["dataset_type"],
                "collection_method": ds["collection_method"],
                "generation_unit": ds["generation_unit"],
                "update_schedule": ds["update_schedule"],
                "event_time_field": ds["event_time_field"],
                "timezone": ds["timezone"],
                "owner_department_id": node_id("department", "IT_DATA"),
                "confirmed": ds.get("confirmed", False), "is_simulated": True,
            })
            dataset_ids[ds["code"]] = row["id"]
        field_ids = {}
        for f in s.DATASET_FIELDS:
            row = self.system.create_field({
                "dataset_id": dataset_ids[f["dataset_code"]],
                "code": f["code"], "name": f["name"],
                "data_type": f["data_type"], "is_key": f["is_key"],
                "confirmed": False,
            })
            field_ids[(f["dataset_code"], f["code"])] = row["id"]
        for flow in s.DATA_FLOWS:
            self.system.create_flow({
                "code": flow["code"], "name": flow["name"],
                "source_dataset_id": dataset_ids[flow["from"]],
                "target_dataset_id": dataset_ids[flow["to"]],
                "confirmed": False, "is_simulated": True,
            })
        for dataset_code, field_code, target_type, target_code in s.MAPPINGS:
            self.graph.create_edge({
                "source_type": "field", "source_id": field_ids[(dataset_code, field_code)],
                "target_type": target_type, "target_id": node_id(target_type, target_code),
                "kind": "data_mapping",
                "label": f"Trường {field_code} ánh xạ {target_code}",
                "source_confirmation": "Demo", "is_simulated": True,
            })

        # Vận hành
        for d in s.DOWNTIMES:
            self.operations.create_downtime({
                "machine_id": node_id("machine", d["machine_code"]),
                "start_time": s.dt(d["start_time"]), "end_time": s.dt(d["end_time"]),
                "reason": d["reason"], "error_code": d["error_code"],
                "operator_name": d["operator_name"], "is_simulated": True,
            })
        for m in s.MACHINE_STATES:
            self.operations.create_state({
                "machine_id": node_id("machine", m["machine_code"]),
                "event_time": s.dt(m["event_time"]), "state": m["state"],
                "error_code": m.get("error_code"), "is_simulated": True,
            })
        for q in s.QC_RESULTS:
            self.operations.create_qc({
                "lot_id": node_id("lot", q["lot_code"]),
                "product_id": node_id("product", q["product_code"]),
                "process_id": node_id("process", q["process_code"]),
                "check_time": s.dt(q["check_time"]),
                "inspected_qty": q["inspected_qty"], "defect_qty": q["defect_qty"],
                "defect_type": q["defect_type"], "result": q["result"],
                "is_simulated": True,
            })
        for ms in s.MATERIAL_STATUSES:
            self.operations.create_material({
                "material_id": node_id("material", ms["material_code"]),
                "recorded_at": s.dt(ms["recorded_at"]),
                "available_qty": ms["available_qty"], "unit": ms["unit"],
                "scope": ms["scope"], "is_simulated": True,
            })

        # Sự cố
        for inc in s.INCIDENTS:
            self.incidents.create({
                "code": inc["code"], "title": inc["title"],
                "incident_type": inc["incident_type"],
                "source_object_type": inc["source_object_type"],
                "source_object_id": node_id(inc["source_object_type"], inc["source_object_code"]),
                "start_time": s.dt(inc["start_time"]),
                "end_time": s.dt(inc["end_time"]) if inc.get("end_time") else None,
                "severity": inc["severity"], "description": inc["description"],
                "status": inc["status"],
                "assigned_department_id": node_id("department", inc["department_code"]),
                "request_id": uuid4(), "is_simulated": True,
            })

        return {"loaded": True, "message": "Đã nạp dữ liệu demo (dữ liệu mô phỏng — chưa xác nhận bởi Denso)."}
