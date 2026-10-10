"""Nghiệp vụ xác thực: đăng nhập, phiên, người dùng hiện tại và vai trò."""

from datetime import datetime, timezone

from app.exceptions import ValidationFailedError
from app.repositories.auth_repository import AuthRepository, LOCKOUT_MINUTES
from app.security import hash_token, hash_password, new_session_token, verify_password


class AuthError(ValueError):
    """Đăng nhập thất bại (không tiết lộ tài khoản có tồn tại hay không)."""


class AuthService:
    def __init__(self, repository: AuthRepository | None = None):
        self.repository = repository or AuthRepository()

    def login(self, username: str, password: str) -> dict:
        username = (username or "").strip()
        if not username or not password:
            raise AuthError("Sai tài khoản hoặc mật khẩu.")
        user = self.repository.find_by_username(username)
        # Luôn chạy hàm băm để tránh đoán sự tồn tại tài khoản theo thời gian.
        dummy = hash_password("dummy-password-for-timing")
        if user is None:
            verify_password(password, dummy)
            raise AuthError("Sai tài khoản hoặc mật khẩu.")

        locked = user.get("locked_until")
        if locked is not None:
            if locked.tzinfo is None:
                locked = locked.replace(tzinfo=timezone.utc)
            if locked > datetime.now(timezone.utc):
                raise AuthError("Tài khoản tạm khóa do nhập sai nhiều lần. Thử lại sau.")

        if not user.get("active"):
            raise AuthError("Sai tài khoản hoặc mật khẩu.")

        if not verify_password(password, user.get("password_hash")):
            self.repository.record_failure(user["id"])
            raise AuthError("Sai tài khoản hoặc mật khẩu.")

        self.repository.reset_failures(user["id"])
        token = new_session_token()
        self.repository.create_session(hash_token(token), user["id"])
        return {"token": token, "user": self._to_public(user)}

    def logout(self, token: str):
        if token:
            self.repository.revoke_session(hash_token(token))

    def user_from_token(self, token: str) -> dict | None:
        """Trả về user + roles nếu phiên hợp lệ; None nếu không."""
        if not token:
            return None
        session = self.repository.get_session(hash_token(token))
        if session is None:
            return None
        if session.get("revoked_at") is not None:
            return None
        if session["expires_at"].replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            return None
        user = self.repository.get_user(session["user_id"])
        if user is None or not user.get("active"):
            return None
        roles = self.repository.roles_for(user["id"])
        return self._to_public(user, roles)

    def _to_public(self, user, roles=None) -> dict:
        roles = roles if roles is not None else self.repository.roles_for(user["id"])
        return {
            "id": user["id"],
            "username": user["username"],
            "display_name": user["display_name"],
            "roles": roles,
            "is_simulated": user.get("is_simulated", False),
        }

    def list_users(self):
        return self.repository.list_users()

    def create_user(self, username, display_name, password, roles, is_simulated=False):
        if not username or not password:
            raise ValidationFailedError("username và password là bắt buộc.")
        if self.repository.find_by_username(username) is not None:
            raise ValidationFailedError("Tên đăng nhập đã tồn tại.")
        row = self.repository.create_user({
            "username": username.strip(),
            "display_name": (display_name or username).strip(),
            "password_hash": hash_password(password),
            "active": True,
            "is_simulated": is_simulated,
        })
        for role in roles or []:
            self.repository.add_role(row["id"], role)
        return row

    def set_user_active(self, user_id, active):
        row = self.repository.set_active(user_id, active)
        if not active:
            self.repository.revoke_user_sessions(user_id)
        return self._to_public(row)

    def reset_password(self, user_id, new_password):
        self.repository.set_password(user_id, hash_password(new_password))
        self.repository.revoke_user_sessions(user_id)
