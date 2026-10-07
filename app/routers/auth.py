"""API đăng nhập/đăng xuất, người dùng hiện tại và quản lý tài khoản (ADMIN)."""

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse

from app.auth import SESSION_COOKIE, cookie_options, current_user, require_roles
from app.services.auth_service import AuthError, AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])


def get_service() -> AuthService:
    return AuthService()


@router.post("/login")
def login(payload: dict, response: Response, service: AuthService = Depends(get_service)):
    try:
        result = service.login(payload.get("username", ""), payload.get("password", ""))
    except AuthError as exc:
        return JSONResponse(status_code=401,
                            content={"success": False, "message": str(exc), "data": None})
    response.set_cookie(SESSION_COOKIE, result["token"], **cookie_options())
    return {"success": True, "message": "Đã đăng nhập.", "data": result["user"]}


@router.post("/logout")
def logout(request: Request, response: Response, service: AuthService = Depends(get_service)):
    token = request.cookies.get(SESSION_COOKIE)
    service.logout(token)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"success": True, "message": "Đã đăng xuất.", "data": None}


@router.get("/me")
def me(user: dict = Depends(current_user)):
    return {"success": True, "message": "OK", "data": user}


# ---- Quản lý tài khoản (ADMIN) ----
@router.get("/users")
def list_users(user: dict = Depends(require_roles("ADMIN")),
               service: AuthService = Depends(get_service)):
    return {"success": True, "message": "OK", "data": service.list_users()}


@router.post("/users", status_code=201)
def create_user(payload: dict, user: dict = Depends(require_roles("ADMIN")),
                service: AuthService = Depends(get_service)):
    row = service.create_user(
        username=payload.get("username"),
        display_name=payload.get("display_name"),
        password=payload.get("password"),
        roles=payload.get("roles") or ["OPERATOR"],
        is_simulated=bool(payload.get("is_simulated", False)),
    )
    roles = service.repository.roles_for(row["id"])
    return {"success": True, "message": "Đã tạo tài khoản.", "data": {"id": row["id"], "username": row["username"], "display_name": row["display_name"], "roles": roles}}


@router.post("/users/{user_id}/active")
def set_user_active(user_id: int, payload: dict,
                    user: dict = Depends(require_roles("ADMIN")),
                    service: AuthService = Depends(get_service)):
    row = service.set_user_active(user_id, bool(payload.get("active", True)))
    return {"success": True, "message": "Đã cập nhật.", "data": row}
