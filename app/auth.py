"""Xác thực: middleware đọc phiên, dependency lấy user/roles, cấu hình cookie.

Phiên dùng cookie HttpOnly + SameSite. Đăng nhập/làm mới xử lý ở router.
"""

import os

from fastapi import Request
from fastapi.responses import JSONResponse

from app.services.auth_service import AuthService

SESSION_COOKIE = "d3_session"
SESSION_MAX_AGE = 12 * 3600  # 12 giờ

# Các đường dẫn không cần đăng nhập.
PUBLIC_PATHS = {"/api/auth/login", "/api/health"}

# Cấu hình cookie Secure (bật khi chạy HTTPS).
SECURE_COOKIE = os.getenv("APP_SECURE_COOKIE", "0") in ("1", "true", "True")


def cookie_options() -> dict:
    return {
        "httponly": True,
        "samesite": "lax",
        "secure": SECURE_COOKIE,
        "path": "/",
        "max_age": SESSION_MAX_AGE,
    }


def _is_mutating(method: str) -> bool:
    return method in ("POST", "PUT", "PATCH", "DELETE")


def _origin_ok(request: Request) -> bool:
    """Chặn yêu cầu đổi dữ liệu từ origin khác (CSRF nhẹ, bổ trợ SameSite=Lax)."""
    origin = request.headers.get("origin")
    if not origin:
        return True  # same-origin hoặc client không gửi Origin (curl/script)
    host = request.headers.get("host", "")
    try:
        from urllib.parse import urlparse

        return urlparse(origin).netloc == host
    except Exception:
        return False


async def auth_middleware(request: Request, call_next):
    path = request.url.path
    if path in PUBLIC_PATHS or not path.startswith("/api/"):
        request.state.user = None
        request.state.roles = []
        return await call_next(request)

    token = request.cookies.get(SESSION_COOKIE)
    user = AuthService().user_from_token(token) if token else None
    if user is None:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Chưa đăng nhập hoặc phiên đã hết hạn.", "data": None},
        )
    if _is_mutating(request.method) and not _origin_ok(request):
        return JSONResponse(
            status_code=403,
            content={"success": False, "message": "Nguồn gốc yêu cầu không hợp lệ.", "data": None},
        )

    request.state.user = user
    request.state.roles = user["roles"]
    return await call_next(request)


def current_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if user is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=401, detail="Chưa đăng nhập hoặc phiên đã hết hạn.")
    return user


def require_roles(*allowed):
    from fastapi import HTTPException

    def dep(request: Request) -> dict:
        user = current_user(request)
        roles = set(getattr(request.state, "roles", []))
        if "ADMIN" in roles:
            return user
        if not (roles & set(allowed)):
            raise HTTPException(status_code=403, detail="Không có quyền thực hiện hành động này.")
        return user

    return dep
