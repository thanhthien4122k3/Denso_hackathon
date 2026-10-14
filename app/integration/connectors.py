"""Adapter Ä‘á»c dá»¯ liá»‡u tá»« database nguá»“n bÃªn ngoÃ i (CHá»ˆ Äá»ŒC).

Má»i truy váº¥n Ä‘á»u do backend xÃ¢y dá»±ng tá»« tÃªn schema/báº£ng/cá»™t Ä‘Ã£ Ä‘Æ°á»£c quote Ä‘Ãºng
theo dialect; khÃ´ng cho ngÆ°á»i dÃ¹ng cháº¡y SQL tÃ¹y Ã½. KhÃ´ng cÃ³ thao tÃ¡c ghi nÃ o.
"""

from __future__ import annotations

import re

PREVIEW_LIMIT = 100
MAX_READ_ROWS = 50000
CONNECT_TIMEOUT = 8

SUPPORTED_DB_TYPES = ("postgresql", "mysql", "mssql")


class SourceConnectionError(Exception):
    """Lá»—i káº¿t ná»‘i/Ä‘á»c dá»¯ liá»‡u nguá»“n (Ä‘Ã£ lÃ m sáº¡ch, khÃ´ng chá»©a credentials)."""


def sanitize_error(message: str | None) -> str:
    if not message:
        return ""
    msg = str(message)
    msg = re.sub(r"(?i)(password|pwd|passwd)\s*=\s*[^\s;,]+", r"\1=***", msg)
    msg = re.sub(r"(?i)(://[^/@:\s]+):[^/@\s]+@", r"\1:***@", msg)
    return msg[:500]


def _quote_pg(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _quote_mysql(name: str) -> str:
    return "`" + name.replace("`", "``") + "`"


def _quote_mssql(name: str) -> str:
    return "[" + name.replace("]", "]]") + "]"


class BaseConnector:
    db_type = "unknown"

    def test(self) -> dict:
        raise NotImplementedError

    def schemas(self) -> list[str]:
        raise NotImplementedError

    def tables(self, schema: str) -> list[str]:
        raise NotImplementedError

    def columns(self, schema: str, table: str) -> list[dict]:
        raise NotImplementedError

    def preview(self, schema: str, table: str, columns: list[str] | None,
                limit: int = PREVIEW_LIMIT) -> dict:
        raise NotImplementedError


class PostgresConnector(BaseConnector):
    db_type = "postgresql"

    def __init__(self, host, port, database, username, password, ssl_mode=None, options=None):
        self._host = host
        self._port = port or 5432
        self._database = database
        self._username = username
        self._password = password
        self._ssl_mode = ssl_mode or "prefer"
        self._options = options or {}

    def _connect(self):
        import psycopg
        from psycopg.rows import dict_row

        kwargs = dict(host=self._host, port=self._port, dbname=self._database,
                      user=self._username, password=self._password,
                      connect_timeout=CONNECT_TIMEOUT)
        if self._ssl_mode:
            kwargs["sslmode"] = self._ssl_mode
        return psycopg.connect(**kwargs, row_factory=dict_row)

    def test(self) -> dict:
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT version() AS v")
                    cur.fetchone()
            return {"ok": True, "db_type": self.db_type,
                    "message": "Káº¿t ná»‘i thÃ nh cÃ´ng (PostgreSQL)."}
        except Exception as exc:  # noqa: BLE001
            raise SourceConnectionError(sanitize_error(exc)) from exc

    def schemas(self) -> list[str]:
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT schema_name FROM information_schema.schemata "
                        "WHERE schema_name NOT IN ('pg_catalog','information_schema') "
                        "AND schema_name NOT LIKE 'pg_%' ORDER BY schema_name"
                    )
                    return [r["schema_name"] for r in cur.fetchall()]
        except Exception as exc:  # noqa: BLE001
            raise SourceConnectionError(sanitize_error(exc)) from exc

    def tables(self, schema: str) -> list[str]:
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = %(s)s AND table_type IN ('BASE TABLE','VIEW') "
                        "ORDER BY table_name", {"s": schema})
                    return [r["table_name"] for r in cur.fetchall()]
        except Exception as exc:  # noqa: BLE001
            raise SourceConnectionError(sanitize_error(exc)) from exc

    def columns(self, schema: str, table: str) -> list[dict]:
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT column_name, data_type, is_nullable "
                        "FROM information_schema.columns "
                        "WHERE table_schema = %(s)s AND table_name = %(t)s "
                        "ORDER BY ordinal_position", {"s": schema, "t": table})
                    return [{"name": r["column_name"], "data_type": r["data_type"],
                             "nullable": r["is_nullable"] == "YES"} for r in cur.fetchall()]
        except Exception as exc:  # noqa: BLE001
            raise SourceConnectionError(sanitize_error(exc)) from exc

    def preview(self, schema, table, columns=None, limit=PREVIEW_LIMIT):
        limit = max(1, min(int(limit), MAX_READ_ROWS))
        cols = self.columns(schema, table)
        names = [c["name"] for c in cols]
        if columns:
            selected = [c for c in columns if c in names]
        else:
            selected = names
        if not selected:
            selected = names
        projection = ", ".join(_quote_pg(c) for c in selected)
        sql = f"SELECT {projection} FROM {_quote_pg(schema)}.{_quote_pg(table)} LIMIT {limit}"
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql)
                    rows = cur.fetchall()
            return {"columns": selected,
                    "rows": [[row[c] for c in selected] for row in rows]}
        except Exception as exc:  # noqa: BLE001
            raise SourceConnectionError(sanitize_error(exc)) from exc


