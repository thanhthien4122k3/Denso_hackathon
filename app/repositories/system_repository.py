"""Repository cho lớp logic hệ thống: nguồn, dataset, trường, luồng dữ liệu."""

from psycopg import OperationalError
from psycopg.errors import ForeignKeyViolation

from app.database import get_connection
from app.exceptions import DatabaseUnavailableError, NotFoundError

_SOURCE_COLS = [
    "code", "name", "source_type", "collection_method", "owner_department_id",
    "location_metadata", "confirmed", "is_simulated",
]
_DATASET_COLS = [
    "code", "name", "source_id", "dataset_type", "storage_location",
    "collection_method", "owner_department_id", "generation_unit", "update_schedule",
    "event_time_field", "timezone", "update_frequency", "expected_latency",
    "last_received_at", "confirmed", "is_simulated",
]
_FIELD_COLS = [
    "dataset_id", "code", "name", "description", "data_type", "is_key", "confirmed",
]
_FLOW_COLS = [
    "code", "name", "source_dataset_id", "target_dataset_id", "description",
    "confirmed", "is_simulated",
]


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


class SystemRepository:
    def __init__(self, settings=None):
        self._settings = settings

    def _conn(self):
        return get_connection(self._settings)

    # ---- data_sources ----
    @_db_errors
    def list_sources(self, page, page_size, search=None):
        params = {"limit": page_size, "offset": (page - 1) * page_size}
        where = ""
        if search:
            where = " WHERE code ILIKE %(search)s OR name ILIKE %(search)s"
            params["search"] = f"%{search}%"
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) AS total FROM production.data_sources{where}", params)
            total = cur.fetchone()["total"]
            cur.execute(
                f"SELECT * FROM production.data_sources{where} "
                "ORDER BY id DESC LIMIT %(limit)s OFFSET %(offset)s",
                params,
            )
            return cur.fetchall(), total

    @_db_errors
    def get_source(self, source_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM production.data_sources WHERE id = %(id)s", {"id": source_id})
            return cur.fetchone()

    @_db_errors
    def create_source(self, data):
        cols = [c for c in _SOURCE_COLS if c in data]
        sql = (
            "INSERT INTO production.data_sources ("
            + ", ".join(cols) + ") VALUES (" + ", ".join(f"%({c})s" for c in cols)
            + ") RETURNING *"
        )
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, data)
            row = cur.fetchone()
            conn.commit()
        return row

    @_db_errors
    def update_source(self, source_id, data):
        cols = [c for c in _SOURCE_COLS if c in data]
        if not cols:
            return self.get_source(source_id)
        assign = ", ".join(f"{c} = %({c})s" for c in cols)
        sql = (
            f"UPDATE production.data_sources SET {assign}, updated_at = CURRENT_TIMESTAMP "
            "WHERE id = %(id)s RETURNING *"
        )
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, {**data, "id": source_id})
            row = cur.fetchone()
            conn.commit()
        return row

    @_db_errors
    def source_dataset_count(self, source_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS total FROM production.datasets WHERE source_id = %(id)s",
                {"id": source_id},
            )
            return cur.fetchone()["total"]

    @_db_errors
    def delete_source(self, source_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM production.data_sources WHERE id = %(id)s", {"id": source_id})
            deleted = cur.rowcount > 0
            conn.commit()
        return deleted

    # ---- datasets ----
    @_db_errors
    def list_datasets(self, page, page_size, source_id=None, search=None):
        params = {"limit": page_size, "offset": (page - 1) * page_size}
        conds = []
        if source_id is not None:
            conds.append("source_id = %(source_id)s")
            params["source_id"] = source_id
        if search:
            conds.append("(code ILIKE %(search)s OR name ILIKE %(search)s)")
            params["search"] = f"%{search}%"
        where = (" WHERE " + " AND ".join(conds)) if conds else ""
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) AS total FROM production.datasets{where}", params)
            total = cur.fetchone()["total"]
            cur.execute(
                f"SELECT * FROM production.datasets{where} "
                "ORDER BY id DESC LIMIT %(limit)s OFFSET %(offset)s",
                params,
            )
            return cur.fetchall(), total

    @_db_errors
    def get_dataset(self, dataset_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM production.datasets WHERE id = %(id)s", {"id": dataset_id})
            return cur.fetchone()

    @_db_errors
    def create_dataset(self, data):
        cols = [c for c in _DATASET_COLS if c in data]
        sql = (
            "INSERT INTO production.datasets (" + ", ".join(cols)
            + ") VALUES (" + ", ".join(f"%({c})s" for c in cols) + ") RETURNING *"
        )
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, data)
            row = cur.fetchone()
            conn.commit()
        return row

    @_db_errors
    def update_dataset(self, dataset_id, data):
        cols = [c for c in _DATASET_COLS if c in data]
        if not cols:
            return self.get_dataset(dataset_id)
        assign = ", ".join(f"{c} = %({c})s" for c in cols)
        sql = (
            f"UPDATE production.datasets SET {assign}, updated_at = CURRENT_TIMESTAMP "
            "WHERE id = %(id)s RETURNING *"
        )
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, {**data, "id": dataset_id})
            row = cur.fetchone()
            conn.commit()
        return row

    @_db_errors
    def delete_dataset(self, dataset_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM production.datasets WHERE id = %(id)s", {"id": dataset_id})
            deleted = cur.rowcount > 0
            conn.commit()
        return deleted

    # ---- dataset_fields ----
    @_db_errors
    def list_fields(self, dataset_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM production.dataset_fields WHERE dataset_id = %(id)s ORDER BY id",
                {"id": dataset_id},
            )
            return cur.fetchall()

    @_db_errors
    def get_field(self, field_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM production.dataset_fields WHERE id = %(id)s", {"id": field_id})
            return cur.fetchone()

    @_db_errors
    def create_field(self, data):
        cols = [c for c in _FIELD_COLS if c in data]
        sql = (
            "INSERT INTO production.dataset_fields (" + ", ".join(cols)
            + ") VALUES (" + ", ".join(f"%({c})s" for c in cols) + ") RETURNING *"
        )
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, data)
            row = cur.fetchone()
            conn.commit()
        return row

    @_db_errors
    def update_field(self, field_id, data):
        cols = [c for c in _FIELD_COLS if c in data and c != "dataset_id"]
        if not cols:
            return self.get_field(field_id)
        assign = ", ".join(f"{c} = %({c})s" for c in cols)
        sql = f"UPDATE production.dataset_fields SET {assign} WHERE id = %(id)s RETURNING *"
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, {**data, "id": field_id})
            row = cur.fetchone()
            conn.commit()
        return row

    @_db_errors
    def delete_field(self, field_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "DELETE FROM production.graph_edges WHERE "
                "(source_type = 'field' AND source_id = %(id)s) "
                "OR (target_type = 'field' AND target_id = %(id)s)",
                {"id": field_id},
            )
            cur.execute("DELETE FROM production.dataset_fields WHERE id = %(id)s", {"id": field_id})
            deleted = cur.rowcount > 0
            conn.commit()
        return deleted

    # ---- data_flows ----
    @_db_errors
    def list_flows(self, page, page_size):
        params = {"limit": page_size, "offset": (page - 1) * page_size}
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM production.data_flows", params)
            total = cur.fetchone()["total"]
            cur.execute(
                "SELECT * FROM production.data_flows ORDER BY id DESC "
                "LIMIT %(limit)s OFFSET %(offset)s",
                params,
            )
            return cur.fetchall(), total

    @_db_errors
    def create_flow(self, data):
        cols = [c for c in _FLOW_COLS if c in data]
        sql = (
            "INSERT INTO production.data_flows (" + ", ".join(cols)
            + ") VALUES (" + ", ".join(f"%({c})s" for c in cols) + ") RETURNING *"
        )
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, data)
            row = cur.fetchone()
            conn.commit()
        return row

    @_db_errors
    def update_flow(self, flow_id, data):
        cols = [c for c in _FLOW_COLS if c in data and c != "code"]
        if not cols:
            return None
        assign = ", ".join(f"{c} = %({c})s" for c in cols)
        sql = f"UPDATE production.data_flows SET {assign} WHERE id = %(id)s RETURNING *"
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, {**data, "id": flow_id})
            row = cur.fetchone()
            conn.commit()
        return row

    @_db_errors
    def delete_flow(self, flow_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM production.data_flows WHERE id = %(id)s", {"id": flow_id})
            deleted = cur.rowcount > 0
            conn.commit()
        return deleted
