"""Tạo tài khoản (kể cả quản trị viên đầu tiên) bằng cách nhập mật khẩu an toàn.

Cách chạy:
    python scripts/create_user.py
"""

import getpass
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env", override=False)

from app.settings import reset_settings  # noqa: E402

reset_settings()

from app.migrations import run_migrations  # noqa: E402
from app.repositories.auth_repository import ROLES  # noqa: E402
from app.services.auth_service import AuthService  # noqa: E402


def main():
    print("=== Tạo tài khoản Denso D3 ===")
    print("Vai trò khả dụng:", ", ".join(sorted(ROLES)))
    username = input("Tên đăng nhập: ").strip()
    if not username:
        print("Tên đăng nhập không được rỗng.")
        return
    display = input("Tên hiển thị: ").strip() or username
    roles_raw = input("Vai trò (phân tách bởi dấu phẩy, mặc định OPERATOR): ").strip()
    roles = [r.strip().upper() for r in roles_raw.split(",") if r.strip()] or ["OPERATOR"]
    bad = [r for r in roles if r not in ROLES]
    if bad:
        print("Vai trò không hợp lệ:", ", ".join(bad))
        return
    password = getpass.getpass("Mật khẩu: ")
    confirm = getpass.getpass("Nhập lại mật khẩu: ")
    if password != confirm:
        print("Mật khẩu không khớp.")
        return

    print("Đang khởi tạo schema (nếu chưa có)...")
    run_migrations()

    svc = AuthService()
    row = svc.create_user(username, display, password, roles, is_simulated=False)
    print("Đã tạo tài khoản #%s (%s) với vai trò %s." % (row["id"], username, roles))


if __name__ == "__main__":
    main()
