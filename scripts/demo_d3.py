"""Demo end-to-end cho kịch bản chính DEMO-D3-01 (Bước 1-7 trong đặc tả).

Chạy trong tiến trình, tự tạo database demo riêng (mặc định denso_hackathon_demo)
để không đụng dữ liệu thật. Dùng FastAPI TestClient (gọi qua ASGI, cùng endpoint
với server thật).

Cách chạy:
    python scripts/demo_d3.py
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DEMO_DB = os.environ.get("DEMO_DB_NAME", "denso_hackathon_demo")

# Đặt DB demo trước khi import app để lifespan chạy migration trên DB demo.
os.environ["DB_NAME"] = DEMO_DB
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")

import psycopg  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
from app.settings import ENV_FILE, reset_settings  # noqa: E402

load_dotenv(ENV_FILE, override=False)
reset_settings()


def _ensure_db():
    host = os.environ.get("DB_HOST", "localhost")
    port = int(os.environ.get("DB_PORT", "5432"))
    user = os.environ.get("DB_USER", "postgres")
    password = os.environ.get("DB_PASSWORD", "")
    admin = psycopg.connect(host=host, port=port, user=user, password=password,
                            dbname="postgres", autocommit=True)
    with admin.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %(n)s", {"n": DEMO_DB})
        if cur.fetchone() is not None:
            cur.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %(n)s",
                {"n": DEMO_DB},
            )
            cur.execute(f'DROP DATABASE "{DEMO_DB}"')
        cur.execute(f'CREATE DATABASE "{DEMO_DB}"')
    admin.close()


def _print(title, obj):
    import json
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def _find_by_code(client, path, code):
    d = client.get(f"{path}?page_size=100").json()["data"]["items"]
    for i in d:
        if i["code"] == code:
            return i
    raise RuntimeError(f"Không tìm thấy {code} trong {path}")


def main():
    _ensure_db()

    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as client:
        # Tạo admin và đăng nhập (DB demo mới nên chưa có tài khoản).
        from app.services.auth_service import AuthService
        svc = AuthService()
        if svc.repository.find_by_username("admin") is None:
            svc.create_user("admin", "Quản trị demo", "admin-demo-password", ["ADMIN"], is_simulated=False)
        client.post("/api/auth/login", json={"username": "admin", "password": "admin-demo-password"})

        # Bước 1: nạp dữ liệu nền.
        r = client.post("/api/scenarios/d3/load")
        d3 = r.json()["data"]
        _print("Bước 1 — Nạp DEMO-D3-01", {"loaded": d3["loaded"], "credentials": d3.get("credentials")})

        machine = _find_by_code(client, "/api/catalog/machine", "M10")

        # Bước 2: ghi nhận lỗi mới (STOPPED + khoảng dừng mở).
        r = client.post("/api/operations/report-machine-error", json={
            "machine_id": machine["id"],
            "event_time": "2026-10-06T10:00:00+07:00",
            "error_code": "E-DEMO-01",
            "observation": "Máy dừng, màn hình báo lỗi bộ phận cấp phôi",
            "is_simulated": True,
        })
        err = r.json()["data"]
        _print("Bước 2 — Ghi nhận lỗi máy", err)
        downtime_id = err["downtime"]["id"]

        # Tạo sự cố từ bản ghi (thông tin điền sẵn).
        r = client.post("/api/incidents", json={
            "code": "INC-DEMO-01", "title": "Máy M10 dừng - lỗi cấp phôi",
            "incident_type": "MACHINE_STOP", "source_object_type": "machine",
            "source_object_id": machine["id"],
            "start_time": "2026-10-06T10:00:00+07:00", "severity": "HIGH",
            "description": "Máy dừng, màn hình báo lỗi bộ phận cấp phôi.",
            "status": "OPEN", "request_id": "550e8400-e29b-41d4-a716-446655440001",
            "is_simulated": True,
        })
        incident_id = r.json()["data"]["id"]
        _print("Bước 2 — Sự cố đã tạo", {"incident_id": incident_id, "code": "INC-DEMO-01"})

        # Bước 3: phân tích tại mốc 10:00, giả định dừng 15 phút.
        r = client.post("/api/analysis/run", json={
            "incident_id": incident_id, "max_depth": 5, "duration_minutes": 15,
        })
        res = r.json()["data"]
        run_id = res["run_id"]
        _print("Bước 3 — Kết quả phân tích", {
            "run_id": run_id,
            "rule_version": res["rule_version"],
            "context": res["context"],
            "buffer_estimate": res["buffer_estimate"],
            "capacity_estimate": res["capacity_estimate"],
            "related_past_incidents": res["related_past_incidents"],
            "hypotheses": res["hypotheses"],
            "actions": res["actions"],
        })

        # Bước 5: chọn đề xuất bảo trì -> tạo công việc, chạy lại không trùng.
        # Lấy action id thật từ run (lưu vết).
        actions = client.get(f"/api/analysis/runs/{run_id}").json()["data"]["actions"]
        maint_act = next(a for a in actions if "Bảo trì" in (a["department_name"] or "")
                         or a["department_name"] == "MAINT")
        payload = {"analysis_action_id": maint_act["id"], "title": maint_act["action"],
                   "department_id": maint_act["department_id"],
                   "source_incident_id": incident_id, "source_analysis_run_id": run_id,
                   "is_simulated": True}
        t1 = client.post("/api/tasks/from-action", json=payload).json()["data"]
        t2 = client.post("/api/tasks/from-action", json=payload)
        _print("Bước 5 — Tạo công việc (không trùng)", {
            "created_task_id": t1["id"],
            "re_run_status_code": t2.status_code,
            "re_run_message": t2.json()["message"],
        })

        # Bước 6: phục hồi lúc 10:12.
        client.post("/api/operations/machine-states", json={
            "machine_id": machine["id"], "event_time": "2026-10-06T10:12:00+07:00",
            "state": "RUNNING", "is_simulated": True,
        })
        client.post(f"/api/operations/downtimes/{downtime_id}/close", json={
            "end_time": "2026-10-06T10:12:00+07:00",
        })
        client.post(f"/api/tasks/{t1['id']}/status", json={"status": "DONE"})
        r2 = client.post("/api/analysis/run", json={
            "incident_id": incident_id, "max_depth": 5, "duration_minutes": 12,
        }).json()["data"]
        _print("Bước 6 — Phân tích lại sau phục hồi", {
            "duration_minutes": 12,
            "capacity_estimate": r2["capacity_estimate"],
            "context": r2["context"],
        })

        # Bước 7: đóng hồ sơ và lưu kinh nghiệm.
        client.put(f"/api/incidents/{incident_id}", json={
            "status": "RESOLVED",
            "recovered_at": "2026-10-06T10:12:00+07:00",
            "recovered_by": "demo-supervisor",
            "closed_at": "2026-10-06T11:00:00+07:00",
            "closed_by": "demo-supervisor",
            "resolution_summary": "Bảo trì kiểm tra và căn chỉnh cảm biến cấp phôi.",
            "root_cause_status": "CONFIRMED",
        })
        client.post("/api/context/experiences", json={
            "source_incident_id": incident_id, "incident_type": "MACHINE_STOP",
            "error_code": "E-DEMO-01", "machine_id": machine["id"],
            "symptom": "Máy dừng, màn hình báo lỗi bộ phận cấp phôi.",
            "root_cause": "Cảm biến phát hiện phôi bị lệch vị trí.",
            "actions": "Bảo trì kiểm tra và căn chỉnh theo hướng dẫn demo.",
            "result": "Máy chạy lại sau xử lý.",
            "approved_by": "demo-supervisor",
            "is_simulated": True,
        })
        inc = client.get(f"/api/incidents/{incident_id}").json()["data"]
        _print("Bước 7 — Hồ sơ đã đóng", {
            "status": inc["status"], "root_cause_status": inc["root_cause_status"],
            "closed_by": inc["closed_by"], "resolution_summary": inc["resolution_summary"],
        })

        print("\nHoàn tất demo. Xem dữ liệu bằng SQL read-only trong docs/SQL_READONLY.md")


if __name__ == "__main__":
    main()
