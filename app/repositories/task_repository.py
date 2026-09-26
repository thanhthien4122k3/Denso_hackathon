"""Repository công việc theo bộ phận và thông tin khảo sát."""

from psycopg import OperationalError

from app.database import get_connection
from app.exceptions import DatabaseUnavailableError

_TASK_COLS = [
    "department_id", "title", "description", "status", "priority",
    "source_incident_id", "source_analysis_run_id", "rule_id", "is_simulated",
]


def _db_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except OperationalError as exc:
            raise DatabaseUnavailableError(str(exc)) from exc

    wrapper.__name__ = func.__name__
    return wrapper


class TaskRepository:
    def __init__(self, settings=None):
        self._settings = settings

    def _conn(self):
        return get_connection(self._settings)

    @_db_errors
    def list(self, page, page_size, department_id=None, status=None):
        conds, params = [], {"limit": page_size, "offset": (page - 1) * page_size}
        if department_id is not None:
            conds.append("department_id = %(department_id)s")
            params["department_id"] = department_id
        if status:
            conds.append("status = %(status)s")
            params["status"] = status
        where = (" WHERE " + " AND ".join(conds)) if conds else ""
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                f"SELECT COUNT(*) AS total FROM production.action_tasks{where}", params
            )
            total = cur.fetchone()["total"]
            cur.execute(
                f"SELECT * FROM production.action_tasks{where} "
                "ORDER BY id DESC LIMIT %(limit)s OFFSET %(offset)s",
                params,
            )
            return cur.fetchall(), total

    @_db_errors
    def get(self, task_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM production.action_tasks WHERE id = %(id)s", {"id": task_id})
            return cur.fetchone()

    @_db_errors
    def create(self, data):
        cols = [c for c in _TASK_COLS if c in data]
        sql = (
            "INSERT INTO production.action_tasks (" + ", ".join(cols)
            + ") VALUES (" + ", ".join(f"%({c})s" for c in cols) + ") RETURNING *"
        )
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, data)
            row = cur.fetchone()
            conn.commit()
        return row

    @_db_errors
    def update(self, task_id, data):
        cols = ["department_id", "title", "description", "status", "priority"]
        cols = [c for c in cols if c in data]
        if not cols:
            return self.get(task_id)
        assign = ", ".join(f"{c} = %({c})s" for c in cols)
        sql = (
            f"UPDATE production.action_tasks SET {assign}, updated_at = CURRENT_TIMESTAMP "
            "WHERE id = %(id)s RETURNING *"
        )
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, {**data, "id": task_id})
            row = cur.fetchone()
            conn.commit()
        return row

    @_db_errors
    def update_status(self, task_id, status):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE production.action_tasks SET status = %(status)s, "
                "updated_at = CURRENT_TIMESTAMP WHERE id = %(id)s RETURNING *",
                {"status": status, "id": task_id},
            )
            row = cur.fetchone()
            conn.commit()
        return row


class SurveyRepository:
    def __init__(self, settings=None):
        self._settings = settings

    def _conn(self):
        return get_connection(self._settings)

    @_db_errors
    def list(self, group_code=None):
        with self._conn() as conn, conn.cursor() as cur:
            if group_code:
                cur.execute(
                    "SELECT * FROM production.survey_items WHERE group_code = %(g)s ORDER BY id",
                    {"g": group_code},
                )
            else:
                cur.execute("SELECT * FROM production.survey_items ORDER BY group_code, id")
            return cur.fetchall()

    @_db_errors
    def get(self, item_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM production.survey_items WHERE id = %(id)s", {"id": item_id})
            return cur.fetchone()

    @_db_errors
    def create(self, data):
        cols = ["group_code", "question", "answer", "provided_by", "provided_at", "status", "note"]
        cols = [c for c in cols if c in data]
        sql = (
            "INSERT INTO production.survey_items (" + ", ".join(cols)
            + ") VALUES (" + ", ".join(f"%({c})s" for c in cols) + ") RETURNING *"
        )
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, data)
            row = cur.fetchone()
            conn.commit()
        return row

    @_db_errors
    def update(self, item_id, data):
        cols = ["group_code", "question", "answer", "provided_by", "provided_at", "status", "note"]
        cols = [c for c in cols if c in data]
        if not cols:
            return self.get(item_id)
        assign = ", ".join(f"{c} = %({c})s" for c in cols)
        sql = f"UPDATE production.survey_items SET {assign}, updated_at = CURRENT_TIMESTAMP WHERE id = %(id)s RETURNING *"
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, {**data, "id": item_id})
            row = cur.fetchone()
            conn.commit()
        return row
