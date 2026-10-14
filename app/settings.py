"""Đọc và kiểm tra cấu hình ứng dụng từ biến môi trường (.env).

Đường dẫn file .env được tính từ vị trí file này, không phụ thuộc thư mục
terminal hiện tại.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

# Nạp .env vào os.environ ngay khi import để các hằng số điều chỉnh bên dưới
# có thể đọc từ .env (override=False: biến môi trường thật vẫn được ưu tiên).
load_dotenv(ENV_FILE, override=False)

# Các giá trị điều chỉnh của ứng dụng, có thể ghi đè qua .env (xem .env.example).
MAX_QUANTITY = int(os.getenv("MAX_QUANTITY", "1000000000"))
MATERIAL_LOW_THRESHOLD = int(os.getenv("MATERIAL_LOW_THRESHOLD", "50"))
QC_DEFECT_RATE_THRESHOLD = float(os.getenv("QC_DEFECT_RATE_THRESHOLD", "5"))
# Khóa mã hóa đối xứng cho mật khẩu nguồn bên ngoài (không lưu trong DB/repo).
SOURCE_ENCRYPTION_KEY = os.getenv("SOURCE_ENCRYPTION_KEY", "")
DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", "20"))
MAX_PAGE_SIZE = int(os.getenv("MAX_PAGE_SIZE", "100"))


def _path(name: str, default_rel: str) -> Path:
    """Đọc đường dẫn từ .env; mặc định tính tương đối với thư mục dự án."""
    raw = os.getenv(name, "").strip()
    if raw:
        path = Path(raw)
        return path if path.is_absolute() else (BASE_DIR / path)
    return BASE_DIR / default_rel


# Đường dẫn các file/thư mục, có thể ghi đè qua .env (xem .env.example).
DATABASE_YAML_PATH = _path("DATABASE_YAML_PATH", "config/database.yaml")
PRODUCTION_QUERIES_YAML_PATH = _path("PRODUCTION_QUERIES_YAML_PATH", "config/production_queries.yaml")
RULES_YAML_PATH = _path("RULES_YAML_PATH", "config/rules.yaml")
MIGRATIONS_DIR = _path("MIGRATIONS_DIR", "migrations")
STATIC_DIR = _path("STATIC_DIR", "app/static")


class ConfigError(ValueError):
    """Thiếu hoặc sai cấu hình trong .env."""


@dataclass(frozen=True)
class Settings:
    app_host: str
    app_port: int
    app_env: str
    app_timezone: str
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    db_connect_timeout: int

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv(ENV_FILE, override=False)

        def _int(name: str, default: str, low: int, high: int) -> int:
            raw = os.getenv(name, default).strip()
            try:
                value = int(raw)
            except ValueError:
                raise ConfigError(
                    f"{name} phải là số nguyên (nhận: {raw!r})."
                ) from None
            if not low <= value <= high:
                raise ConfigError(f"{name} phải nằm trong khoảng {low}-{high}.")
            return value

        def _required(name: str) -> str:
            value = os.getenv(name, "").strip()
            if not value:
                raise ConfigError(
                    f"Thiếu cấu hình bắt buộc: {name}. "
                    "Hãy tạo file .env từ .env.example."
                )
            return value

        return cls(
            app_host=os.getenv("APP_HOST", "0.0.0.0").strip() or "0.0.0.0",
            app_port=_int("APP_PORT", "8000", 1, 65535),
            app_env=os.getenv("APP_ENV", "development").strip() or "development",
            app_timezone=os.getenv("APP_TIMEZONE", "Asia/Ho_Chi_Minh").strip()
            or "Asia/Ho_Chi_Minh",
            db_host=_required("DB_HOST"),
            db_port=_int("DB_PORT", "5432", 1, 65535),
            db_name=_required("DB_NAME"),
            db_user=_required("DB_USER"),
            db_password=_required("DB_PASSWORD"),
            db_connect_timeout=_int("DB_CONNECT_TIMEOUT", "5", 1, 300),
        )


_settings: Settings | None = None


def get_settings() -> Settings:
    """Trả về cấu hình đã tải (có cache). Dùng reset_settings() trong kiểm thử."""
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
    return _settings


def reset_settings() -> None:
    """Xóa cache cấu hình (dùng khi kiểm thử đổi biến môi trường)."""
    global _settings
    _settings = None
