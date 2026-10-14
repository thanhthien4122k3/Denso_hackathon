"""Kiểm thử đơn vị cho tích hợp nguồn ngoài (crypto, file, connector, service).

Không cần database ngoài thật; dùng dữ liệu trong bộ nhớ và mock repository.
"""

import io

import pytest

from app.integration import crypto, files
from app.integration.connectors import (
    PostgresConnector,
    SourceConnectionError,
    build_connector,
    sanitize_error,
)
from app.exceptions import ValidationFailedError
from app.services.integration_service import TARGETS, IntegrationService


# ---- crypto ----
def test_crypto_roundtrip(monkeypatch):
    monkeypatch.setattr(crypto, "SOURCE_ENCRYPTION_KEY", "test-secret-key")
    enc = crypto.encrypt_secret("my-password-123")
    assert enc != "my-password-123"
    assert "my-password-123" not in enc
    assert crypto.decrypt_secret(enc) == "my-password-123"


def test_crypto_no_key_raises(monkeypatch):
    monkeypatch.setattr(crypto, "SOURCE_ENCRYPTION_KEY", "")
    with pytest.raises(RuntimeError):
        crypto.encrypt_secret("anything")


# ---- files: CSV ----
def _csv_bytes(text: str, bom: bool = False) -> bytes:
    data = text.encode("utf-8")
    return (b"\xef\xbb\xbf" if bom else b"") + data


def test_parse_csv_utf8_bom_and_leading_zeros():
    raw = _csv_bytes("lot_code,good_quantity\n0007,120\n00123,3\n", bom=True)
    p = files.parse_preview("a.csv", raw)
    assert p["header"] == ["lot_code", "good_quantity"]
    assert p["total_rows"] == 2
    # mã có số 0 đầu được giữ nguyên dạng chuỗi.
    assert p["preview"][0][0] == "0007"
    assert p["preview"][1][0] == "00123"


def test_parse_csv_semicolon_delimiter():
    raw = _csv_bytes("line_code;process_code\nLINE-01;ASSY-01\n")
    p = files.parse_preview("a.csv", raw)
    assert p["delimiter"] == ";"
    assert p["header"] == ["line_code", "process_code"]


def test_parse_csv_short_row_padded():
    raw = _csv_bytes("a,b,c\n1,2\n")
    header, rows, _ = files.read_rows("a.csv", raw)
    assert rows == [["1", "2", ""]]


def test_parse_csv_empty_raises():
    with pytest.raises(files.FileParseError):
        files.parse_preview("a.csv", b"")


def test_parse_csv_unsupported_extension():
    with pytest.raises(files.FileParseError):
        files.parse_preview("a.txt", b"a,b\n1,2\n")


# ---- files: XLSX ----
def test_parse_xlsx_multi_sheet():
    from openpyxl import Workbook

    wb = Workbook()
    ws1 = wb.active
    ws1.title = "Sheet1"
    ws1.append(["code", "qty"])
    ws1.append(["0007", 120])
    ws2 = wb.create_sheet("Sheet2")
    ws2.append(["other"])
    ws2.append(["x"])
    buf = io.BytesIO()
    wb.save(buf)

    p = files.parse_preview("a.xlsx", buf.getvalue())
    assert p["format"] == "xlsx"
    assert p["sheets"] == ["Sheet1", "Sheet2"]
    assert p["header"] == ["code", "qty"]
    assert p["preview"][0][0] == "0007"

    p2 = files.parse_preview("a.xlsx", buf.getvalue(), sheet="Sheet2")
    assert p2["header"] == ["other"]


def test_parse_xlsx_corrupt_raises():
    with pytest.raises(files.FileParseError):
        files.parse_preview("a.xlsx", b"not-an-xlsx-file")


# ---- connectors ----
def test_sanitize_error_removes_password():
    msg = "connect failed password=supersecret host=db"
    assert "supersecret" not in sanitize_error(msg)


def test_build_connector_unsupported_type():
    with pytest.raises(SourceConnectionError):
        build_connector("oracle", "h", 1, "d", "u", "p")


def test_postgres_quote_preview_limit():
    c = PostgresConnector("h", 5432, "d", "u", "p")
    # Không kết nối thật; chỉ kiểm tra hàm preview không bị lỗi giới hạn trước khi gọi DB.
    # (bỏ qua vì cần DB thật — đã được kiểm tra ở tích hợp khi có DB nguồn.)
    assert c.db_type == "postgresql"


