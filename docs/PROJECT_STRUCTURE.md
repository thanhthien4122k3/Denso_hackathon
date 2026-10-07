# Denso D3 — Tài liệu cấu trúc Project

Tài liệu mô tả cấu trúc thư mục, từng module và luồng dữ liệu của ứng dụng **Denso D3 — Liên kết chuỗi sản xuất và phân tích sự cố**.

> **Cập nhật (mở rộng D3):** bổ sung bối cảnh sản xuất, truy vết dữ liệu, hồ sơ kinh nghiệm
> và lịch sử sự cố. Chi tiết mapping bảng xem `docs/DATAMODEL.md`, truy vấn kiểm tra xem
> `docs/SQL_READONLY.md`.

## 1. Cây thư mục tổng quan

```
Denso_production_input/
├── .env                        # Cấu hình thật (KHÔNG commit, chứa mật khẩu DB)
├── .env.example                # Mẫu cấu hình để tham khảo
├── .gitignore
├── README.md                   # Hướng dẫn cài đặt & sử dụng cho người dùng cuối
├── requirements.txt            # Danh sách dependencies
├── run.py                      # Entry point duy nhất: python run.py
├── pytest.ini                  # Cấu hình pytest
├── app/                        # Mã nguồn chính
│   ├── __init__.py
│   ├── main.py                 # Khởi tạo FastAPI, lifespan, exception handler, routes
│   ├── settings.py             # Đọc/kiểm tra cấu hình từ .env
│   ├── security.py             # Băm mật khẩu (PBKDF2) + token phiên
│   ├── auth.py                 # Middleware xác thực + dependency user/roles
│   ├── database.py             # Kết nối PostgreSQL (Psycopg 3)
│   ├── migrations.py           # Migration có phiên bản + checksum
│   ├── query_loader.py         # Nạp SQL từ file YAML
│   ├── graph.py                # Đăng ký loại node/cạnh + kiểm tra quan hệ hợp lệ
│   ├── catalog.py              # Đặc tả danh mục nghiệp vụ (9 đối tượng)
│   ├── scenarios.py            # Dữ liệu demo cho 3 kịch bản mô phỏng (cũ)
│   ├── scenario_d3.py          # Dữ liệu DEMO-D3-01 (kịch bản chính mở rộng)
│   ├── exceptions.py           # Ngoại lệ nghiệp vụ dùng chung
│   ├── schemas.py              # Pydantic model (sản lượng + health)
│   ├── engine/                 # Lõi phân tích
│   │   ├── __init__.py
│   │   ├── impact_engine.py    # Duyệt đồ thị lan truyền tác động (BFS)
│   │   └── rules.py            # Nạp & kiểm tra quy tắc từ YAML
│   ├── services/               # Tầng nghiệp vụ (validate + điều phối)
│   │   ├── __init__.py
│   │   ├── analysis_service.py
│   │   ├── auth_service.py
│   │   ├── catalog_service.py
│   │   ├── context_verification_service.py
│   │   ├── dashboard_service.py
│   │   ├── graph_service.py
│   │   ├── incident_service.py
│   │   ├── operations_service.py
│   │   ├── production_service.py
│   │   ├── scenario_service.py
│   │   ├── scenario_d3_service.py
│   │   ├── scenario_ambiguous_service.py
│   │   ├── survey_service.py
│   │   ├── system_service.py
│   │   └── task_service.py
│   ├── repositories/           # Tầng truy cập dữ liệu (SQL thuần)
│   │   ├── __init__.py
│   │   ├── analysis_repository.py
│   │   ├── catalog_repository.py
│   │   ├── context_repository.py   # Bảng mới 0007 (context/buffer/capacity/mapping/ingestion/experience/users)
│   │   ├── graph_repository.py
│   │   ├── incident_repository.py
│   │   ├── operations_repository.py
│   │   ├── production_repository.py
│   │   ├── system_repository.py
│   │   └── task_repository.py
│   ├── routers/                # Tầng API (định nghĩa endpoint)
│   │   ├── __init__.py
│   │   ├── analysis.py
│   │   ├── auth.py             # Đăng nhập/đăng xuất/người dùng/quản lý tài khoản
│   │   ├── catalog.py
│   │   ├── context.py          # API bối cảnh/đệm/công suất/mapping/kinh nghiệm
│   │   ├── dashboard.py
│   │   ├── graph.py
│   │   ├── health.py
│   │   ├── incidents.py
│   │   ├── operations.py
│   │   ├── production.py
│   │   ├── scenarios.py
│   │   ├── system.py
│   │   └── tasks.py
│   └── static/                 # Frontend thuần (không framework, không CDN)
│       ├── index.html
│       ├── app.js
│       ├── styles.css
│       └── favicon.svg
├── config/                     # Cấu hình khai báo (YAML)
│   ├── database.yaml           # SQL khởi tạo schema/bảng/index
│   ├── production_queries.yaml # SQL nghiệp vụ (insert/select/count/health)
│   └── rules.yaml              # Quy tắc phân tích sự cố
├── migrations/                 # Migration SQL có phiên bản
│   ├── 0001_catalog.sql
│   ├── 0002_system_layer.sql
│   ├── 0003_graph_edges.sql
│   ├── 0004_operations.sql
│   ├── 0005_incidents.sql
│   ├── 0006_analysis_tasks_survey.sql
│   ├── 0007_production_context.sql
│   └── 0008_auth_context.sql
├── scripts/                   # Script demo end-to-end
│   ├── demo_d3.py
│   └── create_user.py
├── docs/                       # Tài liệu
│   ├── Dữ liệu đầu vào.xlsx
│   ├── DATAMODEL.md
│   ├── SQL_READONLY.md
│   ├── USAGE_GUIDE.md
└── tests/                      # Kiểm thử (pytest)
    ├── __init__.py
    ├── conftest.py
    ├── helpers.py
    ├── test_api.py
    ├── test_d3_api.py
    ├── test_engine.py
    ├── test_queries.py
    ├── test_schemas.py
    └── test_service.py
```

