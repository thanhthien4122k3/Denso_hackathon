"""Nạp bộ dữ liệu mô phỏng DEMO-D3-01 (chủ động, không tự động, không trùng)."""

import secrets
from uuid import uuid4

from app import scenario_d3 as s
from app.repositories.catalog_repository import CatalogRepository
from app.repositories.context_repository import ContextRepository
from app.repositories.graph_repository import GraphRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.operations_repository import OperationsRepository
from app.repositories.system_repository import SystemRepository
from app.services.auth_service import AuthService


def _demo_password():
    return "demo-" + secrets.token_urlsafe(9)


class ScenarioD3Service:
    def __init__(self, **repos):
        self.catalog = repos.get("catalog") or CatalogRepository()
        self.graph = repos.get("graph") or GraphRepository()
        self.system = repos.get("system") or SystemRepository()
        self.operations = repos.get("operations") or OperationsRepository()
        self.incidents = repos.get("incidents") or IncidentRepository()
        self.context = repos.get("context") or ContextRepository()

    def is_loaded(self) -> bool:
        return self.incidents.get_by_code("INC-HIST-001") is not None

    def load(self) -> dict:
        if self.is_loaded():
            return {"loaded": False, "message": "Dữ liệu DEMO-D3-01 đã được nạp từ trước."}

        ids = {}

        def nid(ntype, code):
            return ids[(ntype, code)]

        def ensure(key, data):
            row = self.catalog.find_by_code(key, data["code"])
            if row is None:
                row = self.catalog.create(key, data)
            return row["id"]

        # Danh mục (find-or-create để không lỗi khi DB đã có một phần dữ liệu)
        for dept in s.DEPARTMENTS:
            ids[("department", dept["code"])] = ensure("department", {**dept, "is_simulated": True})
        for line in s.LINES:
            ids[("line", line["code"])] = ensure("line", {
                **line, "is_simulated": True,
                "department_id": nid("department", "PROD"),
            })
        for proc in s.PROCESSES:
            ids[("process", proc["code"])] = ensure("process", {
                **proc, "is_simulated": True,
                "line_id": nid("line", "LINE-01"),
            })
        for machine in s.MACHINES:
            ids[("machine", machine["code"])] = ensure("machine", {
                "code": machine["code"], "name": machine["name"], "is_simulated": True,
                "department_id": nid("department", "MAINT"),
            })
        for material in s.MATERIALS:
            ids[("material", material["code"])] = ensure("material", {
                "code": material["code"], "name": material["name"], "is_simulated": True,
                "unit": material["unit"], "department_id": nid("department", "WH"),
            })
        for product in s.PRODUCTS:
            ids[("product", product["code"])] = ensure("product", {
                **product, "is_simulated": True,
                "department_id": nid("department", "PROD"),
            })
        for order in s.ORDERS:
            ids[("order", order["code"])] = ensure("order", {
                "code": order["code"], "name": order["name"],
                "status": order["status"], "is_simulated": True,
                "product_id": nid("product", order["product_code"]),
                "plan_qty": order["plan_qty"],
                "description": (f"Kế hoạch {order['plan_qty']} pcs, "
                                f"khung {order['plan_start']} -> {order['plan_end']}"),
            })
        for lot in s.LOTS:
            ids[("lot", lot["code"])] = ensure("lot", {
                "code": lot["code"], "name": lot["name"], "is_simulated": True,
                "production_order_id": nid("order", lot["order_code"]),
                "qty": lot["qty"],
                "description": f"Quy mô lô {lot['qty']} pcs (không phải sản lượng đã hoàn thành).",
            })

        # Quan hệ (cạnh đồ thị), hiệu lực từ 2026-10-01.
        valid_from = s.dt(s.EDGE_VALID_FROM)
        for src_type, src_code, tgt_type, tgt_code, kind, label in s.EDGES:
            self.graph.create_edge({
                "source_type": src_type, "source_id": nid(src_type, src_code),
                "target_type": tgt_type, "target_id": nid(tgt_type, tgt_code),
                "kind": kind, "label": label,
                "source_confirmation": "Demo", "is_simulated": True,
                "valid_from": valid_from,
            })

        # Bối cảnh sản xuất
        for op in s.OPERATIONS:
            self.context.create_operation({
                "lot_id": nid("lot", op["lot_code"]),
                "process_id": nid("process", op["process_code"]),
                "machine_id": nid("machine", op["machine_code"]),
                "started_at": s.dt(op["started_at"]),
                "ended_at": s.dt(op["ended_at"]) if op["ended_at"] else None,
                "status": op["status"],
                "context_status": op["status"],
                "source": "Demo",
                "scenario_id": s.SCENARIO_ID,
                "is_simulated": True,
            })

        # Vận hành nền
        for m in s.MACHINE_STATES:
            self.operations.create_state({
                "machine_id": nid("machine", m["machine_code"]),
                "event_time": s.dt(m["event_time"]), "state": m["state"],
                "is_simulated": True,
            })
        for b in s.BUFFER_SNAPSHOTS:
            self.context.create_buffer({
                "upstream_process_id": nid("process", b["upstream_process_code"]),
                "downstream_process_id": nid("process", b["downstream_process_code"]),
                "product_id": nid("product", b["product_code"]),
                "lot_id": nid("lot", b["lot_code"]),
                "available_qty": b["available_qty"], "unit": b["unit"],
                "recorded_at": s.dt(b["recorded_at"]), "source": b["source"],
                "confirmed": b["confirmed"], "scenario_id": s.SCENARIO_ID,
                "is_simulated": True,
            })
        for c in s.CAPACITY_PROFILES:
            self.context.create_capacity({
                "process_id": nid("process", c["process_code"]) if c["process_code"] else None,
                "machine_id": nid("machine", c["machine_code"]) if c["machine_code"] else None,
                "product_id": nid("product", c["product_code"]) if c["product_code"] else None,
                "rate_per_minute": c["rate_per_minute"], "unit": c["unit"],
                "valid_from": s.dt(c["valid_from"]),
                "source_confirmation": c["source_confirmation"],
                "scenario_id": s.SCENARIO_ID, "is_simulated": True,
            })
        for q in s.QC_RESULTS:
            self.operations.create_qc({
                "lot_id": nid("lot", q["lot_code"]),
                "product_id": nid("product", q["product_code"]),
                "process_id": nid("process", q["process_code"]),
                "check_time": s.dt(q["check_time"]),
                "inspected_qty": q["inspected_qty"], "defect_qty": q["defect_qty"],
                "defect_type": q["defect_type"], "result": q["result"],
                "is_simulated": True,
            })
        for ms in s.MATERIAL_STATUSES:
            self.operations.create_material({
                "material_id": nid("material", ms["material_code"]),
                "recorded_at": s.dt(ms["recorded_at"]),
                "available_qty": ms["available_qty"], "unit": ms["unit"],
                "scope": ms["scope"], "is_simulated": True,
            })

        # Lớp logic hệ thống + mapping
        source_ids = {}
        for src in s.DATA_SOURCES:
            row = self.system.create_source({
                "code": src["code"], "name": src["name"],
                "source_type": src["source_type"],
                "collection_method": src["collection_method"],
                "owner_department_id": nid("department", "DATA"),
                "confirmed": src["confirmed"], "is_simulated": True,
            })
            source_ids[src["code"]] = row["id"]
        dataset_ids = {}
        for ds in s.DATASETS:
            row = self.system.create_dataset({
                "code": ds["code"], "name": ds["name"],
                "source_id": source_ids["APP-DEMO"],
                "dataset_type": ds["dataset_type"],
                "collection_method": ds["collection_method"],
                "generation_unit": ds["generation_unit"],
                "update_schedule": ds["update_schedule"],
                "event_time_field": ds["event_time_field"],
                "timezone": ds["timezone"],
                "owner_department_id": nid("department", "DATA"),
                "confirmed": ds["confirmed"], "is_simulated": True,
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
        for m in s.MAPPINGS:
            self.context.create_mapping({
                "source_id": source_ids[m["source_code"]],
                "object_type": m["object_type"],
                "source_code": m["source_code_value"],
                "node_id": nid(m["object_type"], m["target_code"]),
                "confirmed": True, "scenario_id": s.SCENARIO_ID, "is_simulated": True,
            })

        # Cạnh luồng dữ liệu (data_flow) và ánh xạ dữ liệu-nghiệp vụ (data_mapping).
        for src_type, src_ref, tgt_type, tgt_ref, kind, label in s.DATA_FLOW_EDGES:
            src_id = source_ids[src_ref] if src_type == "source" else dataset_ids[src_ref]
            tgt_id = source_ids[tgt_ref] if tgt_type == "source" else dataset_ids[tgt_ref]
            self.graph.create_edge({
                "source_type": src_type, "source_id": src_id,
                "target_type": tgt_type, "target_id": tgt_id,
                "kind": kind, "label": label,
                "source_confirmation": "Demo", "is_simulated": True,
                "valid_from": valid_from,
            })
        for src_type, src_ref, tgt_type, tgt_code, kind, label in s.DATA_MAPPING_EDGES:
            if src_type == "field":
                ds_code, f_code = src_ref.split(".", 1)
                src_id = field_ids[(ds_code, f_code)]
            else:
                src_id = dataset_ids[src_ref]
            self.graph.create_edge({
                "source_type": src_type, "source_id": src_id,
                "target_type": tgt_type, "target_id": nid(tgt_type, tgt_code),
                "kind": kind, "label": label,
                "source_confirmation": "Demo", "is_simulated": True,
                "valid_from": valid_from,
            })

        # Mẫu nhập sai mã (chưa ánh xạ).
        self.context.create_ingestion({
            "source_id": source_ids["APP-DEMO"],
            "request_id": uuid4(),
            "event_time": s.dt(s.UNMAPPED_INGESTION["event_time"]),
            "payload": s.UNMAPPED_INGESTION["payload"],
            "status": s.UNMAPPED_INGESTION["status"],
            "error": s.UNMAPPED_INGESTION["error"],
            "scenario_id": s.SCENARIO_ID, "is_simulated": True,
        })

        # Sự cố cũ INC-HIST-001 + bằng chứng + kinh nghiệm (idempotent).
        inc = s.HISTORIC_INCIDENT
        if self.incidents.get_by_code(inc["code"]) is None:
            request_id = uuid4()
            incident = self.incidents.create({
                "code": inc["code"], "title": inc["title"],
                "incident_type": inc["incident_type"],
                "source_object_type": inc["source_object_type"],
                "source_object_id": nid(inc["source_object_type"], inc["source_object_code"]),
                "start_time": s.dt(inc["start_time"]), "end_time": s.dt(inc["end_time"]),
                "severity": inc["severity"], "description": inc["description"],
                "status": inc["status"],
                "assigned_department_id": nid("department", inc["department_code"]),
                "request_id": request_id, "is_simulated": True,
                "recovered_at": s.dt(inc["recovered_at"]), "recovered_by": inc["recovered_by"],
                "closed_at": s.dt(inc["closed_at"]), "closed_by": inc["closed_by"],
                "resolution_summary": inc["resolution_summary"],
                "root_cause_status": inc["root_cause_status"],
            })
            incident_id = incident["id"]
            self.operations.create_downtime({
                "machine_id": nid("machine", s.HISTORIC_DOWNTIME["machine_code"]),
                "start_time": s.dt(s.HISTORIC_DOWNTIME["start_time"]),
                "end_time": s.dt(s.HISTORIC_DOWNTIME["end_time"]),
                "reason": s.HISTORIC_DOWNTIME["reason"],
                "error_code": s.HISTORIC_DOWNTIME["error_code"],
                "operator_name": s.HISTORIC_DOWNTIME["operator_name"],
                "is_simulated": True,
            })
            self.operations.create_state({
                "machine_id": nid("machine", s.HISTORIC_RECOVERY_STATE["machine_code"]),
                "event_time": s.dt(s.HISTORIC_RECOVERY_STATE["event_time"]),
                "state": s.HISTORIC_RECOVERY_STATE["state"], "is_simulated": True,
            })
            self.incidents.create_cause({
                "incident_id": incident_id,
                "content": s.HISTORIC_CAUSE["content"],
                "kind": s.HISTORIC_CAUSE["kind"],
                "evidence": s.HISTORIC_CAUSE["evidence"],
                "confirmed_by": s.HISTORIC_CAUSE["confirmed_by"],
                "confirmed_at": s.dt(inc["recovered_at"]),
            })
            self.context.create_experience({
                "source_incident_id": incident_id,
                "incident_type": s.HISTORIC_EXPERIENCE["incident_type"],
                "error_code": s.HISTORIC_EXPERIENCE["error_code"],
                "machine_id": nid("machine", inc["source_object_code"]),
                "symptom": s.HISTORIC_EXPERIENCE["symptom"],
                "root_cause": s.HISTORIC_EXPERIENCE["root_cause"],
                "actions": s.HISTORIC_EXPERIENCE["actions"],
                "result": s.HISTORIC_EXPERIENCE["result"],
                "approved_by": s.HISTORIC_EXPERIENCE["approved_by"],
                "approved_at": s.dt(inc["closed_at"]),
                "scenario_id": s.SCENARIO_ID, "is_simulated": True,
            })
            self.context.add_history(incident_id, "CREATED", "demo-supervisor",
                                     {"code": inc["code"], "scenario_id": s.SCENARIO_ID})

        # Hai sự cố mở cho tình huống QUALITY và MATERIAL_SHORTAGE (idempotent).
        for inc in s.OPEN_INCIDENTS:
            if self.incidents.get_by_code(inc["code"]) is not None:
                continue
            self.incidents.create({
                "code": inc["code"], "title": inc["title"],
                "incident_type": inc["incident_type"],
                "source_object_type": inc["source_object_type"],
                "source_object_id": nid(inc["source_object_type"], inc["source_object_code"]),
                "start_time": s.dt(inc["start_time"]),
                "severity": inc["severity"], "description": inc["description"],
                "status": inc["status"],
                "assigned_department_id": nid("department", inc["department_code"]),
                "request_id": uuid4(), "is_simulated": True,
            })

        # Tài khoản demo (mật khẩu sinh ngẫu nhiên, trả về đúng một lần).
        credentials = {}
        auth = AuthService()
        for u in s.USERS:
            if auth.repository.find_by_username(u["username"]) is not None:
                continue
            password = _demo_password()
            auth.create_user(u["username"], u["display_name"], password, u["roles"], is_simulated=True)
            credentials[u["username"]] = {"password": password, "roles": u["roles"]}

        return {"loaded": True,
                "message": "Đã nạp dữ liệu mô phỏng DEMO-D3-01 (dữ liệu tổng hợp để kiểm thử, không phải dữ liệu DENSO).",
                "credentials": credentials}
