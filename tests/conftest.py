"""Fixtures dùng cho integration test.

Integration test chạy trên database test riêng (mặc định denso_hackathon_test),
KHÔNG đụng tới database thật. Nếu không kết nối/tạo được database test, các test
integration sẽ bị skip.
"""

import os

import psycopg
import pytest
from dotenv import load_dotenv

from app.settings import ENV_FILE, reset_settings

TEST_DB_NAME = os.environ.get("TEST_DB_NAME", "denso_hackathon_test")


def _base_params() -> dict:
    load_dotenv(ENV_FILE, override=False)
    return {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": int(os.environ.get("DB_PORT", "5432")),
        "user": os.environ.get("DB_USER", "postgres"),
        "password": os.environ.get("DB_PASSWORD", ""),
        "connect_timeout": 5,
    }


@pytest.fixture(scope="session")
def test_db():
    params = _base_params()
    try:
        admin = psycopg.connect(**{**params, "dbname": "postgres"}, autocommit=True)
    except Exception:
        pytest.skip("Không kết nối được PostgreSQL; bỏ qua integration test.")

    try:
        with admin.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM pg_database WHERE datname = %(name)s",
                {"name": TEST_DB_NAME},
            )
            if cur.fetchone() is None:
                cur.execute(
                    'CREATE DATABASE "{}"'.format(TEST_DB_NAME)
                )
    except Exception:
        admin.close()
        pytest.skip("Không tạo được database test; bỏ qua integration test.")
    finally:
        admin.close()

    return TEST_DB_NAME


@pytest.fixture(scope="session")
def client(test_db):
    params = _base_params()
    os.environ["DB_NAME"] = test_db
    os.environ.setdefault("DB_HOST", params["host"])
    os.environ.setdefault("DB_PORT", str(params["port"]))
    os.environ.setdefault("DB_USER", params["user"])
    os.environ.setdefault("DB_PASSWORD", params["password"])
    reset_settings()

    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        _ensure_admin(c)
        yield c


def _ensure_admin(client, username="admin", password="admin-test-password"):
    """Tạo tài khoản admin (nếu chưa có) và đăng nhập để mọi request có phiên hợp lệ."""
    from app.services.auth_service import AuthService

    svc = AuthService()
    if svc.repository.find_by_username(username) is None:
        svc.create_user(username, "Admin Test", password, ["ADMIN"], is_simulated=False)
    client.post("/api/auth/login", json={"username": username, "password": password})


@pytest.fixture(scope="session")
def login_as_admin():
    """Helper đăng nhập lại (dùng sau khi fixture truncate xóa user)."""
    return _ensure_admin