## 2. Luồng khởi động

`run.py` là entry point duy nhất:

```
python run.py
  └─> from app.main import app
  └─> uvicorn.run(app, host, port)
        └─> lifespan (asynccontextmanager)
              ├─> get_settings()            # đọc .env
              ├─> load_all()                # nạp 2 file YAML SQL
              ├─> load_rules()              # nạp rules.yaml
              ├─> ProductionRepository().init_schema()  # tạo schema + bảng sản lượng
              └─> run_migrations()          # chạy migration chưa áp dụng
```

Nếu bất kỳ bước nào thất bại (sai `.env`, PostgreSQL không chạy, migration lỗi), ứng dụng dừng và báo lỗi rõ ràng — không tiếp tục với schema dở dang.

## 3. Kiến trúc phân lớp

Toàn bộ ứng dụng tuân theo mô hình **Router → Service → Repository → Database**:

```
HTTP Request
    │
    ▼
Router (app/routers/)          # Định nghĩa endpoint, parse query/body, trả response
    │
    ▼
Service (app/services/)        # Nghiệp vụ: validate dữ liệu, kiểm tra tham chiếu, điều phối
    │
    ▼
Repository (app/repositories/) # Truy cập dữ liệu: SQL thuần, bind tham số
    │
    ▼
PostgreSQL (app/database.py)   # Psycopg 3, mỗi thao tác mở connection riêng
```

- **Router** chỉ lo HTTP: nhận dữ liệu, gọi service, trả JSON.
- **Service** chứa logic nghiệp vụ và validation (dữ liệu phải là dict, kiểm tra tham chiếu tồn tại, chuẩn hóa chuỗi...).
- **Repository** chứa SQL và bind tham số bằng `%(name)s` — chống SQL injection.
- **Engine** (`app/engine/`) được service `analysis_service` gọi để duyệt đồ thị và chọn giả thuyết.
- **Config YAML** tách riêng: SQL nằm trong YAML, quy tắc phân tích nằm trong YAML khác — không nhúng vào code.

## 4. Chi tiết từng module

### 4.1. Thư mục gốc

| File | Vai trò |
|---|---|
| `run.py` | Entry point duy nhất; in URL giao diện/API; gọi `uvicorn.run`. |
| `requirements.txt` | fastapi, uvicorn, psycopg, pydantic, python-dotenv, PyYAML, pytest, httpx. |
| `.env` / `.env.example` | Cấu hình app + kết nối PostgreSQL + các giá trị điều chỉnh nghiệp vụ. |
| `pytest.ini` | Cấu hình pytest (bỏ qua warning Starlette). |

### 4.2. `app/` — mã nguồn chính

