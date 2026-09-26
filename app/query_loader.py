"""Đọc và kiểm tra cấu hình SQL trong file YAML.

Chỉ dùng yaml.safe_load. Mỗi query phải có đủ `description`, `fetch`
(none/one/all) và `sql`. Không cho phép người dùng tự truyền tên query.
"""

from pathlib import Path

import yaml

from app.settings import DATABASE_YAML_PATH, PRODUCTION_QUERIES_YAML_PATH

ALLOWED_FETCH = {"none", "one", "all"}


class QueryConfigError(ValueError):
    """Cấu hình SQL trong YAML không hợp lệ."""


class QueryLoader:
    def __init__(self, path: Path):
        self.path = path
        self._queries: dict | None = None

    def load(self) -> dict:
        if self._queries is None:
            self._queries = self._load()
        return self._queries

    def _load(self) -> dict:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f)
        except FileNotFoundError as exc:
            raise QueryConfigError(f"Không tìm thấy file cấu hình: {self.path}") from exc
        except yaml.YAMLError as exc:
            raise QueryConfigError(f"File YAML không hợp lệ: {self.path}: {exc}") from exc

        if not isinstance(raw, dict) or not isinstance(raw.get("queries"), dict):
            raise QueryConfigError(f"{self.path} phải chứa khóa 'queries' là một dict.")

        queries = raw["queries"]
        if not queries:
            raise QueryConfigError(f"{self.path} không có query nào.")

        validated = {}
        for name, spec in queries.items():
            validated[name] = self._validate(name, spec)
        return validated

    def _validate(self, name: str, spec) -> dict:
        if not isinstance(spec, dict):
            raise QueryConfigError(f"Query '{name}' phải là một dict.")

        description = spec.get("description")
        fetch = spec.get("fetch")
        sql = spec.get("sql")

        if fetch not in ALLOWED_FETCH:
            raise QueryConfigError(
                f"Query '{name}' có fetch={fetch!r}; cho phép {sorted(ALLOWED_FETCH)}."
            )
        if not isinstance(sql, str) or not sql.strip():
            raise QueryConfigError(f"Query '{name}' thiếu sql hoặc sql rỗng.")

        return {
            "description": description or "",
            "fetch": fetch,
            "sql": sql.strip(),
        }


_database_loader = QueryLoader(DATABASE_YAML_PATH)
_production_loader = QueryLoader(PRODUCTION_QUERIES_YAML_PATH)


def get_database_queries() -> dict:
    """Các query khởi tạo schema/bảng/index."""
    return _database_loader.load()


def get_production_queries() -> dict:
    """Các query nghiệp vụ (insert/select/count/health)."""
    return _production_loader.load()


def load_all() -> tuple[dict, dict]:
    """Nạp và kiểm tra cả hai file cấu hình (gọi lúc khởi động)."""
    return get_database_queries(), get_production_queries()
