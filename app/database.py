"""Quản lý kết nối PostgreSQL (Psycopg 3).

Không giữ một connection toàn cục dùng chung: mỗi thao tác mở một connection
mới và đóng ngay sau khi xong. Route dùng def (đồng bộ) nên FastAPI chạy trong
threadpool, không chặn event loop.
"""

import psycopg
from psycopg.rows import dict_row

from app.settings import Settings, get_settings


def connection_params(settings: Settings) -> dict:
    return {
        "host": settings.db_host,
        "port": settings.db_port,
        "dbname": settings.db_name,
        "user": settings.db_user,
        "password": settings.db_password,
        "connect_timeout": settings.db_connect_timeout,
    }


def get_connection(settings: Settings | None = None) -> psycopg.Connection:
    settings = settings or get_settings()
    return psycopg.connect(**connection_params(settings), row_factory=dict_row)