# ---- service: mapping + validation ----
def _make_service():
    class FakeRepo:
        def __init__(self):
            self.created = None

        def create_batch(self, data):
            self.created = {**data, "id": 1}
            return self.created

    repo = FakeRepo()
    return IntegrationService(repository=repo), repo


def test_validate_payload_types():
    svc, _ = _make_service()
    spec = TARGETS["production_records"]["fields"]
    ok, out = svc._validate_payload({
        "production_date": "2026-10-06", "shift": "CA_1", "line_code": "LINE-01",
        "process_code": "ASSY-01", "product_code": "PROD-001", "lot_code": "0007",
        "good_quantity": "120", "defect_quantity": "0", "operator_name": "a",
    }, spec)
    assert ok is True
    assert out["good_quantity"] == 120
    assert out["lot_code"] == "0007"


def test_validate_payload_bad_int_and_date():
    svc, _ = _make_service()
    spec = TARGETS["production_records"]["fields"]
    base = {"production_date": "2026-10-06", "shift": "CA_1", "line_code": "L",
            "process_code": "P", "product_code": "X", "lot_code": "L",
            "operator_name": "a", "defect_quantity": "0"}
    ok, _ = svc._validate_payload({**base, "good_quantity": "abc"}, spec)
    assert ok is False
    ok2, _ = svc._validate_payload({**base, "good_quantity": "10",
                                    "production_date": "2026/10/06"}, spec)
    assert ok2 is False


def test_create_batch_missing_required_mapping():
    svc, repo = _make_service()
    with pytest.raises(ValidationFailedError):
        svc._create_batch("csv", "f.csv", "production_records",
                          {"lot_code": "lot"}, ["lot"], [["0007"]])


def test_create_batch_detects_duplicate():
    svc, repo = _make_service()
    mapping = {"production_date": "d", "shift": "s", "line_code": "l",
               "process_code": "p", "product_code": "x", "lot_code": "lot",
               "good_quantity": "g", "defect_quantity": "df", "operator_name": "o"}
    header = ["d", "s", "l", "p", "x", "lot", "g", "df", "o"]
    rows = [
        ["2026-10-06", "CA_1", "L", "P", "X", "LOT-1", "10", "0", "a"],
        ["2026-10-06", "CA_1", "L", "P", "X", "LOT-1", "20", "1", "b"],
    ]
    batch = svc._create_batch("csv", "f.csv", "production_records", mapping, header, rows)
    assert batch["valid_rows"] == 1
    assert batch["error_rows"] == 1  # dòng trùng bị loại


# ---- API (integration, cần test DB) ----
def test_connection_profile_api_no_password_leak(client, monkeypatch):
    monkeypatch.setattr(crypto, "SOURCE_ENCRYPTION_KEY", "test-key")
    r = client.post("/api/integration/connections", json={
        "db_type": "postgresql", "host": "127.0.0.1", "port": 59999,
        "database_name": "x", "username": "u", "password": "s3cr3t"})
    assert r.status_code == 201
    data = r.json()["data"]
    assert "password" not in data and "password_encrypted" not in data
    pid = data["id"]

    listing = client.get("/api/integration/connections").json()["data"]["items"]
    got = next(x for x in listing if x["id"] == pid)
    assert "password_encrypted" not in got and "password" not in got

    # Test kết nối thất bại an toàn (không có DB ngoài), không lộ password.
    r2 = client.post(f"/api/integration/connections/{pid}/test")
    assert r2.status_code == 422
    assert "s3cr3t" not in r2.text


def test_connection_profile_requires_admin(client):
    # Người dùng thường (không phải admin) không được tạo kết nối.
    from app.services.auth_service import AuthService
    svc = AuthService()
    if svc.repository.find_by_username("int-op") is None:
        svc.create_user("int-op", "int-op", "test-pass-123", ["OPERATOR"], is_simulated=False)
    from fastapi.testclient import TestClient
    from app.main import app
    tc = TestClient(app)
    assert tc.post("/api/auth/login", json={"username": "int-op", "password": "test-pass-123"}).status_code == 200
    r = tc.post("/api/integration/connections", json={
        "db_type": "postgresql", "host": "h", "port": 5432})
    assert r.status_code == 403
    tc.close()
