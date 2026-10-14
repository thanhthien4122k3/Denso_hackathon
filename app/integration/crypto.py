"""Mã hóa đối xứng cho credentials nguồn (Fernet từ khóa cấu hình).

Khóa mã hóa lấy từ biến môi trường SOURCE_ENCRYPTION_KEY (không lưu trong DB hay
repository). Nếu không có khóa, không được lưu password.
"""

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.settings import SOURCE_ENCRYPTION_KEY


def _key() -> bytes | None:
    raw = (SOURCE_ENCRYPTION_KEY or "").strip()
    if not raw:
        return None
    digest = hashlib.sha256(raw.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def encryption_available() -> bool:
    return _key() is not None


def encrypt_secret(plaintext: str) -> str:
    key = _key()
    if key is None:
        raise RuntimeError(
            "Chưa cấu hình SOURCE_ENCRYPTION_KEY; không thể lưu mật khẩu nguồn."
        )
    return Fernet(key).encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_secret(ciphertext: str) -> str:
    key = _key()
    if key is None:
        raise RuntimeError(
            "Chưa cấu hình SOURCE_ENCRYPTION_KEY; không thể giải mã mật khẩu nguồn."
        )
    try:
        return Fernet(key).decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError):
        raise RuntimeError("Không thể giải mã mật khẩu nguồn (khóa mã hóa không khớp).")


def mask_secret(value: str) -> str:
    return "••••••" if value else ""
