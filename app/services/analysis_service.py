"""Nghiệp vụ phân tích tác động: nối engine với dữ liệu và lưu vết kết quả."""

from datetime import datetime, timedelta

from app.engine.impact_engine import match_past_incidents, select_hypotheses, traverse
from app.engine.rules import load_rules, matching_rules
from app.exceptions import NotFoundError, ValidationFailedError
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.catalog_repository import CatalogRepository
from app.repositories.context_repository import ContextRepository
from app.repositories.graph_repository import GraphRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.operations_repository import OperationsRepository
from app.settings import MATERIAL_LOW_THRESHOLD


class AnalysisService:
    def __init__(self, **repos):
        self.analysis = repos.get("analysis") or AnalysisRepository()
        self.graph = repos.get("graph") or GraphRepository()
        self.incidents = repos.get("incidents") or IncidentRepository()
        self.operations = repos.get("operations") or OperationsRepository()
        self.catalog = repos.get("catalog") or CatalogRepository()
        self.context = repos.get("context") or ContextRepository()

    def _department_map(self) -> dict:
        rows, _ = self.catalog.list("department", 1, 500, None, None)
        return {r["code"]: {"id": r["id"], "name": r["name"]} for r in rows}

    def _node_name(self, node_type: str, node_id: int) -> str:
        node = self.graph.get_node(node_type, node_id)
        if not node:
            return f"{node_type}#{node_id}"
        return node.get("name") or node.get("code") or f"{node_type}#{node_id}"

    def _signals(self, incident: dict) -> dict:
        itype = incident["incident_type"]
        source_type = incident.get("source_object_type")
        source_id = incident.get("source_object_id")

        signals = {
            "has_machine_stop": itype == "MACHINE_STOP",
            "has_error_code": False,
            "qc_fail": False,
            "low_material": False,
            "dataset_delay": itype == "DATA_DELAY",
            "defect_rate": None,
            "material_available": None,
        }
        if source_type == "machine" and source_id:
            err = self.operations.latest_downtime_error(source_id)
            signals["has_error_code"] = bool(err)
        if source_type == "lot" and source_id:
            qc = self.operations.latest_qc(source_id)
            if qc and qc["inspected_qty"]:
                signals["qc_fail"] = qc["defect_qty"] > 0
                signals["defect_rate"] = round(qc["defect_qty"] / qc["inspected_qty"] * 100, 2)
        if source_type == "material" and source_id:
            ms = self.operations.latest_material_available(source_id)
            if ms:
                avail = float(ms["available_qty"])
                signals["material_available"] = avail
                signals["low_material"] = avail < MATERIAL_LOW_THRESHOLD
        if itype == "QUALITY":
            signals["qc_fail"] = True
        if itype == "MATERIAL_SHORTAGE":
            signals["low_material"] = True
        return signals

    # ------------------------------------------------------------------
    # Bối cảnh sản xuất & ước tính định lượng
    # ------------------------------------------------------------------
    @staticmethod
    def _candidate(op) -> dict:
        return {
            "operation_id": op["id"],
            "machine_id": op["machine_id"],
            "machine_code": op.get("machine_code"),
            "process_id": op["process_id"],
            "process_code": op.get("process_code"),
            "lot_id": op["lot_id"],
            "lot_code": op.get("lot_code"),
            "order_code": op.get("order_code"),
            "started_at": op["started_at"],
            "ended_at": op["ended_at"],
            "source": op.get("source"),
            "status": op.get("status"),
        }

    def _ctx_result(self, status, candidates, selected, verification=None, message=None) -> dict:
        selected = selected or []
        primary = None
        if len(selected) == 1:
            primary = selected[0]
        elif len(candidates) == 1:
            primary = candidates[0]
        result = {
            "status": status,
            "resolved": primary is not None,
            "selected_operation_id": primary["operation_id"] if primary else None,
            "candidates": candidates,
            "message": message,
        }
        if primary:
            result.update({
                "machine_id": primary["machine_id"], "machine_code": primary["machine_code"],
                "process_id": primary["process_id"], "process_code": primary["process_code"],
                "lot_id": primary["lot_id"], "lot_code": primary["lot_code"],
                "order_code": primary.get("order_code"),
                "started_at": primary["started_at"], "ended_at": primary["ended_at"],
            })
        if verification:
            result["verified"] = {
                "decided_by": verification.get("decided_by"),
                "decided_at": verification.get("decided_at"),
                "reason": verification.get("reason"),
                "evidence": verification.get("evidence"),
                "status": verification.get("status"),
            }
        return result

    def _resolve_context(self, source_type, source_id, at_time, incident_id=None, is_simulated=None):
        """Bối cảnh lô–công đoạn–máy tại thời điểm xảy ra lỗi.

        Trả trạng thái MATCHED/AMBIGUOUS/NOT_FOUND/CONFIRMED/NEEDS_REVIEW.
        Không tự chọn khi có nhiều bối cảnh phù hợp.
        """
        if source_type != "machine" or not source_id or not at_time:
            return self._ctx_result("NOT_FOUND", [], None,
                                    message="Chưa đủ thông tin để đối chiếu bối cảnh.")
        ops = self.context.active_operations(source_id, at_time, is_simulated=is_simulated)
        candidates = [self._candidate(o) for o in ops]
        if not candidates:
            return self._ctx_result("NOT_FOUND", [], None,
                                    message="Không xác định được bối cảnh lô/công đoạn tại thời điểm này.")

        verification = self.context.latest_verification(incident_id) if incident_id else None
        if verification and verification.get("status") == "CONFIRMED":
            chosen_ids = [int(x) for x in (verification.get("operation_ids") or [])]
            selected = [c for c in candidates if c["operation_id"] in chosen_ids]
            if selected:
                return self._ctx_result("CONFIRMED", candidates, selected, verification=verification)
            return self._ctx_result("NEEDS_REVIEW", candidates, None,
                                    verification=verification,
                                    message="Bối cảnh đã thay đổi sau khi xác minh; cần kiểm tra lại.")

        if len(candidates) == 1:
            return self._ctx_result("MATCHED", candidates, candidates)
        return self._ctx_result("AMBIGUOUS", candidates, None,
                                message="Có nhiều bối cảnh phù hợp; cần xác minh trước khi kết luận lô/lệnh.")

    @staticmethod
    def _downstream_process(process_id, edges):
        for e in edges:
            if (e["kind"] == "production_dependency" and e["source_type"] == "process"
                    and e["source_id"] == process_id and e["target_type"] == "process"):
                return e["target_id"]
        return None

    def _buffer_estimate(self, context, edges, at_time, is_simulated=None):
        """Ước tính thời điểm công đoạn sau cạn hàng đệm (nếu có dữ liệu)."""
        if not context or not context.get("resolved"):
            return {"available": False, "message": "Chưa đủ dữ liệu để ước tính hàng đệm."}
        process_id = context["process_id"]
        downstream = self._downstream_process(process_id, edges)
        if downstream is None:
            return {"available": False, "message": "Không xác định được công đoạn sau của công đoạn đang xét."}
        buffer = self.context.buffer_between(process_id, downstream, at_time, is_simulated=is_simulated)
        if not buffer:
            return {"available": False,
                    "message": "Chưa có dữ liệu hàng đệm giữa hai công đoạn (không đưa ra thời điểm cụ thể)."}
        rate = self.context.capacity_for(downstream, None, None, at_time, is_simulated=is_simulated)
        if not rate or not rate.get("rate_per_minute"):
            return {"available": False,
                    "message": "Chưa có công suất tham chiếu cho công đoạn sau (không đưa ra thời điểm cụ thể)."}
        qty = float(buffer["available_qty"])
        rpm = float(rate["rate_per_minute"])
        if rpm <= 0:
            return {"available": False, "message": "Công suất tham chiếu không hợp lệ (<= 0)."}
        minutes = round(qty / rpm, 2)
        depletion_time = at_time + timedelta(minutes=minutes)
        return {
            "available": True,
            "upstream_process_id": process_id,
            "downstream_process_id": downstream,
            "downstream_name": self._node_name("process", downstream),
            "buffer_qty": qty,
            "buffer_unit": buffer.get("unit"),
            "rate_per_minute": rpm,
            "depletion_minutes": minutes,
            "depletion_time": depletion_time.isoformat(),
            "assumptions": "Không bổ sung hàng vào buffer sau mốc đánh giá; công đoạn sau duy trì tốc độ không đổi; "
                           "không có nguồn thay thế. Đây là ước tính, không phải bằng chứng công đoạn sau đã dừng.",
        }

    def _capacity_estimate(self, context, duration_minutes, at_time, is_simulated=None):
        """Ước tính năng lực gia công có nguy cơ không thực hiện trong khoảng dừng."""
        if not context or not context.get("resolved"):
            return None
        if duration_minutes is None:
            return None
        profile = self.context.capacity_for(context["process_id"], context["machine_id"],
                                            None, at_time, is_simulated=is_simulated)
        if not profile or not profile.get("rate_per_minute"):
            return None
        rpm = float(profile["rate_per_minute"])
        lost = round(duration_minutes * rpm, 2)
        return {
            "process_id": context["process_id"],
            "machine_id": context["machine_id"],
            "rate_per_minute": rpm,
            "duration_minutes": duration_minutes,
            "estimated_quantity": lost,
            "unit": profile.get("unit"),
            "formula": "năng lực có nguy cơ = thời gian dừng (phút) × công suất tham chiếu (pcs/phút)",
            "assumptions": "Công suất tham chiếu, chưa xét tồn đệm, sản xuất bù và máy thay thế. "
                           "Không cộng thêm ở từng công đoạn và không phải thành phẩm chắc chắn mất.",
        }

    @staticmethod
    def _json_safe(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {k: AnalysisService._json_safe(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [AnalysisService._json_safe(v) for v in obj]
        if isinstance(obj, (str, int, float, bool)) or obj is None:
            return obj
        return str(obj)

    def _related_past(self, incident_type, source_type, source_id, error_code):
        current = {
            "incident_type": incident_type,
            "source_object_type": source_type,
            "source_object_id": source_id,
            "error_code": error_code or "",
        }
        past = self.context.experiences_for_match()
        matched = match_past_incidents(current, past)
        return [{"incident_id": m["incident_id"], "code": m["code"],
                 "matched_criteria": m["matched_criteria"]} for m in matched]

    def analyze(
        self,
        incident_type: str,
        source_type: str,
        source_id: int | None,
        max_depth: int = 3,
        duration_minutes: float | None = None,
        rate_per_minute: float | None = None,
        assumptions: str | None = None,
        at_time=None,
        incident_id: int | None = None,
        is_simulated: bool = False,
    ) -> dict:
        rules, version = load_rules()
        matched = matching_rules(rules, incident_type)

        propagate = set()
        for rule in matched:
            propagate.update(rule.get("propagate_kinds", []))

        signals = {"has_machine_stop": incident_type == "MACHINE_STOP",
                   "has_error_code": False, "qc_fail": False, "low_material": False,
                   "dataset_delay": incident_type == "DATA_DELAY",
                   "defect_rate": None, "material_available": None}
        error_code = None
        if source_type == "machine" and source_id:
            error_code = self.operations.latest_downtime_error(source_id)
            signals["has_error_code"] = bool(error_code)
        if source_type == "lot" and source_id:
            qc = self.operations.latest_qc(source_id)
            if qc and qc["inspected_qty"]:
                signals["qc_fail"] = qc["defect_qty"] > 0
                signals["defect_rate"] = round(qc["defect_qty"] / qc["inspected_qty"] * 100, 2)
        if source_type == "material" and source_id:
            ms = self.operations.latest_material_available(source_id)
            if ms:
                avail = float(ms["available_qty"])
                signals["material_available"] = avail
                signals["low_material"] = avail < MATERIAL_LOW_THRESHOLD
        if incident_type == "QUALITY":
            signals["qc_fail"] = True
        if incident_type == "MATERIAL_SHORTAGE":
            signals["low_material"] = True

        edges = self.graph.all_edges()
        impacts = []
        if source_id is not None:
            impacts = traverse(edges, source_type, source_id, propagate, max_depth, at_time)

        dept_map = self._department_map()
        rule_assumptions = " ".join(r.get("assumptions", "") for r in matched).strip()
        full_assumptions = " ".join(x for x in (rule_assumptions, assumptions) if x).strip()

        context = self._resolve_context(source_type, source_id, at_time, incident_id, is_simulated)

        impact_items = []
        for impact in impacts:
            impact_items.append({
                "node_type": impact["node_type"],
                "node_id": impact["node_id"],
                "node_name": self._node_name(impact["node_type"], impact["node_id"]),
                "impact_type": impact["impact_type"],
                "relation_depth": impact.get("relation_depth"),
                "evidence_status": impact.get("evidence_status", "POTENTIAL"),
                "path": impact["path"],
                "evidence": "Cạnh '" + impact["edge_kind"] + "' trong đồ thị liên kết.",
                "rule_id": ",".join(r["id"] for r in matched) or None,
                "assumptions": full_assumptions or None,
                "missing_info": rule_assumptions or None,
                "departments": [{"code": c, "name": dept_map.get(c, {}).get("name", c)}
                                for r in matched for c in r.get("departments", [])],
            })

        # Ảnh hưởng quan sát được: bối cảnh đang chạy tại thời điểm lỗi.
        if context and context.get("resolved") and source_type == "machine":
            impact_items.append({
                "node_type": "lot",
                "node_id": context["lot_id"],
                "node_name": context["lot_code"],
                "impact_type": "OBSERVED",
                "relation_depth": "DIRECT",
                "evidence_status": "OBSERVED",
                "path": [],
                "evidence": "Lô đang được thực hiện tại công đoạn của máy ở thời điểm lỗi.",
                "rule_id": None,
                "assumptions": None,
                "missing_info": None,
                "departments": [],
            })

        # Định lượng sản lượng có nguy cơ mất (từ tham số người dùng hoặc công suất tham chiếu).
        quantification = {
            "available": False,
            "message": "Chưa đủ dữ liệu để định lượng (thiếu thời lượng dừng hoặc tốc độ sản xuất).",
        }
        if incident_type == "MACHINE_STOP":
            if rate_per_minute is not None and duration_minutes is not None:
                lost = round(duration_minutes * rate_per_minute, 2)
                quantification = {
                    "available": True,
                    "formula": "sản lượng có nguy cơ mất = thời gian dừng (phút) × tốc độ (pcs/phút)",
                    "duration_minutes": duration_minutes,
                    "rate_per_minute": rate_per_minute,
                    "lost_quantity": lost,
                    "assumptions": "Chưa xét tồn đệm, sản xuất bù và máy thay thế.",
                }
                impact_items.append({
                    "node_type": source_type,
                    "node_id": source_id,
                    "node_name": self._node_name(source_type, source_id),
                    "impact_type": "ESTIMATED",
                    "relation_depth": None,
                    "evidence_status": "ESTIMATED",
                    "path": [],
                    "evidence": f"{duration_minutes} phút × {rate_per_minute} pcs/phút = {lost} pcs.",
                    "rule_id": ",".join(r["id"] for r in matched) or None,
                    "assumptions": quantification["assumptions"],
                    "missing_info": None,
                    "departments": [],
                })

        buffer_estimate = self._buffer_estimate(context, edges, at_time, is_simulated) if at_time else None
        capacity_estimate = self._capacity_estimate(context, duration_minutes, at_time, is_simulated) if at_time else None

        related_past = self._related_past(incident_type, source_type, source_id, error_code)

        hypotheses = []
        for rule in matched:
            for hyp in select_hypotheses(rule.get("hypotheses", []), signals):
                hypotheses.append({
                    "content": hyp.get("content", ""),
                    "evidence": hyp.get("evidence", ""),
                    "check_more": hyp.get("check_more", ""),
                    "rule_id": hyp.get("id") or rule["id"],
                    "priority": hyp.get("priority", rule.get("priority", "MEDIUM")),
                })

        actions = []
        for rule in matched:
            for action in rule.get("actions", []):
                code = action["department"]
                dept = dept_map.get(code)
                actions.append({
                    "department_id": dept["id"] if dept else None,
                    "department_name": dept["name"] if dept else code,
                    "department_code": code,
                    "action": action["text"],
                    "priority": rule.get("priority", "MEDIUM"),
                })

        return {
            "rule_version": version,
            "rules": [r["id"] for r in matched],
            "signals": signals,
            "context": context,
            "impacts": impact_items,
            "hypotheses": hypotheses,
            "actions": actions,
            "quantification": quantification,
            "buffer_estimate": buffer_estimate,
            "capacity_estimate": capacity_estimate,
            "related_past_incidents": related_past,
        }

    def run_for_incident(self, incident_id, max_depth=3, duration_minutes=None,
                         rate_per_minute=None, assumptions=None) -> dict:
        incident = self.incidents.get(incident_id)
        if incident is None:
            raise NotFoundError("Sự cố không tồn tại.")
        if not incident.get("source_object_id"):
            raise ValidationFailedError("Sự cố chưa gắn đối tượng phát sinh.")

        result = self.analyze(
            incident_type=incident["incident_type"],
            source_type=incident["source_object_type"],
            source_id=incident["source_object_id"],
            max_depth=max_depth,
            duration_minutes=duration_minutes,
            rate_per_minute=rate_per_minute,
            assumptions=assumptions,
            at_time=incident.get("start_time"),
            incident_id=incident_id,
            is_simulated=incident.get("is_simulated", False),
        )
        run = self._save(
            source_type="INCIDENT", source_id=incident_id,
            input_data={"incident_id": incident_id, "max_depth": max_depth,
                        "duration_minutes": duration_minutes,
                        "rate_per_minute": rate_per_minute, "assumptions": assumptions},
            rule_version=result["rule_version"],
            is_simulated=incident.get("is_simulated", False),
            result=result,
        )
        result["run_id"] = run["id"]
        result["run_at"] = run["run_at"]
        result["incident_id"] = incident_id
        result["source_type"] = "INCIDENT"
        result["source_id"] = incident_id
        result["is_simulated"] = incident.get("is_simulated", False)
        result["snapshot_available"] = True
        return result

    def run_whatif(self, incident_type, source_type, source_id, max_depth=3,
                   duration_minutes=None, rate_per_minute=None, assumptions=None,
                   at_time=None) -> dict:
        if isinstance(at_time, str):
            at_time = datetime.fromisoformat(at_time.replace("Z", "+00:00"))
        result = self.analyze(
            incident_type=incident_type, source_type=source_type, source_id=source_id,
            max_depth=max_depth, duration_minutes=duration_minutes,
            rate_per_minute=rate_per_minute, assumptions=assumptions,
            at_time=at_time, is_simulated=True,
        )
        run = self._save(
            source_type="SCENARIO", source_id=source_id,
            input_data={"incident_type": incident_type, "source_type": source_type,
                        "source_id": source_id, "max_depth": max_depth,
                        "duration_minutes": duration_minutes,
                        "rate_per_minute": rate_per_minute, "assumptions": assumptions},
            rule_version=result["rule_version"], is_simulated=True, result=result,
        )
        result["run_id"] = run["id"]
        result["run_at"] = run["run_at"]
        result["incident_id"] = None
        result["source_type"] = "SCENARIO"
        result["source_id"] = source_id
        result["is_simulated"] = True
        result["snapshot_available"] = True
        return result

    def _save(self, source_type, source_id, input_data, rule_version, is_simulated, result) -> dict:
        actions_db = [
            {"department_id": a["department_id"], "department_name": a["department_name"],
             "action": a["action"], "priority": a["priority"]}
            for a in result["actions"]
        ]
        related = [{"related_incident_id": r["incident_id"], "match_criteria": ", ".join(r["matched_criteria"]),
                    "note": None} for r in result.get("related_past_incidents", [])]
        snapshot = self._json_safe(result)
        run, action_ids = self.analysis.save_run(
            {
                "source_type": source_type, "source_id": source_id,
                "input": input_data, "rule_version": rule_version,
                "is_simulated": is_simulated, "result": snapshot,
            },
            result["impacts"], result["hypotheses"], actions_db, related,
        )
        for a, aid in zip(result["actions"], action_ids):
            a["id"] = aid
        return run

    def list_runs(self, page, page_size, source_type=None, source_id=None):
        return self.analysis.list_runs(page, page_size, source_type, source_id)

    def get_run(self, run_id):
        run = self.analysis.get_run(run_id)
        if run is None:
            raise NotFoundError("Không tìm thấy kết quả phân tích.")
        snapshot = run.get("result")
        snapshot = snapshot if isinstance(snapshot, dict) else None
        return {
            "run_id": run_id,
            "run_at": run["run_at"],
            "incident_id": run["source_id"] if run["source_type"] == "INCIDENT" else None,
            "source_type": run["source_type"],
            "source_id": run["source_id"],
            "is_simulated": run.get("is_simulated", False),
            "snapshot_available": snapshot is not None,
            "rule_version": run.get("rule_version"),
            "rules": (snapshot or {}).get("rules") or [],
            "signals": (snapshot or {}).get("signals"),
            "context": (snapshot or {}).get("context"),
            "quantification": (snapshot or {}).get("quantification"),
            "buffer_estimate": (snapshot or {}).get("buffer_estimate"),
            "capacity_estimate": (snapshot or {}).get("capacity_estimate"),
            "related_past_incidents": (snapshot or {}).get("related_past_incidents") or [],
            "impacts": self.analysis.list_impacts(run_id),
            "hypotheses": self.analysis.list_hypotheses(run_id),
            "actions": self.analysis.list_actions(run_id),
        }
