"""Kiểm tra tài nguyên tĩnh: cú pháp JavaScript của giao diện không được lỗi.

Lỗi cú pháp trong app.js làm hỏng TOÀN BỘ tương tác giao diện, nên cần chặn trong CI.
"""

import pytest

from app.settings import STATIC_DIR


def test_app_js_has_valid_syntax():
    esprima = pytest.importorskip("esprima")
    src = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    esprima.parseScript(src)  # raises on syntax error


def test_index_references_app_js():
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    assert "app.js" in html
