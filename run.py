"""Entry point duy nhất để khởi động ứng dụng: python run.py"""

import sys
from pathlib import Path
from app.main import app
from app.settings import get_settings

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def main() -> None:
    import uvicorn

    settings = get_settings()
    # Host hiển thị cho người dùng mở trình duyệt (0.0.0.0 chỉ là địa chỉ bind).
    browser_host = "localhost" if settings.app_host in ("0.0.0.0", "::", "") else settings.app_host
    print("=" * 60)
    print("Denso Production Input")
    print(f"  Trang giao diện : http://{browser_host}:{settings.app_port}")
    print(f"  Tài liệu API     : http://{browser_host}:{settings.app_port}/docs")
    print("=" * 60)

    uvicorn.run(
        app,
        host=settings.app_host,
        port=settings.app_port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
