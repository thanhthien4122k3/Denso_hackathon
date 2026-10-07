"""Băm mật khẩu và sinh phiên đăng nhập (dùng thư viện chuẩn, không tự viết thuật toán).

- Mật khẩu: PBKDF2-HMAC-SHA256 (hashlib.pbkdf2_hmac) với muối ngẫu nhiên và số
  vòng lặp đủ lớn. Định dạng lưu: pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>.
- Phiên: token ngẫu nhiên 256-bit (cookie), DB lưu SHA-256 của token.
"""

import hashlib
import hmac
import os
import secrets

PBKDF2_ITERATIONS = 260_000
SESSION_BYTES = 32


def _constant_time(a: bytes, b: bytes) -> bool:
    return hmac.compare_digest(a, b)


def hash_password(password: str) -> str:
    if not password:
        raise ValueError("Mật khẩu không được rỗng.")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return "pbkdf2_sha256${}${}${}".format(
        PBKDF2_ITERATIONS, salt.hex(), digest.hex()
    )


def verify_password(password: str, stored: str) -> bool:
    if not stored or "$" not in stored:
        return False
    try:
        algo, iterations, salt_hex, hash_hex = stored.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, int(iterations)
        )
        return _constant_time(actual, expected)
    except (ValueError, TypeError):
        return False


def new_session_token() -> str:
    return secrets.token_hex(SESSION_BYTES)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
