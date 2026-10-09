"""Nghiệp vụ phân tích tác động: nối engine với dữ liệu và lưu vết kết quả."""

from app.engine.impact_engine import select_hypotheses, traverse
from app.engine.rules import load_rules, matching_rules
from app.exceptions import NotFoundError, ValidationFailedError
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.catalog_repository import CatalogRepository
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

    def analyze(
        self,
        incident_type: str,
        source_type: str,
        source_id: int | None,
        max_depth: int = 3,
        duration_minutes: float | None = None,
        rate_per_minute: float | None = None,
        assumptions: str | None = None,
    ) -> dict:
        rules, version = load_rules()
        matched = matching_rules(rules, incident_type)

        propagate = set()
        for rule in matched:
            propagate.update(rule.get("propagate_kinds", []))

        signals = self._signals({
            "incident_type": incident_type,
            "source_object_type": source_type,
            "source_object_id": source_id,
        })

        edges = self.graph.all_edges()
        impacts = []
        if source_id is not None:
            impacts = traverse(edges, source_type, source_id, propagate, max_depth)

        dept_map = self._department_map()
        rule_assumptions = " ".join(r.get("assumptions", "") for r in matched).strip()
        full_assumptions = " ".join(x for x in (rule_assumptions, assumptions) if x).strip()

        impact_items = []
        for impact in impacts:
            impact_items.append({
                "node_type": impact["node_type"],
                "node_id": impact["node_id"],
                "node_name": self._node_name(impact["node_type"], impact["node_id"]),
                "impact_type": impact["impact_type"],
                "path": impact["path"],
                "evidence": "Cạnh '" + impact["edge_kind"] + "' trong đồ thị liên kết.",
                "rule_id": ",".join(r["id"] for r in matched) or None,
                "assumptions": full_assumptions or None,
                "missing_info": rule_assumptions or None,
                "departments": [{"code": c, "name": dept_map.get(c, {}).get("name", c)}
                                for r in matched for c in r.get("departments", [])],
            })

        # Định lượng sản lượng có nguy cơ mất (chỉ cho loại dừng máy khi đủ 2 đầu vào).
        quantification = {
            "available": False,
            "message": "Chưa đủ dữ liệu để định lượng (thiếu thời lượng dừng hoặc tốc độ sản xuất).",
        }
        if incident_type == "MACHINE_STOP" and duration_minutes is not None and rate_per_minute is not None:
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
                "path": [],
                "evidence": f"{duration_minutes} phút × {rate_per_minute} pcs/phút = {lost} pcs.",
                "rule_id": ",".join(r["id"] for r in matched) or None,
                "assumptions": quantification["assumptions"],
                "missing_info": None,
                "departments": [],
            })

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
            "impacts": impact_items,
            "hypotheses": hypotheses,
            "actions": actions,
            "quantification": quantification,
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
        result["source_type"] = "INCIDENT"
        result["source_id"] = incident_id
        result["source_incident_id"] = incident_id
        return result

    def run_whatif(self, incident_type, source_type, source_id, max_depth=3,
                   duration_minutes=None, rate_per_minute=None, assumptions=None) -> dict:
        result = self.analyze(
            incident_type=incident_type, source_type=source_type, source_id=source_id,
            max_depth=max_depth, duration_minutes=duration_minutes,
            rate_per_minute=rate_per_minute, assumptions=assumptions,
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
        return result

    def _save(self, source_type, source_id, input_data, rule_version, is_simulated, result) -> dict:
        run = self.analysis.create_run({
            "source_type": source_type, "source_id": source_id,
            "input": input_data, "rule_version": rule_version,
            "is_simulated": is_simulated,
        })
        run_id = run["id"]
        self.analysis.save_impacts(run_id, result["impacts"])
        self.analysis.save_hypotheses(run_id, result["hypotheses"])
        self.analysis.save_actions(run_id, [
            {"department_id": a["department_id"], "department_name": a["department_name"],
             "action": a["action"], "priority": a["priority"]}
            for a in result["actions"]
        ])
        return run

    def list_runs(self, page, page_size, source_type=None):
        return self.analysis.list_runs(page, page_size, source_type)

    def get_run(self, run_id):
        run = self.analysis.get_run(run_id)
        if run is None:
            raise NotFoundError("Không tìm thấy kết quả phân tích.")
        return {
            "run": run,
            "impacts": self.analysis.list_impacts(run_id),
            "hypotheses": self.analysis.list_hypotheses(run_id),
            "actions": self.analysis.list_actions(run_id),
        }