| File | Vai trò |
|---|---|
| `main.py` | Tạo FastAPI app (title "Denso D3", version 2.0.0). Định nghĩa `lifespan`, 6 exception handler (503/409/404/422), `include_router` cho 11 router, mount `/static`, route `/` (trả index.html) và `/favicon.ico`. |
| `settings.py` | Đọc `.env` bằng `dotenv`. Định nghĩa các hằng điều chỉnh (`MAX_QUANTITY`, `MATERIAL_LOW_THRESHOLD`, `DEFAULT_PAGE_SIZE`, `MAX_PAGE_SIZE`) và đường dẫn file/thư mục có thể ghi đè. Lớp `Settings` (dataclass frozen) đọc biến bắt buộc (`DB_*`) có kiểm tra khoảng giá trị. `get_settings()` có cache. |
| `database.py` | `connection_params()` và `get_connection()` dùng Psycopg 3 với `row_factory=dict_row`. Không giữ connection toàn cục. |
| `migrations.py` | Chạy migration có phiên bản từ thư mục `migrations/`. Bảng `schema_migrations` lưu version + checksum SHA-256. Chặn nếu file đã chạy bị sửa đổi; rollback nếu lỗi giữa chừng. |
| `query_loader.py` | Đọc YAML chứa SQL, kiểm tra cấu trúc (`queries` là dict, mỗi query có `description`/`fetch`/`sql`). Chỉ dùng `yaml.safe_load`. |
| `graph.py` | Định nghĩa 12 loại node (9 nghiệp vụ + 3 hệ thống), ánh xạ sang tên bảng và nhãn tiếng Việt, 4 loại cạnh. `validate_edge()` kiểm tra loại node/cạnh hợp lệ và quy tắc cặp (source,target) theo từng loại cạnh. |
| `catalog.py` | Đặc tả 9 đối tượng nghiệp vụ (`CATALOG_ENTITIES`): trường chung (code, name, description, active, is_simulated), trường riêng và khóa ngoại của từng đối tượng. `all_fields()` trả spec đầy đủ cho validation. |
| `scenarios.py` | Dữ liệu demo cho 3 kịch bản: danh mục, cạnh đồ thị, nguồn/dataset/field/luồng, vận hành (downtime/state/QC/vật tư) và 3 sự cố (`INC-001/002/003`). Tất cả `is_simulated=True`. |
| `exceptions.py` | 6 ngoại lệ nghiệp vụ: `DatabaseUnavailableError`, `DuplicateRequestError`, `RecordConflictError`, `DuplicateCodeError`, `NotFoundError`, `ValidationFailedError`. |
| `schemas.py` | Pydantic model cho form sản lượng (`ProductionRecordCreate` với `StrictInt`, trim chuỗi, tổng > 0) và các response (`RecordData`, `ListResponse`, `HealthResponse`...). |

### 4.3. `app/engine/` — lõi phân tích

| File | Vai trò |
|---|---|
| `impact_engine.py` | `build_adjacency()` xây danh sách kề. `traverse()` duyệt BFS với `visited` set (chống lặp vô hạn khi có chu trình), phân loại `DIRECT`/`INDIRECT`; cạnh không truyền tác động được ghi là `RISK`. `evaluate_condition()` hỗ trợ các toán tử `eq/ne/gt/lt/gte/lte/in/exists`. `select_hypotheses()` lọc giả thuyết theo điều kiện. |
| `rules.py` | Nạp `rules.yaml` (cache), kiểm tra cấu trúc rule và giới hạn toán tử (`ALLOWED_OPS`), không dùng `eval`. `matching_rules()` lọc rule theo `incident_type`. |

### 4.4. `app/services/` — tầng nghiệp vụ (11 file)

| File | Vai trò |
|---|---|
| `production_service.py` | Ghi nhận sản lượng: chống trùng theo `request_id` (idempotent), tự tính `total_quantity` và `defect_rate`, conflict nếu cùng request_id nhưng nội dung khác. |
| `dashboard_service.py` | Tổng hợp dashboard: chỉ số chính (sự cố mở, công việc TODO, máy dừng, sản lượng, tỷ lệ lỗi), checklist thiết lập, độ mới dữ liệu (theo `FRESHNESS_THRESHOLDS`), danh sách sự cố/công việc. |
| `catalog_service.py` | CRUD chung 9 danh mục: `clean_payload()` kiểm tra trường theo spec, kiểm tra tham chiếu khóa ngoại tồn tại. |
| `graph_service.py` | Quản lý cạnh đồ thị: làm sạch dữ liệu, `validate_edge()`, kiểm tra node nguồn/đích tồn tại (chống mồ côi). |
| `incident_service.py` | Sự cố: tạo (chống trùng theo `request_id`), cập nhật có giới hạn trường, nguyên nhân (giả thuyết/đã xác nhận), liên kết bản ghi vận hành. |
| `operations_service.py` | Ghi nhận vận hành: trạng thái máy, dừng máy (end >= start), QC (defect <= inspected), vật tư. Kiểm tra tham chiếu tồn tại. |
| `system_service.py` | Lớp hệ thống: nguồn, dataset, trường, luồng. Kiểm tra tham chiếu, cấm xóa nguồn đang có dataset, dataset nguồn ≠ đích. |
| `task_service.py` | Công việc theo bộ phận: tạo/cập nhật/chuyển trạng thái TODO/IN_PROGRESS/DONE/DISMISSED. |
| `survey_service.py` | Khảo sát 9 nhóm (G1–G9) với câu hỏi mặc định, tự seed khi truy cập. |
| `scenario_service.py` | Nạp dữ liệu demo (chủ động, không tự động, không trùng), dựng đầy đủ danh mục/cạnh/hệ thống/vận hành/sự cố. |
| `analysis_service.py` | Điều phối phân tích: trích tín hiệu từ dữ liệu vận hành, gọi `traverse()` + `select_hypotheses()`, định lượng sản lượng mất (thời gian × tốc độ), lưu vết vào `analysis_runs` + các bảng con. |

