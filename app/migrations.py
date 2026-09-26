"""Migration có phiên bản, chạy có kiểm soát khi khởi động.

Mỗi file SQL trong thư mục migrations/ được đặt tên NNNN_name.sql, chạy một lần
theo thứ tự tăng dần và được ghi lại trong bảng schema_migrations. Nếu một
migration đã chạy mà nội dung file bị thay đổi, hoặc một migration lỗi giữa
chừng, ứng dụng dừng khởi động và báo lỗi rõ ràng.
"""

import hashlib
from pathlib import Path

from psycopg import OperationalError

from app.database import get_connection
from app.exceptions import DatabaseUnavailableError
from app.settings import MIGRATIONS_DIR


class MigrationError(RuntimeError):
    """Migration thất bại hoặc không nhất quán."""


def _ensure_table(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                checksum TEXT NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    conn.commit()


def _applied(conn) -> dict:
    with conn.cursor() as cur:
        cur.execute("SELECT version, checksum FROM schema_migrations")
        return {row["version"]: row["checksum"] for row in cur.fetchall()}


def _list_migrations() -> list[tuple[str, str, Path]]:
    result = []
    for path in MIGRATIONS_DIR.glob("*.sql"):
        version = path.stem.split("_", 1)[0]
        result.append((version, path.stem, path))
    result.sort(key=lambda item: item[0])
    return result


def run_migrations() -> list[str]:
    try:
        conn = get_connection()
    except OperationalError as exc:
        raise DatabaseUnavailableError(str(exc)) from exc

    applied_now: list[str] = []
    try:
        _ensure_table(conn)
        applied = _applied(conn)

        for version, name, path in _list_migrations():
            content = path.read_text(encoding="utf-8")
            checksum = hashlib.sha256(content.encode("utf-8")).hexdigest()

            if version in applied:
                if applied[version] != checksum:
                    raise MigrationError(
                        f"Migration {name} đã được áp dụng nhưng file đã thay đổi "
                        "(checksum khác). Không tiếp tục để tránh schema không nhất quán."
                    )
                continue

            try:
                with conn.cursor() as cur:
                    cur.execute(content)
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO schema_migrations (version, name, checksum) "
                        "VALUES (%(version)s, %(name)s, %(checksum)s)",
                        {"version": version, "name": name, "checksum": checksum},
                    )
                conn.commit()
            except Exception as exc:
                conn.rollback()
                raise MigrationError(f"Migration {name} thất bại: {exc}") from exc

            applied_now.append(name)
    finally:
        conn.close()

    return applied_now
