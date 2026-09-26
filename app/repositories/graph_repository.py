"""Repository cho đồ thị node/edge hai lớp."""

from psycopg import OperationalError
from psycopg.errors import ForeignKeyViolation

from app.database import get_connection
from app.exceptions import DatabaseUnavailableError, NotFoundError
from app.graph import NODE_TABLES, NODE_TYPES

# Bảng dataset_fields không có cột is_simulated.
_SIMULATED_TYPES = NODE_TYPES - {"field"}


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


class GraphRepository:
    def __init__(self, settings=None):
        self._settings = settings

    def _conn(self):
        return get_connection(self._settings)

    @_db_errors
    def node_exists(self, node_type: str, node_id: int) -> bool:
        if node_type not in NODE_TABLES:
            return False
        table = NODE_TABLES[node_type]
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                f'SELECT 1 FROM production."{table}" WHERE id = %(id)s', {"id": node_id}
            )
            return cur.fetchone() is not None

    @_db_errors
    def get_node(self, node_type: str, node_id: int) -> dict | None:
        if node_type not in NODE_TABLES:
            return None
        table = NODE_TABLES[node_type]
        sim = "is_simulated" if node_type in _SIMULATED_TYPES else "FALSE AS is_simulated"
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                f'SELECT id, code, name, {sim} FROM production."{table}" WHERE id = %(id)s',
                {"id": node_id},
            )
            row = cur.fetchone()
        if row is None:
            return None
        return {"type": node_type, **row}

    @_db_errors
    def list_nodes(self, types=None) -> list[dict]:
        selected = [t for t in (types or list(NODE_TABLES)) if t in NODE_TABLES]
        nodes = []
        with self._conn() as conn, conn.cursor() as cur:
            for node_type in selected:
                table = NODE_TABLES[node_type]
                sim = (
                    "is_simulated"
                    if node_type in _SIMULATED_TYPES
                    else "FALSE AS is_simulated"
                )
                cur.execute(
                    f'SELECT id, code, name, {sim} FROM production."{table}" ORDER BY id'
                )
                for row in cur.fetchall():
                    nodes.append({"type": node_type, **row})
        return nodes

    @_db_errors
    def list_edges(self, page, page_size, kind=None, is_simulated=None):
        conditions = []
        params = {"limit": page_size, "offset": (page - 1) * page_size}
        if kind:
            conditions.append("kind = %(kind)s")
            params["kind"] = kind
        if is_simulated is not None:
            conditions.append("is_simulated = %(sim)s")
            params["sim"] = is_simulated
        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) AS total FROM production.graph_edges{where}", params)
            total = cur.fetchone()["total"]
            cur.execute(
                f"SELECT * FROM production.graph_edges{where} "
                "ORDER BY id DESC LIMIT %(limit)s OFFSET %(offset)s",
                params,
            )
            return cur.fetchall(), total

    @_db_errors
    def get_edge(self, edge_id: int) -> dict | None:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM production.graph_edges WHERE id = %(id)s", {"id": edge_id}
            )
            return cur.fetchone()

    @_db_errors
    def create_edge(self, data: dict) -> dict:
        cols = [
            "source_type", "source_id", "target_type", "target_id", "kind",
            "label", "description", "source_confirmation", "valid_from",
            "valid_to", "is_simulated",
        ]
        cols = [c for c in cols if c in data]
        names = ", ".join(cols)
        placeholders = ", ".join(f"%({c})s" for c in cols)
        sql = (
            f"INSERT INTO production.graph_edges ({names}) "
            f"VALUES ({placeholders}) RETURNING *"
        )
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, data)
            row = cur.fetchone()
            conn.commit()
        return row

    @_db_errors
    def update_edge(self, edge_id: int, data: dict) -> dict | None:
        cols = [
            "label", "description", "source_confirmation", "valid_from",
            "valid_to", "is_simulated",
        ]
        cols = [c for c in cols if c in data]
        if not cols:
            return self.get_edge(edge_id)
        assignments = ", ".join(f"{c} = %({c})s" for c in cols)
        sql = (
            f"UPDATE production.graph_edges SET {assignments}, "
            "updated_at = CURRENT_TIMESTAMP WHERE id = %(id)s RETURNING *"
        )
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, {**data, "id": edge_id})
            row = cur.fetchone()
            conn.commit()
        return row

    @_db_errors
    def delete_edge(self, edge_id: int) -> bool:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "DELETE FROM production.graph_edges WHERE id = %(id)s", {"id": edge_id}
            )
            deleted = cur.rowcount > 0
            conn.commit()
        return deleted

    @_db_errors
    def all_edges(self) -> list[dict]:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM production.graph_edges ORDER BY id")
            return cur.fetchall()

    @_db_errors
    def edges_from(self, source_type: str, source_id: int) -> list[dict]:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM production.graph_edges "
                "WHERE source_type = %(t)s AND source_id = %(id)s ORDER BY id",
                {"t": source_type, "id": source_id},
            )
            return cur.fetchall()
