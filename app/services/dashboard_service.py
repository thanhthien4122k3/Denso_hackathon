"""Tổng quan dashboard từ dữ liệu thật trong database."""

from app.catalog import CATALOG_ENTITIES
from app.database import get_connection
from app.exceptions import DatabaseUnavailableError
from psycopg import OperationalError


class DashboardService:
    def _count(self, table, where=""):
        try:
            with get_connection() as conn, conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) AS n FROM production.{table} {where}")
                return cur.fetchone()["n"]
        except OperationalError as exc:
            raise DatabaseUnavailableError(str(exc)) from exc

    def summary(self):
        catalog = {}
        for key, spec in CATALOG_ENTITIES.items():
            total = self._count(spec.table)
            simulated = self._count(spec.table, "WHERE is_simulated = TRUE")
            catalog[key] = {"total": total, "simulated": simulated}

        return {
            "production_records": self._count("production_records"),
            "catalog": catalog,
            "sources": self._count("data_sources"),
            "datasets": self._count("datasets"),
            "graph_edges": self._count("graph_edges"),
            "incidents": {
                "total": self._count("incidents"),
                "open": self._count("incidents", "WHERE status = 'OPEN'"),
            },
            "tasks": {
                "total": self._count("action_tasks"),
                "todo": self._count("action_tasks", "WHERE status = 'TODO'"),
            },
            "analysis_runs": self._count("analysis_runs"),
        }
