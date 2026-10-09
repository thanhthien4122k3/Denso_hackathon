"""Tổng quan dashboard: số liệu quyết định, checklist thiết lập, độ mới dữ liệu."""

from datetime import datetime, timedelta, timezone

from app.database import get_connection
from app.exceptions import DatabaseUnavailableError
from psycopg import OperationalError

# Ánh xạ lịch cập nhật -> ngưỡng chậm (không đánh giá nếu không có ánh xạ).
FRESHNESS_THRESHOLDS = {
    "realtime": timedelta(minutes=15),
    "per_shift": timedelta(hours=8),
    "daily": timedelta(hours=26),
    "batch": timedelta(hours=26),
}


class DashboardService:
    def _query_one(self, sql, params=None):
        try:
            with get_connection() as conn, conn.cursor() as cur:
                cur.execute(sql, params or {})
                return cur.fetchone()
        except OperationalError as exc:
            raise DatabaseUnavailableError(str(exc)) from exc

    def _query_all(self, sql, params=None):
        try:
            with get_connection() as conn, conn.cursor() as cur:
                cur.execute(sql, params or {})
                return cur.fetchall()
        except OperationalError as exc:
            raise DatabaseUnavailableError(str(exc)) from exc

    def summary(self, date_from=None, date_to=None, simulated=None) -> dict:
        # Điều kiện lọc mô phỏng cho các bảng có cột is_simulated.
        sim = None if simulated is None else bool(simulated)

        def sim_where(prefix=""):
            return "" if sim is None else (prefix + "is_simulated = %(sim)s")

        inc_conds = ["status <> 'RESOLVED'"]
        inc_list_conds = ["i.status <> 'RESOLVED'"]
        if sim is not None:
            inc_conds.append("is_simulated = %(sim)s")
            inc_list_conds.append("i.is_simulated = %(sim)s")
        inc_where = " WHERE " + " AND ".join(inc_conds)
        inc_list_where = " WHERE " + " AND ".join(inc_list_conds)
        inc_params = {"sim": sim} if sim is not None else {}

        open_incidents = self._query_one(
            "SELECT COUNT(*) AS n FROM production.incidents" + inc_where, inc_params
        )["n"]

        task_conds = ["status = 'TODO'"]
        task_list_conds = ["t.status = 'TODO'"]
        if sim is not None:
            task_conds.append("is_simulated = %(sim)s")
            task_list_conds.append("t.is_simulated = %(sim)s")
        task_where = " WHERE " + " AND ".join(task_conds)
        task_list_where = " WHERE " + " AND ".join(task_list_conds)
        todo_tasks = self._query_one(
            "SELECT COUNT(*) AS n FROM production.action_tasks" + task_where, inc_params
        )["n"]

        ms_where = sim_where(" WHERE ") if sim is not None else ""
        machine_state_total = self._query_one(
            "SELECT COUNT(DISTINCT machine_id) AS n FROM production.machine_states" + ms_where,
            inc_params,
        )["n"]
        if machine_state_total == 0:
            machines_stopped = None
        else:
            machines_stopped = self._query_one(
                "SELECT COUNT(*) AS n FROM ("
                "  SELECT DISTINCT ON (machine_id) machine_id, state, event_time"
                "  FROM production.machine_states" + ms_where +
                "  ORDER BY machine_id, event_time DESC"
                ") latest"
                " WHERE latest.state = 'STOPPED'"
                "   AND latest.event_time >= now() - interval '24 hours'",
                inc_params,
            )["n"]

        # Sản lượng (bảng production_records không có cờ mô phỏng -> luôn là dữ liệu thật).
        if sim is True:
            good_qty = defect_qty = defect_rate = None
        else:
            prod_where = ""
            prod_params = {}
            if date_from:
                prod_where += " WHERE production_date >= %(date_from)s"
                prod_params["date_from"] = date_from
            if date_to:
                prod_where += (" AND " if prod_where else " WHERE ") + "production_date <= %(date_to)s"
                prod_params["date_to"] = date_to
            prod = self._query_one(
                "SELECT COALESCE(SUM(good_quantity),0) AS g, COALESCE(SUM(defect_quantity),0) AS d,"
                " COUNT(*) AS c FROM production.production_records" + prod_where,
                prod_params,
            )
            if prod["c"] == 0:
                good_qty = defect_qty = defect_rate = None
            else:
                good_qty = prod["g"]
                defect_qty = prod["d"]
                total = good_qty + defect_qty
                defect_rate = round(defect_qty / total * 100, 2) if total else None

        qc_where = (" WHERE is_simulated = %(sim)s") if sim is not None else ""
        qc = self._query_one(
            "SELECT COALESCE(SUM(inspected_qty),0) AS i, COALESCE(SUM(defect_qty),0) AS d"
            " FROM production.qc_results" + qc_where,
            inc_params,
        )
        qc_defect_rate = round(qc["d"] / qc["i"] * 100, 2) if qc["i"] else None

        metrics = {
            "open_incidents": open_incidents,
            "todo_tasks": todo_tasks,
            "machines_stopped": machines_stopped,
            "good_qty": good_qty,
            "defect_qty": defect_qty,
            "defect_rate": defect_rate,
            "qc_defect_rate": qc_defect_rate,
        }

        incidents = self._query_all(
            "SELECT i.id, i.code, i.title, i.incident_type, i.severity, i.status,"
            " i.start_time, i.source_object_type, i.source_object_id, i.is_simulated,"
            " d.name AS department_name, r.affected_count, r.task_count, r.departments AS report_departments"
            " FROM production.incidents i"
            " LEFT JOIN production.departments d ON d.id = i.assigned_department_id"
            " LEFT JOIN production.incident_reports r ON r.incident_id = i.id"
            + inc_list_where +
            " ORDER BY CASE i.severity WHEN 'CRITICAL' THEN 0 WHEN 'HIGH' THEN 1"
            "   WHEN 'MEDIUM' THEN 2 ELSE 3 END, i.start_time DESC NULLS LAST"
            " LIMIT 10",
            inc_params,
        )
        tasks = self._query_all(
            "SELECT t.id, t.title, t.priority, t.status, t.source_incident_id,"
            " t.source_analysis_run_id, t.is_simulated, d.name AS department_name"
            " FROM production.action_tasks t"
            " LEFT JOIN production.departments d ON d.id = t.department_id" + task_list_where +
            " ORDER BY t.id DESC LIMIT 10",
            inc_params,
        )

        datasets = self._query_all(
            "SELECT id, code, name, last_received_at, update_schedule, confirmed,"
            " is_simulated FROM production.datasets ORDER BY id"
        )
        now = datetime.now(timezone.utc)
        data_freshness = []
        for ds in datasets:
            last = ds["last_received_at"]
            schedule = (ds["update_schedule"] or "").lower()
            if last is None:
                status = "NO_DATA"
            elif schedule not in FRESHNESS_THRESHOLDS:
                status = "UNKNOWN"
            else:
                if last.tzinfo is None:
                    last = last.replace(tzinfo=timezone.utc)
                status = "STALE" if (now - last) > FRESHNESS_THRESHOLDS[schedule] else "OK"
            data_freshness.append({
                "id": ds["id"], "code": ds["code"], "name": ds["name"],
                "last_received_at": last, "update_schedule": ds["update_schedule"],
                "confirmed": ds["confirmed"], "is_simulated": ds["is_simulated"],
                "status": status,
            })

        departments = self._query_one("SELECT COUNT(*) AS n FROM production.departments")["n"]
        lines = self._query_one("SELECT COUNT(*) AS n FROM production.production_lines")["n"]
        processes = self._query_one("SELECT COUNT(*) AS n FROM production.processes")["n"]
        machines = self._query_one("SELECT COUNT(*) AS n FROM production.machines")["n"]
        edges = self._query_one("SELECT COUNT(*) AS n FROM production.graph_edges")["n"]
        records = self._query_one("SELECT COUNT(*) AS n FROM production.production_records")["n"]
        incident_rows = self._query_one("SELECT COUNT(*) AS n FROM production.incidents")["n"]
        machine_states = machine_state_total

        has_ops_data = (records + machine_states + incident_rows) > 0

        checklist = [
            {"key": "departments_lines", "title": "Tạo bộ phận và chuyền",
             "description": "Khai báo các bộ phận và chuyền sản xuất.",
             "done": departments > 0 and lines > 0, "route": "catalog"},
            {"key": "processes_machines", "title": "Khai báo công đoạn và máy",
             "description": "Khai báo công đoạn và máy móc/thiết bị.",
             "done": processes > 0 and machines > 0, "route": "catalog"},
            {"key": "relations", "title": "Thiết lập quan hệ",
             "description": "Nối máy - công đoạn - vật tư - sản phẩm.",
             "done": edges > 0, "route": "map"},
            {"key": "first_record", "title": "Ghi nhận dữ liệu đầu tiên",
             "description": "Nhập sản lượng, trạng thái máy, QC hoặc vật tư.",
             "done": has_ops_data, "route": "operations"},
            {"key": "incident", "title": "Tạo sự cố hoặc thử kịch bản",
             "description": "Tạo sự cố đầu tiên hoặc chạy kịch bản mô phỏng.",
             "done": incident_rows > 0, "route": "incidents"},
        ]

        setup = {
            "departments": departments, "lines": lines, "processes": processes,
            "machines": machines,
            "materials": self._query_one("SELECT COUNT(*) AS n FROM production.materials")["n"],
            "products": self._query_one("SELECT COUNT(*) AS n FROM production.products")["n"],
            "orders": self._query_one("SELECT COUNT(*) AS n FROM production.production_orders")["n"],
            "lots": self._query_one("SELECT COUNT(*) AS n FROM production.lots")["n"],
            "edges": edges,
            "sources": self._query_one("SELECT COUNT(*) AS n FROM production.data_sources")["n"],
            "datasets": self._query_one("SELECT COUNT(*) AS n FROM production.datasets")["n"],
            "analysis_runs": self._query_one("SELECT COUNT(*) AS n FROM production.analysis_runs")["n"],
            "has_simulated": self._query_one("SELECT COUNT(*) AS n FROM production.incidents WHERE is_simulated = TRUE")["n"] > 0
            or self._query_one("SELECT COUNT(*) AS n FROM production.departments WHERE is_simulated = TRUE")["n"] > 0,
        }

        last_updated = self._query_one(
            "SELECT GREATEST("
            " COALESCE((SELECT MAX(created_at) FROM production.production_records), 'epoch'),"
            " COALESCE((SELECT MAX(received_at) FROM production.machine_states), 'epoch'),"
            " COALESCE((SELECT MAX(received_at) FROM production.qc_results), 'epoch'),"
            " COALESCE((SELECT MAX(received_at) FROM production.material_statuses), 'epoch'),"
            " COALESCE((SELECT MAX(created_at) FROM production.incidents), 'epoch')) AS ts"
        )["ts"]
        if last_updated.year == 1970:
            last_updated = None

        has_data = (departments + records + machine_states + incident_rows) > 0

        return {
            "metrics": metrics,
            "incidents": incidents,
            "tasks": tasks,
            "data_freshness": data_freshness,
            "checklist": checklist,
            "setup": setup,
            "last_updated": last_updated,
            "has_data": has_data,
        }