### 4.5. `app/repositories/` — tầng dữ liệu (8 file)

Mỗi repository tương ứng một nhóm bảng, chứa SQL thuần và luôn bind tham số. Tên gọi phản ánh chức năng:

| File | Phụ trách bảng |
|---|---|
| `production_repository.py` | `production.production_records` (+ `init_schema()`) |
| `catalog_repository.py` | 9 bảng danh mục |
| `system_repository.py` | `data_sources`, `datasets`, `dataset_fields`, `data_flows` |
| `graph_repository.py` | `graph_edges`, truy vấn node từ các bảng danh mục |
| `operations_repository.py` | `machine_states`, `machine_downtimes`, `qc_results`, `material_statuses` |
| `incident_repository.py` | `incidents`, `incident_causes`, `incident_links` |
| `analysis_repository.py` | `analysis_runs`, `analysis_impacts`, `analysis_hypotheses`, `analysis_actions` |
| `task_repository.py` | `action_tasks`, `survey_items` |

### 4.6. `app/routers/` — tầng API (11 router)

| Router | Prefix | Chức năng |
|---|---|---|
| `production.py` | `/api/production-records` | Nhập & xem báo cáo sản lượng (POST idempotent, GET có lọc/phân trang). |
| `health.py` | `/api/health` | Kiểm tra sức khỏe app + database. |
| `dashboard.py` | `/api/dashboard` | Số liệu tổng quan. |
| `catalog.py` | `/api/catalog` | CRUD chung 9 danh mục. |
| `system.py` | `/api/system` | Nguồn dữ liệu, dataset, trường, luồng. |
| `graph.py` | `/api/graph` | Cạnh + bản đồ liên kết (`/meta`, `/map`). |
| `operations.py` | `/api/operations` | Trạng thái máy, dừng máy, QC, vật tư. |
| `incidents.py` | `/api/incidents` | Sự cố, nguyên nhân, liên kết. |
| `analysis.py` | `/api/analysis` | Phân tích (`/run`, `/whatif`, `/runs`). |
| `tasks.py` | `/api/tasks` | Công việc theo bộ phận. |
| `scenarios.py` | `/api/scenarios`, `/api/survey` | Kịch bản mô phỏng + khảo sát. |

### 4.7. `app/static/` — frontend

| File | Vai trò |
|---|---|
| `index.html` | Khung SPA: header, sidebar, view chính, modal, toast. |
| `app.js` | Logic hiển thị, gọi API bằng URL tương đối (cùng origin). |
| `styles.css` | Toàn bộ CSS. |
| `favicon.svg` | Icon. |

Không dùng framework, không phụ thuộc CDN/Internet.

## 5. Cấu hình khai báo (YAML)

### `config/database.yaml`
SQL khởi tạo schema `production`, bảng `production_records` và index. Chỉ dùng `CREATE ... IF NOT EXISTS`, không DROP/TRUNCATE/reset dữ liệu. Các ràng buộc CHECK chặt chẽ (shift, số lượng, tổng > 0).

### `config/production_queries.yaml`
SQL nghiệp vụ của form sản lượng: `insert_record`, `find_by_request_id`, `find_by_id`, `list_records`, `count_records`, `health_check`. Luôn bind tham số bằng `%(name)s`.

