"""Repository cho xác thực: users, roles, sessions, giới hạn đăng nhập thất bại."""

from datetime import datetime, timedelta, timezone

from psycopg import OperationalError
from psycopg.errors import UniqueViolation

from app.database import get_connection
from app.exceptions import DatabaseUnavailableError

ROLES = {"OPERATOR", "HANDLER", "COORDINATOR", "ADMIN"}

SESSION_TTL_HOURS = 12
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 5


def _db_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except UniqueViolation:
            raise
        except OperationalError as exc:
            raise DatabaseUnavailableError(str(exc)) from exc

    wrapper.__name__ = func.__name__
    return wrapper


class AuthRepository:
    def __init__(self, settings=None):
        self._settings = settings

    def _conn(self):
        return get_connection(self._settings)

    # ---- users ----
    @_db_errors
    def find_by_username(self, username):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM production.users WHERE username = %(u)s", {"u": username}
            )
            return cur.fetchone()

    @_db_errors
    def get_user(self, user_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM production.users WHERE id = %(id)s", {"id": user_id}
            )
            return cur.fetchone()

    @_db_errors
    def create_user(self, data):
        cols = ["username", "display_name", "password_hash", "active", "is_simulated"]
        cols = [c for c in cols if c in data]
        sql = (
            "INSERT INTO production.users (" + ", ".join(cols)
            + ") VALUES (" + ", ".join(f"%({c})s" for c in cols) + ") RETURNING *"
        )
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, data)
            row = cur.fetchone()
            conn.commit()
        return row

    @_db_errors
    def list_users(self):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT u.id, u.username, u.display_name, u.active, u.is_simulated, "
                "u.last_login_at, COALESCE(array_agg(r.role) FILTER (WHERE r.role IS NOT NULL), '{}') AS roles "
                "FROM production.users u "
                "LEFT JOIN production.user_roles r ON r.user_id = u.id "
                "GROUP BY u.id ORDER BY u.id"
            )
            return cur.fetchall()

    @_db_errors
    def set_active(self, user_id, active):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE production.users SET active = %(active)s, updated_at = CURRENT_TIMESTAMP "
                "WHERE id = %(id)s RETURNING *",
                {"active": active, "id": user_id},
            )
            row = cur.fetchone()
            conn.commit()
        return row

    @_db_errors
    def set_password(self, user_id, password_hash):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE production.users SET password_hash = %(h)s, updated_at = CURRENT_TIMESTAMP "
                "WHERE id = %(id)s",
                {"h": password_hash, "id": user_id},
            )
            conn.commit()

    # ---- roles ----
    @_db_errors
    def add_role(self, user_id, role):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO production.user_roles (user_id, role) VALUES (%(u)s, %(r)s) "
                "ON CONFLICT (user_id, role) DO NOTHING",
                {"u": user_id, "r": role},
            )
            conn.commit()

    @_db_errors
    def roles_for(self, user_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT role FROM production.user_roles WHERE user_id = %(id)s ORDER BY role",
                {"id": user_id},
            )
            return [r["role"] for r in cur.fetchall()]

    # ---- failed attempts / lockout ----
    @_db_errors
    def record_failure(self, user_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE production.users SET failed_attempts = failed_attempts + 1, "
                "locked_until = CASE WHEN failed_attempts + 1 >= %(max)s "
                "THEN CURRENT_TIMESTAMP + (%(max)s * interval '1 minute') ELSE locked_until END "
                "WHERE id = %(id)s",
                {"max": MAX_FAILED_ATTEMPTS, "id": user_id},
            )
            conn.commit()

    @_db_errors
    def reset_failures(self, user_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE production.users SET failed_attempts = 0, locked_until = NULL, "
                "last_login_at = CURRENT_TIMESTAMP WHERE id = %(id)s",
                {"id": user_id},
            )
            conn.commit()

    # ---- sessions ----
    @_db_errors
    def create_session(self, token_hash, user_id):
        expires_at = datetime.now(timezone.utc) + timedelta(hours=SESSION_TTL_HOURS)
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO production.sessions (token_hash, user_id, expires_at) "
                "VALUES (%(h)s, %(u)s, %(e)s) RETURNING *",
                {"h": token_hash, "u": user_id, "e": expires_at},
            )
            row = cur.fetchone()
            conn.commit()
        return row

    @_db_errors
    def get_session(self, token_hash):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM production.sessions WHERE token_hash = %(h)s",
                {"h": token_hash},
            )
            return cur.fetchone()

    @_db_errors
    def revoke_session(self, token_hash):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE production.sessions SET revoked_at = CURRENT_TIMESTAMP "
                "WHERE token_hash = %(h)s",
                {"h": token_hash},
            )
            conn.commit()

    @_db_errors
    def revoke_user_sessions(self, user_id):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE production.sessions SET revoked_at = CURRENT_TIMESTAMP "
                "WHERE user_id = %(id)s AND revoked_at IS NULL",
                {"id": user_id},
            )
            conn.commit()
