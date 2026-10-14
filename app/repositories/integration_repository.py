"""Repository cho connection profile và batch nhập dữ liệu (staging)."""

from psycopg import OperationalError
from psycopg.errors import ForeignKeyViolation
from psycopg.types.json import Jsonb

from app.database import get_connection
from app.exceptions import DatabaseUnavailableError, NotFoundError

_PROFILE_COLS = [
    "source_id", "db_type", "host", "port", "database_name", "username",
    "password_encrypted", "ssl_mode", "extra_options", "last_status",
    "last_checked_at", "last_error",
]

# Cột trả về cho client (không bao giờ chứa password_encrypted).
_PROFILE_PUBLIC = [
    "id", "source_id", "db_type", "host", "port", "database_name", "username",
    "ssl_mode", "extra_options", "last_status", "last_checked_at", "last_error",
    "created_at", "updated_at",
]

_BATCH_COLS = [
    "source_id", "connection_id", "dataset_id", "input_type", "source_name",
    "checksum", "target_type", "created_by", "total_rows", "valid_rows",
    "error_rows", "duplicate_rows", "imported_rows", "status", "error_summary",
    "mapping", "rows", "created_business_ids",
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


def _jsonb(params: dict, keys: tuple[str, ...]) -> dict:
    for k in keys:
        if k in params and params[k] is not None:
            params[k] = Jsonb(params[k])
    return params


class IntegrationRepository:
    def __init__(self, settings=None):
        self._settings = settings

    def _conn(self):
        return get_connection(self._settings)

    # ---- connection profiles ----
    @_db_errors
    def list_profiles(self, page, page_size):
        params = {"limit": page_size, "offset": (page - 1) * page_size}
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM production.source_connection_profiles")
            total = cur.fetchone()["total"]
            cur.execute(
                "SELECT " + ", ".join(_PROFILE_PUBLIC)
                + " FROM production.source_connection_profiles ORDER BY id DESC "
                "LIMIT %(limit)s OFFSET %(offset)s", params)
            return cur.fetchall(), total

    @_db_errors
    def get_profile(self, profile_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT " + ", ".join(_PROFILE_PUBLIC)
                + " FROM production.source_connection_profiles WHERE id = %(id)s",
                {"id": profile_id})
            return cur.fetchone()

    @_db_errors
    def get_profile_with_secret(self, profile_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM production.source_connection_profiles WHERE id = %(id)s",
                        {"id": profile_id})
            return cur.fetchone()

    @_db_errors
    def create_profile(self, data):
        cols = [c for c in _PROFILE_COLS if c in data]
        params = _jsonb({**data}, ("extra_options",))
        sql = ("INSERT INTO production.source_connection_profiles (" + ", ".join(cols)
               + ") VALUES (" + ", ".join(f"%({c})s" for c in cols) + ") RETURNING *")
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            conn.commit()
        return row

    @_db_errors
    def update_profile(self, profile_id, data):
        cols = [c for c in _PROFILE_COLS if c in data]
        if not cols:
            return self.get_profile(profile_id)
        params = _jsonb({**data, "id": profile_id}, ("extra_options",))
        assign = ", ".join(f"{c} = %({c})s" for c in cols)
        sql = (f"UPDATE production.source_connection_profiles SET {assign}, "
               "updated_at = CURRENT_TIMESTAMP WHERE id = %(id)s RETURNING *")
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            conn.commit()
        return row

    @_db_errors
    def delete_profile(self, profile_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM production.source_connection_profiles WHERE id = %(id)s",
                        {"id": profile_id})
            deleted = cur.rowcount > 0
            conn.commit()
        return deleted

    # ---- ingestion batches ----
    @_db_errors
    def create_batch(self, data):
        cols = [c for c in _BATCH_COLS if c in data]
        params = _jsonb({**data}, ("error_summary", "mapping", "rows", "created_business_ids"))
        sql = ("INSERT INTO production.ingestion_batches (" + ", ".join(cols)
               + ") VALUES (" + ", ".join(f"%({c})s" for c in cols) + ") RETURNING *")
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            conn.commit()
        return row

    @_db_errors
    def get_batch(self, batch_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM production.ingestion_batches WHERE id = %(id)s",
                        {"id": batch_id})
            return cur.fetchone()

    @_db_errors
    def list_batches(self, page, page_size):
        params = {"limit": page_size, "offset": (page - 1) * page_size}
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM production.ingestion_batches")
            total = cur.fetchone()["total"]
            cur.execute(
                "SELECT * FROM production.ingestion_batches ORDER BY id DESC "
                "LIMIT %(limit)s OFFSET %(offset)s", params)
            return cur.fetchall(), total

    @_db_errors
    def update_batch(self, batch_id, data):
        cols = [c for c in _BATCH_COLS if c in data]
        if not cols:
            return self.get_batch(batch_id)
        params = _jsonb({**data, "id": batch_id},
                        ("error_summary", "mapping", "rows", "created_business_ids"))
        assign = ", ".join(f"{c} = %({c})s" for c in cols)
        sql = (f"UPDATE production.ingestion_batches SET {assign}, "
               "updated_at = CURRENT_TIMESTAMP WHERE id = %(id)s RETURNING *")
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            conn.commit()
        return row
