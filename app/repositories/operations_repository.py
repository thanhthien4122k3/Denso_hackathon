"""Repository ghi nhận vận hành: trạng thái máy, dừng máy, QC, vật tư."""

from psycopg import OperationalError
from psycopg.errors import ForeignKeyViolation

from app.database import get_connection
from app.exceptions import DatabaseUnavailableError, NotFoundError


def _db_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ForeignKeyViolation as exc:
            raise NotFoundError("Đối tượng tham chiếu không tồn tại.") from exc
        except OperationalError as exc:
            raise DatabaseUnavailableError(str(exc)) from exc

    wrapper.__name__ = func.__name__
    return wrapper


class OperationsRepository:
    def __init__(self, settings=None):
        self._settings = settings

    def _conn(self):
        return get_connection(self._settings)

    def _list(self, table, cols, page, page_size, conditions, params):
        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
        full = {**params, "limit": page_size, "offset": (page - 1) * page_size}
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) AS total FROM production.{table}{where}", full)
            total = cur.fetchone()["total"]
            cur.execute(
                f"SELECT {cols} FROM production.{table}{where} "
                "ORDER BY id DESC LIMIT %(limit)s OFFSET %(offset)s",
                full,
            )
            return cur.fetchall(), total

    def _create(self, table, data):
        cols = [c for c in data]
        sql = (
            f"INSERT INTO production.{table} (" + ", ".join(cols)
            + ") VALUES (" + ", ".join(f"%({c})s" for c in cols) + ") RETURNING *"
        )
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, data)
            row = cur.fetchone()
            conn.commit()
        return row

    # ---- machine_states ----
    @_db_errors
    def list_states(self, page, page_size, machine_id=None, from_time=None, to_time=None):
        conds, params = [], {}
        if machine_id is not None:
            conds.append("machine_id = %(machine_id)s")
            params["machine_id"] = machine_id
        if from_time:
            conds.append("event_time >= %(from_time)s")
            params["from_time"] = from_time
        if to_time:
            conds.append("event_time <= %(to_time)s")
            params["to_time"] = to_time
        return self._list("machine_states", "*", page, page_size, conds, params)

    @_db_errors
    def create_state(self, data):
        return self._create("machine_states", data)

    # ---- machine_downtimes ----
    @_db_errors
    def list_downtimes(self, page, page_size, machine_id=None, from_time=None, to_time=None):
        conds, params = [], {}
        if machine_id is not None:
            conds.append("machine_id = %(machine_id)s")
            params["machine_id"] = machine_id
        if from_time:
            conds.append("start_time >= %(from_time)s")
            params["from_time"] = from_time
        if to_time:
            conds.append("start_time <= %(to_time)s")
            params["to_time"] = to_time
        return self._list("machine_downtimes", "*", page, page_size, conds, params)

    @_db_errors
    def create_downtime(self, data):
        return self._create("machine_downtimes", data)

    @_db_errors
    def update_downtime_end(self, downtime_id, end_time):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE production.machine_downtimes SET end_time = %(end_time)s "
                "WHERE id = %(id)s RETURNING *",
                {"end_time": end_time, "id": downtime_id},
            )
            row = cur.fetchone()
            conn.commit()
        return row

    # ---- qc_results ----
    @_db_errors
    def list_qc(self, page, page_size, lot_id=None, result=None):
        conds, params = [], {}
        if lot_id is not None:
            conds.append("lot_id = %(lot_id)s")
            params["lot_id"] = lot_id
        if result:
            conds.append("result = %(result)s")
            params["result"] = result
        return self._list("qc_results", "*", page, page_size, conds, params)

    @_db_errors
    def create_qc(self, data):
        return self._create("qc_results", data)

    # ---- material_statuses ----
    @_db_errors
    def list_material(self, page, page_size, material_id=None):
        conds, params = [], {}
        if material_id is not None:
            conds.append("material_id = %(material_id)s")
            params["material_id"] = material_id
        return self._list("material_statuses", "*", page, page_size, conds, params)

    @_db_errors
    def create_material(self, data):
        return self._create("material_statuses", data)

    # ---- bằng chứng phục vụ engine ----
    @_db_errors
    def latest_downtime_error(self, machine_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT error_code FROM production.machine_downtimes "
                "WHERE machine_id = %(id)s AND error_code IS NOT NULL "
                "ORDER BY start_time DESC LIMIT 1",
                {"id": machine_id},
            )
            row = cur.fetchone()
            return row["error_code"] if row else None

    # ---- báo lỗi máy nhất quán: trạng thái STOPPED + khoảng dừng mở ----
    @_db_errors
    def report_machine_error(self, data):
        """Ghi đồng thời một sự kiện trạng thái và một khoảng dừng đang mở.

        Dùng chung transaction để không tạo hai khoảng dừng trùng lặp.
        """
        state_cols = ["machine_id", "event_time", "state", "error_code", "note", "is_simulated"]
        state_data = {c: data.get(c) for c in state_cols if c in data}
        state_data.setdefault("state", "STOPPED")
        downtime_cols = ["machine_id", "start_time", "reason", "error_code",
                         "operator_name", "is_simulated"]
        downtime_data = {c: data.get(c) for c in downtime_cols if c in data}
        downtime_data.setdefault("start_time", data.get("event_time"))
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO production.machine_states (" + ", ".join(state_data)
                + ") VALUES (" + ", ".join(f"%({c})s" for c in state_data) + ") RETURNING *",
                state_data,
            )
            state = cur.fetchone()
            cur.execute(
                "INSERT INTO production.machine_downtimes (" + ", ".join(downtime_data)
                + ") VALUES (" + ", ".join(f"%({c})s" for c in downtime_data) + ") RETURNING *",
                downtime_data,
            )
            downtime = cur.fetchone()
            conn.commit()
        return {"state": state, "downtime": downtime}


    @_db_errors
    def latest_qc(self, lot_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT inspected_qty, defect_qty FROM production.qc_results "
                "WHERE lot_id = %(id)s ORDER BY check_time DESC LIMIT 1",
                {"id": lot_id},
            )
            return cur.fetchone()

    @_db_errors
    def latest_material_available(self, material_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT available_qty, unit FROM production.material_statuses "
                "WHERE material_id = %(id)s ORDER BY recorded_at DESC LIMIT 1",
                {"id": material_id},
            )
            return cur.fetchone()