class MySQLConnector(BaseConnector):
    db_type = "mysql"

    def __init__(self, host, port, database, username, password, ssl_mode=None, options=None):
        self._host = host
        self._port = port or 3306
        self._database = database
        self._username = username
        self._password = password
        self._ssl_mode = ssl_mode
        self._options = options or {}

    def _connect(self):
        try:
            import pymysql
        except ImportError as exc:  # noqa: BLE001
            raise SourceConnectionError(
                "Thiáº¿u driver MySQL/MariaDB. CÃ i báº±ng: pip install pymysql") from exc
        kwargs = dict(host=self._host, port=self._port, user=self._username,
                      password=self._password, database=self._database,
                      connect_timeout=CONNECT_TIMEOUT, cursorclass=pymysql.cursors.DictCursor)
        return pymysql.connect(**kwargs)

    def _query(self, sql, args=None):
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, args or ())
                return cur.fetchall()
        finally:
            conn.close()

    def test(self):
        try:
            self._query("SELECT 1 AS ok")
            return {"ok": True, "db_type": self.db_type, "message": "Káº¿t ná»‘i thÃ nh cÃ´ng (MySQL/MariaDB)."}
        except SourceConnectionError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise SourceConnectionError(sanitize_error(exc)) from exc

    def schemas(self):
        try:
            rows = self._query(
                "SELECT schema_name AS schema_name FROM information_schema.schemata "
                "WHERE schema_name NOT IN ('information_schema','mysql','performance_schema','sys') "
                "ORDER BY schema_name")
            return [r["schema_name"] for r in rows]
        except SourceConnectionError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise SourceConnectionError(sanitize_error(exc)) from exc

    def tables(self, schema):
        try:
            rows = self._query(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = %s ORDER BY table_name", (schema,))
            return [r["table_name"] for r in rows]
        except SourceConnectionError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise SourceConnectionError(sanitize_error(exc)) from exc

    def columns(self, schema, table):
        try:
            rows = self._query(
                "SELECT column_name, data_type, is_nullable FROM information_schema.columns "
                "WHERE table_schema = %s AND table_name = %s ORDER BY ordinal_position",
                (schema, table))
            return [{"name": r["column_name"], "data_type": r["data_type"],
                     "nullable": r["is_nullable"] == "YES"} for r in rows]
        except SourceConnectionError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise SourceConnectionError(sanitize_error(exc)) from exc

    def preview(self, schema, table, columns=None, limit=PREVIEW_LIMIT):
        limit = max(1, min(int(limit), MAX_READ_ROWS))
        cols = self.columns(schema, table)
        names = [c["name"] for c in cols]
        selected = [c for c in (columns or []) if c in names] or names
        projection = ", ".join(_quote_mysql(c) for c in selected)
        sql = f"SELECT {projection} FROM {_quote_mysql(schema)}.{_quote_mysql(table)} LIMIT {limit}"
        try:
            rows = self._query(sql)
            return {"columns": selected,
                    "rows": [[r[c] for c in selected] for r in rows]}
        except SourceConnectionError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise SourceConnectionError(sanitize_error(exc)) from exc


class MSSQLConnector(BaseConnector):
    db_type = "mssql"

    def __init__(self, host, port, database, username, password, ssl_mode=None, options=None):
        self._host = host
        self._port = port or 1433
        self._database = database
        self._username = username
        self._password = password
        self._ssl_mode = ssl_mode
        self._options = options or {}

    def _connect(self):
        try:
            import pyodbc
        except ImportError as exc:  # noqa: BLE001
            raise SourceConnectionError(
                "Thiáº¿u driver SQL Server. CÃ i Microsoft ODBC Driver 18 for SQL Server "
                "vÃ  thÆ° viá»‡n: pip install pyodbc") from exc
        driver = self._options.get("driver") or "ODBC Driver 18 for SQL Server"
        conn_str = (
            f"DRIVER={{{driver}}};SERVER={self._host},{self._port};"
            f"DATABASE={self._database};UID={self._username};PWD={self._password};"
            f"Encrypt={'yes' if (self._ssl_mode or '') in ('require', 'yes') else 'no'};"
            "TrustServerCertificate=yes;Timeout=8"
        )
        try:
            return pyodbc.connect(conn_str, timeout=CONNECT_TIMEOUT)
        except Exception as exc:  # noqa: BLE001
            raise SourceConnectionError(sanitize_error(exc)) from exc

    def _query(self, sql, args=None):
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, args or ())
            cols = [c[0] for c in cur.description]
            rows = [dict(zip(cols, row)) for row in cur.fetchall()]
            return rows
        finally:
            conn.close()

    def test(self):
        try:
            self._query("SELECT 1 AS ok")
            return {"ok": True, "db_type": self.db_type, "message": "Káº¿t ná»‘i thÃ nh cÃ´ng (SQL Server)."}
        except SourceConnectionError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise SourceConnectionError(sanitize_error(exc)) from exc

    def schemas(self):
        try:
            rows = self._query("SELECT name AS schema_name FROM sys.schemas "
                               "WHERE name NOT IN ('sys','INFORMATION_SCHEMA') ORDER BY name")
            return [r["schema_name"] for r in rows]
        except SourceConnectionError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise SourceConnectionError(sanitize_error(exc)) from exc

    def tables(self, schema):
        try:
            rows = self._query(
                "SELECT table_name FROM INFORMATION_SCHEMA.TABLES "
                "WHERE table_schema = ? AND table_type IN ('BASE TABLE','VIEW') "
                "ORDER BY table_name", (schema,))
            return [r["table_name"] for r in rows]
        except SourceConnectionError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise SourceConnectionError(sanitize_error(exc)) from exc

    def columns(self, schema, table):
        try:
            rows = self._query(
                "SELECT column_name, data_type, is_nullable FROM INFORMATION_SCHEMA.COLUMNS "
                "WHERE table_schema = ? AND table_name = ? ORDER BY ordinal_position",
                (schema, table))
            return [{"name": r["column_name"], "data_type": r["data_type"],
                     "nullable": r["is_nullable"] == "YES"} for r in rows]
        except SourceConnectionError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise SourceConnectionError(sanitize_error(exc)) from exc

    def preview(self, schema, table, columns=None, limit=PREVIEW_LIMIT):
        limit = max(1, min(int(limit), MAX_READ_ROWS))
        cols = self.columns(schema, table)
        names = [c["name"] for c in cols]
        selected = [c for c in (columns or []) if c in names] or names
        projection = ", ".join(_quote_mssql(c) for c in selected)
        sql = (f"SELECT TOP {limit} {projection} FROM {_quote_mssql(schema)}.{_quote_mssql(table)}")
        try:
            rows = self._query(sql)
            return {"columns": selected,
                    "rows": [[r[c] for c in selected] for r in rows]}
        except SourceConnectionError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise SourceConnectionError(sanitize_error(exc)) from exc


def build_connector(db_type, host, port, database, username, password,
                    ssl_mode=None, options=None):
    if db_type == "postgresql":
        return PostgresConnector(host, port, database, username, password, ssl_mode, options)
    if db_type == "mysql":
        return MySQLConnector(host, port, database, username, password, ssl_mode, options)
    if db_type == "mssql":
        return MSSQLConnector(host, port, database, username, password, ssl_mode, options)
    raise SourceConnectionError(f"Loáº¡i database khÃ´ng Ä‘Æ°á»£c há»— trá»£: {db_type}.")
