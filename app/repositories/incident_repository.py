"""Repository quản lý sự cố, nguyên nhân và liên kết bản ghi vận hành."""

from psycopg import OperationalError
from psycopg.errors import ForeignKeyViolation, UniqueViolation

from app.database import get_connection
from app.exceptions import DatabaseUnavailableError, DuplicateCodeError, NotFoundError

_INCIDENT_COLS = [
    "code", "title", "incident_type", "source_object_type", "source_object_id",
    "start_time", "end_time", "severity", "description", "status",
    "assigned_department_id", "request_id", "is_simulated",
    "recovered_at", "recovered_by", "closed_at", "closed_by",
    "resolution_summary", "root_cause_status",
]


def _db_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except UniqueViolation as exc:
            raise DuplicateCodeError() from exc
        except ForeignKeyViolation as exc:
            raise NotFoundError("Đối tượng tham chiếu không tồn tại.") from exc
        except OperationalError as exc:
            raise DatabaseUnavailableError(str(exc)) from exc

    wrapper.__name__ = func.__name__
    return wrapper


class IncidentRepository:
    def __init__(self, settings=None):
        self._settings = settings

    def _conn(self):
        return get_connection(self._settings)

    @_db_errors
    def list(self, page, page_size, status=None, incident_type=None, search=None):
        conds, params = [], {"limit": page_size, "offset": (page - 1) * page_size}
        if status:
            conds.append("status = %(status)s")
            params["status"] = status
        if incident_type:
            conds.append("incident_type = %(incident_type)s")
            params["incident_type"] = incident_type
        if search:
            conds.append("(code ILIKE %(search)s OR title ILIKE %(search)s)")
            params["search"] = f"%{search}%"
        where = (" WHERE " + " AND ".join(conds)) if conds else ""
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) AS total FROM production.incidents{where}", params)
            total = cur.fetchone()["total"]
            cur.execute(
                f"SELECT * FROM production.incidents{where} "
                "ORDER BY id DESC LIMIT %(limit)s OFFSET %(offset)s",
                params,
            )
            return cur.fetchall(), total

    @_db_errors
    def get(self, incident_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM production.incidents WHERE id = %(id)s", {"id": incident_id})
            return cur.fetchone()

    @_db_errors
    def get_by_code(self, code):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM production.incidents WHERE code = %(code)s", {"code": code})
            return cur.fetchone()

    @_db_errors
    def get_by_request_id(self, request_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM production.incidents WHERE request_id = %(id)s",
                {"id": request_id},
            )
            return cur.fetchone()

    @_db_errors
    def create(self, data):
        cols = [c for c in _INCIDENT_COLS if c in data]
        sql = (
            "INSERT INTO production.incidents (" + ", ".join(cols)
            + ") VALUES (" + ", ".join(f"%({c})s" for c in cols) + ") RETURNING *"
        )
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, data)
            row = cur.fetchone()
            conn.commit()
        return row

    @_db_errors
    def update(self, incident_id, data):
        cols = [c for c in _INCIDENT_COLS if c in data and c not in ("request_id", "code")]
        if not cols:
            return self.get(incident_id)
        assign = ", ".join(f"{c} = %({c})s" for c in cols)
        sql = (
            f"UPDATE production.incidents SET {assign}, updated_at = CURRENT_TIMESTAMP "
            "WHERE id = %(id)s RETURNING *"
        )
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, {**data, "id": incident_id})
            row = cur.fetchone()
            conn.commit()
        return row

    # ---- causes ----
    @_db_errors
    def list_causes(self, incident_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM production.incident_causes WHERE incident_id = %(id)s ORDER BY id",
                {"id": incident_id},
            )
            return cur.fetchall()

    @_db_errors
    def create_cause(self, data):
        cols = ["incident_id", "content", "kind", "evidence", "rule_id", "priority",
                "confirmed_by", "confirmed_at"]
        cols = [c for c in cols if c in data]
        sql = (
            "INSERT INTO production.incident_causes (" + ", ".join(cols)
            + ") VALUES (" + ", ".join(f"%({c})s" for c in cols) + ") RETURNING *"
        )
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, data)
            row = cur.fetchone()
            conn.commit()
        return row

    @_db_errors
    def get_cause(self, cause_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM production.incident_causes WHERE id = %(id)s",
                {"id": cause_id},
            )
            return cur.fetchone()

    @_db_errors
    def update_cause(self, cause_id, data):
        cols = ["content", "kind", "evidence", "rule_id", "priority", "confirmed_by", "confirmed_at"]
        cols = [c for c in cols if c in data]
        if not cols:
            return None
        assign = ", ".join(f"{c} = %({c})s" for c in cols)
        sql = f"UPDATE production.incident_causes SET {assign} WHERE id = %(id)s RETURNING *"
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, {**data, "id": cause_id})
            row = cur.fetchone()
            conn.commit()
        return row

    @_db_errors
    def delete_cause(self, cause_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM production.incident_causes WHERE id = %(id)s", {"id": cause_id})
            deleted = cur.rowcount > 0
            conn.commit()
        return deleted

    # ---- links ----
    @_db_errors
    def list_links(self, incident_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM production.incident_links WHERE incident_id = %(id)s ORDER BY id",
                {"id": incident_id},
            )
            return cur.fetchall()

    @_db_errors
    def create_link(self, data):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO production.incident_links (incident_id, source_type, source_id) "
                "VALUES (%(incident_id)s, %(source_type)s, %(source_id)s) RETURNING *",
                data,
            )
            row = cur.fetchone()
            conn.commit()
        return row

    @_db_errors
    def delete_link(self, link_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM production.incident_links WHERE id = %(id)s", {"id": link_id})
            deleted = cur.rowcount > 0
            conn.commit()
        return deleted