### `config/rules.yaml`
Quy tắc phân tích (tách khỏi YAML SQL). Mỗi rule có `id`, `name`, `incident_type`, `propagate_kinds`, `departments`, `actions`, `priority`, `assumptions`, `hypotheses` (điều kiện + nội dung + bằng chứng + cần kiểm tra thêm). Các rule demo: `R_MACHINE_STOP`, `R_QUALITY`, `R_MATERIAL_SHORTAGE`, `R_DATA_DELAY`, `R_OTHER`.

## 6. Migrations

6 file SQL chạy tuần tự, mỗi file đặt tên `NNNN_name.sql`:

| File | Nội dung |
|---|---|
| `0001_catalog.sql` | 9 bảng danh mục nghiệp vụ. |
| `0002_system_layer.sql` | `data_sources`, `datasets`, `dataset_fields`, `data_flows`. |
| `0003_graph_edges.sql` | Bảng `graph_edges` + index (node/edge hai lớp). |
| `0004_operations.sql` | `machine_states`, `machine_downtimes`, `qc_results`, `material_statuses`. |
| `0005_incidents.sql` | `incidents`, `incident_causes`, `incident_links`. |
| `0006_analysis_tasks_survey.sql` | `analysis_runs/impacts/hypotheses/actions`, `action_tasks`, `survey_items`. |
| `0007_production_context.sql` | `users`, `production_operations`, `buffer_snapshots`, `capacity_profiles`, `source_object_mappings`, `ingestion_records`, `incident_experiences`, `incident_history`, `analysis_related_incidents`; cột mới cho `incidents`, `analysis_impacts`, `action_tasks`. |
| `0008_auth_context.sql` | `users` (password_hash, failed_attempts, locked_until, last_login_at), `user_roles`, `sessions`, `incident_context_verifications`. |

## 7. Tests

`tests/` dùng pytest + httpx:

| File | Phạm vi |
|---|---|
| `conftest.py`, `helpers.py` | Fixture và helper chung. |
| `test_schemas.py` | Kiểm tra Pydantic model. |
| `test_queries.py` | Kiểm tra query loader / YAML. |
| `test_engine.py` | Kiểm tra engine phân tích (traverse, điều kiện, chọn giả thuyết). |
| `test_service.py` | Kiểm tra tầng service. |
| `test_api.py`, `test_d3_api.py` | Kiểm tra API tích hợp. |

Lưu ý: phần kiểm thử tích hợp với PostgreSQL chỉ chạy được khi có database thật; không tuyên bố đã test tích hợp khi chỉ dùng mock.

## 8. Mô hình dữ liệu (PostgreSQL, schema `production`)

Xem chi tiết trong các file `migrations/*.sql`. Tóm tắt nhóm bảng:

- **Danh mục nghiệp vụ:** `departments`, `production_lines`, `processes`, `machines`, `materials`, `products`, `production_orders`, `lots`, `shifts`.
- **Lớp hệ thống:** `data_sources`, `datasets`, `dataset_fields`, `data_flows`.
- **Đồ thị:** `graph_edges` (nối hai lớp, 4 loại cạnh).
- **Vận hành:** `machine_states`, `machine_downtimes`, `qc_results`, `material_statuses`.
- **Sự cố & phân tích:** `incidents`, `incident_causes`, `incident_links`, `analysis_runs`, `analysis_impacts`, `analysis_hypotheses`, `analysis_actions`.
- **Công việc & khảo sát:** `action_tasks`, `survey_items`.
- **Nội bộ:** `schema_migrations` (theo dõi migration), `production.production_records` (form sản lượng cũ, không có `is_simulated`).

Mọi bảng nghiệp vụ (trừ `production_records`) đều có cột `is_simulated` để tách dữ liệu demo khỏi dữ liệu thật.

## 9. Quy ước & điểm cần lưu ý khi chỉnh sửa

- **Ngôn ngữ:** mã nguồn và giao diện dùng tiếng Việt; docstring tiếng Việt.
- **SQL:** giữ trong YAML (trừ migration), luôn bind tham số — không ghép chuỗi/f-string.
- **Quy tắc:** giữ trong `rules.yaml`, không dùng `eval`.
- **Khởi động:** chỉ `python run.py`; không cần server riêng.
- **Dữ liệu demo:** `is_simulated=True`, chỉ nạp khi bấm nút, có nhãn "Dữ liệu mô phỏng — chưa xác nhận bởi Denso".
- **Chống trùng:** các thao tác tạo quan trọng dùng `request_id` (UUID) unique.
- **Thay đổi schema:** dùng migration có phiên bản, không chỉ `CREATE TABLE IF NOT EXISTS`.
- **Không phụ thuộc Internet/CDN:** frontend thuần, thư viện (nếu dùng) phải đóng gói local.
