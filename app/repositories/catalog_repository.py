"""Repository CRUD chung cho các danh mục nghiệp vụ.

Tên bảng/cột được lấy từ metadata cố định trong app.catalog (không phải dữ liệu
người dùng). Giá trị người dùng luôn được bind qua %(name)s. Không cho xóa vật lý,
chỉ "ngừng sử dụng" (active = false) để giữ toàn vẹn dữ liệu.
"""

from psycopg import OperationalError
from psycopg.errors import UniqueViolation

from app.catalog import all_fields, get_entity
from app.database import get_connection
from app.exceptions import DatabaseUnavailableError, DuplicateCodeError


def _identifier(name: str):
    return '"' + name.replace('"', '""') + '"'


def _table(key: str) -> str:
    return f"production.{_identifier(get_entity(key).table)}"


def _column_names(key: str) -> list[str]:
    return list(all_fields(get_entity(key)).keys())


def _build_select(key: str) -> str:
    cols = ", ".join(_identifier(c) for c in _column_names(key))
    return f"SELECT id, {cols}, created_at, updated_at FROM {_table(key)}"


def _db_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except UniqueViolation as exc:
            raise DuplicateCodeError() from exc
        except OperationalError as exc:
            raise DatabaseUnavailableError(str(exc)) from exc

    wrapper.__name__ = func.__name__
    return wrapper


class CatalogRepository:
    def __init__(self, settings=None):
        self._settings = settings

    def _conn(self):
        return get_connection(self._settings)

    @_db_errors
    def exists(self, key: str, record_id: int) -> bool:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT 1 FROM {_table(key)} WHERE id = %(id)s", {"id": record_id})
            return cur.fetchone() is not None

    @_db_errors
    def list(self, key: str, page: int, page_size: int, search: str | None, active: bool | None):
        conditions = []
        params = {"limit": page_size, "offset": (page - 1) * page_size}
        if active is not None:
            conditions.append("active = %(active)s")
            params["active"] = active
        if search:
            conditions.append("(code ILIKE %(search)s OR name ILIKE %(search)s)")
            params["search"] = f"%{search}%"
        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""

        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                f"SELECT COUNT(*) AS total FROM {_table(key)}{where}",
                params,
            )
            total = cur.fetchone()["total"]
            cur.execute(
                f"{_build_select(key)}{where} ORDER BY id DESC LIMIT %(limit)s OFFSET %(offset)s",
                params,
            )
            rows = cur.fetchall()
        return rows, total

    @_db_errors
    def get(self, key: str, record_id: int):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(f"{_build_select(key)} WHERE id = %(id)s", {"id": record_id})
            return cur.fetchone()

    @_db_errors
    def find_by_code(self, key: str, code: str):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(f"{_build_select(key)} WHERE code = %(code)s", {"code": code})
            return cur.fetchone()

    @_db_errors
    def create(self, key: str, data: dict) -> dict:
        cols = [c for c in _column_names(key) if c in data]
        names = ", ".join(_identifier(c) for c in cols)
        placeholders = ", ".join(f"%({c})s" for c in cols)
        sql = f"INSERT INTO {_table(key)} ({names}) VALUES ({placeholders}) RETURNING *"
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, data)
            row = cur.fetchone()
            conn.commit()
        return row

    @_db_errors
    def update(self, key: str, record_id: int, data: dict) -> dict | None:
        cols = [c for c in _column_names(key) if c in data]
        if not cols:
            return self.get(key, record_id)
        assignments = ", ".join(f"{_identifier(c)} = %({c})s" for c in cols)
        sql = (
            f"UPDATE {_table(key)} SET {assignments}, updated_at = CURRENT_TIMESTAMP "
            "WHERE id = %(id)s RETURNING *"
        )
        params = {**data, "id": record_id}
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            conn.commit()
        return row

    @_db_errors
    def deactivate(self, key: str, record_id: int) -> dict | None:
        sql = (
            f"UPDATE {_table(key)} SET active = FALSE, updated_at = CURRENT_TIMESTAMP "
            "WHERE id = %(id)s RETURNING *"
        )
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, {"id": record_id})
            row = cur.fetchone()
            conn.commit()
        return row

    @_db_errors
    def reference_count(self, key: str, record_id: int) -> int:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS total FROM production.graph_edges "
                "WHERE (source_type = %(t)s AND source_id = %(id)s) "
                "OR (target_type = %(t)s AND target_id = %(id)s)",
                {"t": key, "id": record_id},
            )
            return cur.fetchone()["total"]
