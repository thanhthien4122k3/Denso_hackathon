"""Thực thi SQL cho bảng production.production_records."""

import functools

from psycopg import OperationalError
from psycopg.errors import UniqueViolation

from app.database import get_connection
from app.exceptions import DatabaseUnavailableError, DuplicateRequestError
from app.query_loader import get_database_queries, get_production_queries


def db_errors(func):
    """Chuyển lỗi kết nối PostgreSQL thành DatabaseUnavailableError."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except OperationalError as exc:
            raise DatabaseUnavailableError(str(exc)) from exc

    return wrapper


class ProductionRepository:
    def __init__(self, settings=None):
        self._settings = settings

    def _connect(self):
        return get_connection(self._settings)

    @db_errors
    def init_schema(self) -> None:
        queries = get_database_queries()
        names = (
            "create_schema",
            "create_table",
            "index_production_date",
            "index_lot_code",
        )
        with self._connect() as conn, conn.cursor() as cur:
            for name in names:
                cur.execute(queries[name]["sql"])
            conn.commit()

    @db_errors
    def insert(self, params: dict) -> dict:
        query = get_production_queries()["insert_record"]
        try:
            with self._connect() as conn, conn.cursor() as cur:
                cur.execute(query["sql"], params)
                row = cur.fetchone()
                conn.commit()
            return row
        except UniqueViolation as exc:
            raise DuplicateRequestError() from exc

    @db_errors
    def find_by_request_id(self, request_id) -> dict | None:
        query = get_production_queries()["find_by_request_id"]
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(query["sql"], {"request_id": request_id})
            return cur.fetchone()

    @db_errors
    def find_by_id(self, record_id: int) -> dict | None:
        query = get_production_queries()["find_by_id"]
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(query["sql"], {"id": record_id})
            return cur.fetchone()

    @db_errors
    def list_records(
        self,
        date_from=None,
        date_to=None,
        line_code=None,
        lot_code=None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        query = get_production_queries()["list_records"]
        params = {
            "date_from": date_from,
            "date_to": date_to,
            "line_code": line_code,
            "lot_code": lot_code,
            "page_size": limit,
            "offset": offset,
        }
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(query["sql"], params)
            return cur.fetchall()

    @db_errors
    def count_records(
        self, date_from=None, date_to=None, line_code=None, lot_code=None
    ) -> int:
        query = get_production_queries()["count_records"]
        params = {
            "date_from": date_from,
            "date_to": date_to,
            "line_code": line_code,
            "lot_code": lot_code,
        }
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(query["sql"], params)
            row = cur.fetchone()
            return row["total"] if row else 0

    @db_errors
    def health_check(self) -> bool:
        query = get_production_queries()["health_check"]
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(query["sql"])
            cur.fetchone()
        return True
