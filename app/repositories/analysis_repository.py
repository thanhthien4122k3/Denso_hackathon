"""Repository lưu vết kết quả phân tích tác động."""

from psycopg import OperationalError
from psycopg.types.json import Jsonb

from app.database import get_connection
from app.exceptions import DatabaseUnavailableError


def _db_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except OperationalError as exc:
            raise DatabaseUnavailableError(str(exc)) from exc

    wrapper.__name__ = func.__name__
    return wrapper


class AnalysisRepository:
    def __init__(self, settings=None):
        self._settings = settings

    def _conn(self):
        return get_connection(self._settings)

    @_db_errors
    def create_run(self, data) -> dict:
        params = {**data, "input": Jsonb(data.get("input") or {})}
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO production.analysis_runs (source_type, source_id, input, "
                "rule_version, is_simulated) VALUES (%(source_type)s, %(source_id)s, "
                "%(input)s, %(rule_version)s, %(is_simulated)s) RETURNING *",
                params,
            )
            row = cur.fetchone()
            conn.commit()
        return row

    @_db_errors
    def list_runs(self, page, page_size, source_type=None):
        params = {"limit": page_size, "offset": (page - 1) * page_size}
        where = ""
        if source_type:
            where = " WHERE source_type = %(source_type)s"
            params["source_type"] = source_type
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                f"SELECT COUNT(*) AS total FROM production.analysis_runs{where}", params
            )
            total = cur.fetchone()["total"]
            cur.execute(
                f"SELECT * FROM production.analysis_runs{where} "
                "ORDER BY id DESC LIMIT %(limit)s OFFSET %(offset)s",
                params,
            )
            return cur.fetchall(), total

    @_db_errors
    def get_run(self, run_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM production.analysis_runs WHERE id = %(id)s", {"id": run_id})
            return cur.fetchone()

    @_db_errors
    def list_impacts(self, run_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM production.analysis_impacts WHERE run_id = %(id)s ORDER BY id",
                {"id": run_id},
            )
            return cur.fetchall()

    @_db_errors
    def list_hypotheses(self, run_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM production.analysis_hypotheses WHERE run_id = %(id)s ORDER BY id",
                {"id": run_id},
            )
            return cur.fetchall()

    @_db_errors
    def list_actions(self, run_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM production.analysis_actions WHERE run_id = %(id)s ORDER BY id",
                {"id": run_id},
            )
            return cur.fetchall()

    @_db_errors
    def save_impacts(self, run_id, impacts: list[dict]):
        if not impacts:
            return
        with self._conn() as conn, conn.cursor() as cur:
            for item in impacts:
                cur.execute(
                    "INSERT INTO production.analysis_impacts (run_id, node_type, node_id, "
                    "node_name, impact_type, path, evidence, rule_id, assumptions, "
                    "missing_info, departments) VALUES (%(run_id)s, %(node_type)s, "
                    "%(node_id)s, %(node_name)s, %(impact_type)s, %(path)s, %(evidence)s, "
                    "%(rule_id)s, %(assumptions)s, %(missing_info)s, %(departments)s)",
                    {
                        "run_id": run_id,
                        **item,
                        "path": Jsonb(item.get("path") or []),
                        "departments": Jsonb(item.get("departments") or []),
                    },
                )
            conn.commit()

    @_db_errors
    def save_hypotheses(self, run_id, hypotheses: list[dict]):
        if not hypotheses:
            return
        with self._conn() as conn, conn.cursor() as cur:
            for item in hypotheses:
                cur.execute(
                    "INSERT INTO production.analysis_hypotheses (run_id, content, evidence, "
                    "check_more, rule_id, priority) VALUES (%(run_id)s, %(content)s, "
                    "%(evidence)s, %(check_more)s, %(rule_id)s, %(priority)s)",
                    {"run_id": run_id, **item},
                )
            conn.commit()

    @_db_errors
    def save_actions(self, run_id, actions: list[dict]):
        if not actions:
            return
        with self._conn() as conn, conn.cursor() as cur:
            for item in actions:
                cur.execute(
                    "INSERT INTO production.analysis_actions (run_id, department_id, "
                    "department_name, action, priority) VALUES (%(run_id)s, %(department_id)s, "
                    "%(department_name)s, %(action)s, %(priority)s)",
                    {"run_id": run_id, **item},
                )
            conn.commit()
