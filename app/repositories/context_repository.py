"""Repository cho bối cảnh sản xuất, hàng đệm, công suất, mapping và truy vết.

Các bảng mới (migration 0007): production_operations, buffer_snapshots,
capacity_profiles, source_object_mappings, ingestion_records, users,
incident_experiences, incident_history.
"""

from psycopg import OperationalError
from psycopg.errors import ForeignKeyViolation
from psycopg.types.json import Jsonb

from app.database import get_connection
from app.exceptions import DatabaseUnavailableError, NotFoundError


def _db_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ForeignKeyViolation as exc:
            raise NotFoundError("Đối tượng tham chiếu không tồn tại.") from exc
        except OperationalError as exc:
            raise DatabaseUnavailableError(str(exc)) from exc

    wrapper.__name__ = func.__name__
    return wrapper


class ContextRepository:
    def __init__(self, settings=None):
        self._settings = settings

    def _conn(self):
        return get_connection(self._settings)

    # ---- production_operations ----
    @_db_errors
    def list_operations(self, page, page_size, machine_id=None, lot_id=None):
        conds, params = [], {"limit": page_size, "offset": (page - 1) * page_size}
        if machine_id is not None:
            conds.append("machine_id = %(machine_id)s")
            params["machine_id"] = machine_id
        if lot_id is not None:
            conds.append("lot_id = %(lot_id)s")
            params["lot_id"] = lot_id
        where = (" WHERE " + " AND ".join(conds)) if conds else ""
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                f"SELECT COUNT(*) AS total FROM production.production_operations{where}",
                params,
            )
            total = cur.fetchone()["total"]
            cur.execute(
                f"SELECT * FROM production.production_operations{where} "
                "ORDER BY id DESC LIMIT %(limit)s OFFSET %(offset)s",
                params,
            )
            return cur.fetchall(), total

    @_db_errors
    def create_operation(self, data):
        cols = ["lot_id", "process_id", "machine_id", "started_at", "ended_at",
                "status", "context_status", "source", "confirmed_by",
                "scenario_id", "is_simulated"]
        cols = [c for c in cols if c in data]
        sql = (
            "INSERT INTO production.production_operations (" + ", ".join(cols)
            + ") VALUES (" + ", ".join(f"%({c})s" for c in cols) + ") RETURNING *"
        )
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, data)
            row = cur.fetchone()
            conn.commit()
        return row

    @_db_errors
    def active_operation(self, machine_id, at_time):
        """Bối cảnh sản xuất đang chạy trên máy tại thời điểm at_time (chỉ 1)."""
        rows = self.active_operations(machine_id, at_time)
        return rows[0] if len(rows) == 1 else None

    @_db_errors
    def active_operations(self, machine_id, at_time):
        """TẤT CẢ bối cảnh phù hợp (không dùng LIMIT 1 — không che giấu nhiều kết quả)."""
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT po.*, l.code AS lot_code, l.name AS lot_name, "
                "p.code AS process_code, p.name AS process_name, "
                "m.code AS machine_code, m.name AS machine_name, "
                "o.code AS order_code "
                "FROM production.production_operations po "
                "JOIN production.lots l ON l.id = po.lot_id "
                "JOIN production.processes p ON p.id = po.process_id "
                "LEFT JOIN production.machines m ON m.id = po.machine_id "
                "LEFT JOIN production.production_orders o ON o.id = l.production_order_id "
                "WHERE po.machine_id = %(machine_id)s "
                "AND po.started_at <= %(at)s "
                "AND (po.ended_at IS NULL OR po.ended_at > %(at)s) "
                "ORDER BY po.started_at",
                {"machine_id": machine_id, "at": at_time},
            )
            return cur.fetchall()

    @_db_errors
    def get_operation(self, operation_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT po.*, l.code AS lot_code, l.name AS lot_name, "
                "p.code AS process_code, p.name AS process_name, "
                "m.code AS machine_code, m.name AS machine_name, "
                "o.code AS order_code "
                "FROM production.production_operations po "
                "JOIN production.lots l ON l.id = po.lot_id "
                "JOIN production.processes p ON p.id = po.process_id "
                "LEFT JOIN production.machines m ON m.id = po.machine_id "
                "LEFT JOIN production.production_orders o ON o.id = l.production_order_id "
                "WHERE po.id = %(id)s",
                {"id": operation_id},
            )
            return cur.fetchone()

    @_db_errors
    def operations_by_ids(self, operation_ids):
        if not operation_ids:
            return []
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT po.*, l.code AS lot_code, p.code AS process_code, "
                "m.code AS machine_code, o.code AS order_code "
                "FROM production.production_operations po "
                "JOIN production.lots l ON l.id = po.lot_id "
                "JOIN production.processes p ON p.id = po.process_id "
                "LEFT JOIN production.machines m ON m.id = po.machine_id "
                "LEFT JOIN production.production_orders o ON o.id = l.production_order_id "
                "WHERE po.id = ANY(%(ids)s) ORDER BY po.id",
                {"ids": list(operation_ids)},
            )
            return cur.fetchall()

    @_db_errors
    def active_operation_by_process(self, process_id, at_time):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT po.*, l.code AS lot_code, p.code AS process_code "
                "FROM production.production_operations po "
                "JOIN production.lots l ON l.id = po.lot_id "
                "JOIN production.processes p ON p.id = po.process_id "
                "WHERE po.process_id = %(process_id)s "
                "AND po.started_at <= %(at)s "
                "AND (po.ended_at IS NULL OR po.ended_at > %(at)s) "
                "ORDER BY po.started_at DESC LIMIT 1",
                {"process_id": process_id, "at": at_time},
            )
            return cur.fetchone()

    # ---- buffer_snapshots ----
    @_db_errors
    def list_buffers(self, page, page_size):
        params = {"limit": page_size, "offset": (page - 1) * page_size}
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM production.buffer_snapshots")
            total = cur.fetchone()["total"]
            cur.execute(
                "SELECT * FROM production.buffer_snapshots "
                "ORDER BY id DESC LIMIT %(limit)s OFFSET %(offset)s",
                params,
            )
            return cur.fetchall(), total

    @_db_errors
    def create_buffer(self, data):
        cols = ["upstream_process_id", "downstream_process_id", "product_id", "lot_id",
                "available_qty", "unit", "recorded_at", "source", "confirmed",
                "scenario_id", "is_simulated"]
        cols = [c for c in cols if c in data]
        sql = (
            "INSERT INTO production.buffer_snapshots (" + ", ".join(cols)
            + ") VALUES (" + ", ".join(f"%({c})s" for c in cols) + ") RETURNING *"
        )
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, data)
            row = cur.fetchone()
            conn.commit()
        return row

    @_db_errors
    def buffer_between(self, upstream_process_id, downstream_process_id, at_time):
        """Lượng hàng đệm gần nhất (theo recorded_at <= at_time) giữa hai công đoạn."""
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM production.buffer_snapshots "
                "WHERE upstream_process_id = %(up)s AND downstream_process_id = %(down)s "
                "AND recorded_at <= %(at)s "
                "ORDER BY recorded_at DESC LIMIT 1",
                {"up": upstream_process_id, "down": downstream_process_id, "at": at_time},
            )
            return cur.fetchone()

    # ---- capacity_profiles ----
    @_db_errors
    def list_capacities(self, page, page_size):
        params = {"limit": page_size, "offset": (page - 1) * page_size}
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM production.capacity_profiles")
            total = cur.fetchone()["total"]
            cur.execute(
                "SELECT * FROM production.capacity_profiles "
                "ORDER BY id DESC LIMIT %(limit)s OFFSET %(offset)s",
                params,
            )
            return cur.fetchall(), total

    @_db_errors
    def create_capacity(self, data):
        cols = ["process_id", "machine_id", "product_id", "rate_per_minute", "unit",
                "valid_from", "valid_to", "source_confirmation", "scenario_id",
                "is_simulated"]
        cols = [c for c in cols if c in data]
        sql = (
            "INSERT INTO production.capacity_profiles (" + ", ".join(cols)
            + ") VALUES (" + ", ".join(f"%({c})s" for c in cols) + ") RETURNING *"
        )
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, data)
            row = cur.fetchone()
            conn.commit()
        return row

    @_db_errors
    def capacity_for(self, process_id, machine_id, product_id, at_time):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM production.capacity_profiles "
                "WHERE (%(process_id)s::bigint IS NULL OR process_id = %(process_id)s) "
                "AND (%(machine_id)s::bigint IS NULL OR machine_id = %(machine_id)s) "
                "AND (%(product_id)s::bigint IS NULL OR product_id = %(product_id)s) "
                "AND valid_from <= %(at)s AND (valid_to IS NULL OR valid_to >= %(at)s) "
                "ORDER BY id DESC LIMIT 1",
                {"process_id": process_id, "machine_id": machine_id,
                 "product_id": product_id, "at": at_time},
            )
            return cur.fetchone()

    # ---- source_object_mappings ----
    @_db_errors
    def list_mappings(self, page, page_size):
        params = {"limit": page_size, "offset": (page - 1) * page_size}
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM production.source_object_mappings")
            total = cur.fetchone()["total"]
            cur.execute(
                "SELECT * FROM production.source_object_mappings "
                "ORDER BY id DESC LIMIT %(limit)s OFFSET %(offset)s",
                params,
            )
            return cur.fetchall(), total

    @_db_errors
    def create_mapping(self, data):
        cols = ["source_id", "object_type", "source_code", "node_id", "valid_from",
                "valid_to", "confirmed", "scenario_id", "is_simulated"]
        cols = [c for c in cols if c in data]
        sql = (
            "INSERT INTO production.source_object_mappings (" + ", ".join(cols)
            + ") VALUES (" + ", ".join(f"%({c})s" for c in cols) + ") RETURNING *"
        )
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, data)
            row = cur.fetchone()
            conn.commit()
        return row

    @_db_errors
    def resolve_mapping(self, source_id, object_type, source_code):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT node_id FROM production.source_object_mappings "
                "WHERE source_id = %(source_id)s AND object_type = %(object_type)s "
                "AND source_code = %(source_code)s ORDER BY id DESC LIMIT 1",
                {"source_id": source_id, "object_type": object_type,
                 "source_code": source_code},
            )
            row = cur.fetchone()
            return row["node_id"] if row else None

    # ---- ingestion_records ----
    @_db_errors
    def list_ingestions(self, page, page_size, status=None):
        conds, params = [], {"limit": page_size, "offset": (page - 1) * page_size}
        if status:
            conds.append("status = %(status)s")
            params["status"] = status
        where = (" WHERE " + " AND ".join(conds)) if conds else ""
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                f"SELECT COUNT(*) AS total FROM production.ingestion_records{where}",
                params,
            )
            total = cur.fetchone()["total"]
            cur.execute(
                f"SELECT * FROM production.ingestion_records{where} "
                "ORDER BY id DESC LIMIT %(limit)s OFFSET %(offset)s",
                params,
            )
            return cur.fetchall(), total

    @_db_errors
    def create_ingestion(self, data):
        cols = ["source_id", "request_id", "event_time", "payload", "status", "error",
                "created_business_ids", "scenario_id", "is_simulated"]
        cols = [c for c in cols if c in data]
        params = {**data}
        if "payload" in params:
            params["payload"] = Jsonb(params["payload"] or {})
        if "created_business_ids" in params:
            params["created_business_ids"] = Jsonb(params["created_business_ids"] or [])
        sql = (
            "INSERT INTO production.ingestion_records (" + ", ".join(cols)
            + ") VALUES (" + ", ".join(f"%({c})s" for c in cols) + ") RETURNING *"
        )
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            conn.commit()
        return row

    # ---- users ----
    @_db_errors
    def list_users(self):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM production.users ORDER BY id")
            return cur.fetchall()

    @_db_errors
    def create_user(self, data):
        cols = ["username", "display_name", "role", "active", "is_simulated"]
        cols = [c for c in cols if c in data]
        sql = (
            "INSERT INTO production.users (" + ", ".join(cols)
            + ") VALUES (" + ", ".join(f"%({c})s" for c in cols) + ") RETURNING *"
        )
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, data)
            row = cur.fetchone()
            conn.commit()
        return row

    @_db_errors
    def find_user_by_username(self, username):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM production.users WHERE username = %(u)s", {"u": username}
            )
            return cur.fetchone()

    # ---- incident_experiences ----
    @_db_errors
    def list_experiences(self, page, page_size):
        params = {"limit": page_size, "offset": (page - 1) * page_size}
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM production.incident_experiences")
            total = cur.fetchone()["total"]
            cur.execute(
                "SELECT * FROM production.incident_experiences "
                "ORDER BY id DESC LIMIT %(limit)s OFFSET %(offset)s",
                params,
            )
            return cur.fetchall(), total

    @_db_errors
    def create_experience(self, data):
        cols = ["source_incident_id", "incident_type", "error_code", "machine_id",
                "process_id", "symptom", "root_cause", "actions", "result",
                "approved_by", "approved_at", "scenario_id", "is_simulated"]
        cols = [c for c in cols if c in data]
        sql = (
            "INSERT INTO production.incident_experiences (" + ", ".join(cols)
            + ") VALUES (" + ", ".join(f"%({c})s" for c in cols) + ") RETURNING *"
        )
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, data)
            row = cur.fetchone()
            conn.commit()
        return row

    @_db_errors
    def experiences_for_match(self):
        """Sự cố cũ có hồ sơ kinh nghiệm, dùng để đối chiếu sự cố tương tự."""
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT i.id, i.code, i.incident_type, e.machine_id, e.error_code "
                "FROM production.incident_experiences e "
                "JOIN production.incidents i ON i.id = e.source_incident_id "
                "ORDER BY i.id"
            )
            return cur.fetchall()

    # ---- incident_history ----
    @_db_errors
    def add_history(self, incident_id, action, changed_by=None, detail=None):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO production.incident_history "
                "(incident_id, action, changed_by, detail) "
                "VALUES (%(incident_id)s, %(action)s, %(changed_by)s, %(detail)s) RETURNING *",
                {"incident_id": incident_id, "action": action,
                 "changed_by": changed_by, "detail": Jsonb(detail or {})},
            )
            row = cur.fetchone()
            conn.commit()
        return row

    @_db_errors
    def list_history(self, incident_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM production.incident_history WHERE incident_id = %(id)s ORDER BY id",
                {"id": incident_id},
            )
            return cur.fetchall()

    # ---- incident_context_verifications ----
    @_db_errors
    def latest_verification(self, incident_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM production.incident_context_verifications "
                "WHERE incident_id = %(id)s ORDER BY id DESC LIMIT 1",
                {"id": incident_id},
            )
            return cur.fetchone()

    @_db_errors
    def list_verifications(self, incident_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM production.incident_context_verifications "
                "WHERE incident_id = %(id)s ORDER BY id",
                {"id": incident_id},
            )
            return cur.fetchall()

    @_db_errors
    def create_verification(self, data):
        cols = ["incident_id", "operation_ids", "status", "decided_by", "reason",
                "evidence", "candidate_snapshot"]
        cols = [c for c in cols if c in data]
        params = {**data}
        for j in ("operation_ids", "candidate_snapshot"):
            if j in params:
                params[j] = Jsonb(params[j] or [])
        sql = (
            "INSERT INTO production.incident_context_verifications (" + ", ".join(cols)
            + ") VALUES (" + ", ".join(f"%({c})s" for c in cols) + ") RETURNING *"
        )
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            conn.commit()
        return row
