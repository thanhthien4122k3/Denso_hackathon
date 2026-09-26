# Denso D3 — Liên kết chuỗi sản xuất và phân tích sự cố

Mở rộng từ ứng dụng **Denso Production Input** (ghi nhận sản lượng công đoạn) thành
hệ thống thử nghiệm liên kết hai lớp (logic hệ thống + nghiệp vụ sản xuất) và phân
tích ảnh hưởng lan truyền, đề xuất nguyên nhân và hành động theo bộ phận.

- Backend: Python 3.11, FastAPI, Uvicorn, Psycopg 3, Pydantic v2.
- Database: PostgreSQL 16 (dùng bảng node/edge để lưu đồ thị; phân tích đồ thị bằng Python).
- Frontend: HTML/CSS/JS thuần, không phụ thuộc CDN, không cần Internet.
- Không dùng Neo4j/Spark/Kafka/ML. Đây là bản thử nghiệm, **không** phải hệ thống dự báo đã kiểm chứng tại nhà máy.

## Cấu trúc dự án (phần mở rộng D3)

```
Denso_production_input/
├── run.py                          # python run.py
├── migrations/                     # migration có phiên bản (chạy có kiểm soát lúc khởi động)
│   ├── 0001_catalog.sql
│   ├── 0002_system_layer.sql
│   ├── 0003_graph_edges.sql
│   ├── 0004_operations.sql
│   ├── 0005_incidents.sql
│   └── 0006_analysis_tasks_survey.sql
├── config/
│   ├── database.yaml               # SQL khởi tạo bảng sản lượng gốc
│   ├── production_queries.yaml     # SQL insert/select sản lượng
│   └── rules.yaml                  # quy tắc nghiệp vụ (tách riêng khỏi SQL)
├── app/
│   ├── migrations.py               # runner migration + schema_migrations
│   ├── graph.py                    # đăng ký loại node/cạnh + kiểm tra quan hệ
│   ├── catalog.py                  # metadata 9 danh mục nghiệp vụ
│   ├── scenarios.py                # bộ dữ liệu mô phỏng 3 kịch bản
│   ├── engine/
│   │   ├── rules.py                # nạp quy tắc YAML (không eval)
│   │   └── impact_engine.py        # duyệt đồ thị + đánh giá điều kiện
│   ├── repositories/               # catalog, graph, system, operations, incident, analysis, task
│   ├── services/                   # nghiệp vụ + phân tích + kịch bản + khảo sát
│   ├── routers/                    # catalog, system, graph, operations, incidents,
│   │                               # analysis, tasks, scenarios, survey, dashboard, ...
│   └── static/                     # SPA 10 mục
└── tests/                          # test_engine.py, test_d3_api.py, ... (67 test)
```

## Cài đặt (PowerShell)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env   # điền DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
```

Không cần cài thêm dependencies mới cho phần D3 (dùng psycopg/yaml sẵn có).

## Chạy (một lệnh duy nhất)

```powershell
python run.py
```

Mở <http://localhost:8000> (Swagger tại <http://localhost:8000/docs>). Khi khởi động,
ứng dụng chạy migration có phiên bản (chỉ áp dụng file chưa chạy, ghi vào `schema_migrations`),
tạo schema/bảng nếu chưa có và không xóa dữ liệu đã có.

Truy cập từ Android: `ipconfig` lấy IP LAN, mở `http://<IP-LAN>:8000`; mở inbound TCP 8000
chỉ trong mạng Private/subnet tin cậy. Không mở cổng 5432, không port-forward ra Internet.

## Nạp dữ liệu demo (3 kịch bản)

Vào menu **9. Kịch bản mô phỏng** → bấm **Nạp dữ liệu demo**. Việc nạp là **chủ động**
(không tự chạy khi khởi động) và **không tạo trùng** khi nạp lại. Toàn bộ dữ liệu demo có
cờ `is_simulated = TRUE` và hiển thị nhãn **"Dữ liệu mô phỏng — chưa xác nhận bởi Denso"**.

## Thao tác từng kịch bản (từ đầu đến kết quả)

1. **Nạp demo** (menu 9).
2. Vào menu **7. Phân tích tác động**, chọn sự cố `INC-001/002/003` (hoặc bấm "Chạy phân
   tích kịch bản này" ở menu 9), nhập tùy chọn *thời lượng dừng* và *tốc độ* rồi **Chạy phân tích**.
3. Đọc kết quả: **ảnh hưởng** (DIRECT/INDIRECT/RISK/ESTIMATED), **đường lan truyền** dạng chữ,
   **giả thuyết nguyên nhân**, **hành động theo bộ phận**, **định lượng** (nếu đủ tham số).

| Kịch bản | Sự cố | Kết quả dự kiến |
|---|---|---|
| S1: Máy lắp ráp dừng | `INC-001` | M-01 → ASSY-01 (trực tiếp) → TEST-01, PACK-01 (gián tiếp); gợi ý Bảo trì + Kế hoạch |
| S2: Lot lỗi QC cao | `INC-002` | LOT-001 → order/product có nguy cơ; gợi ý QC + Kho |
| S3: Thiếu vật tư | `INC-003` | MAT-100 → công đoạn/lệnh liên quan; gợi ý Kho + Kế hoạch |

## Đọc đường lan truyền và bằng chứng

- **Đường lan truyền**: mỗi ảnh hưởng có `path` (danh sách các bước `từ → đến (loại cạnh)`),
  hiển thị dạng chữ để đọc được trên màn hình nhỏ.
- **Bằng chứng**: ảnh hưởng dựa trên cạnh đồ thị; giả thuyết dựa trên tín hiệu quan sát được
  (mã lỗi, kết quả QC, mức vật tư, dataset chậm). `rule_id` cho biết quy tắc đã áp dụng.

## Phân biệt giả thuyết với nguyên nhân đã xác nhận

- Engine chỉ tạo **giả thuyết** (`kind = HYPOTHESIS`) — không tự ghi là nguyên nhân đã xác nhận.
- Người dùng tự xác nhận trong **menu 5 → Chi tiết sự cố**, thêm nguyên nhân với `kind = CONFIRMED`
  và người xác nhận. Kết quả engine luôn kèm ghi chú "chưa được xác nhận".

## Các chức năng đã làm

- **10 menu** đầy đủ: Tổng quan, Danh mục, Nguồn dữ liệu & liên kết, Ghi nhận vận hành,
  Quản lý sự cố, Bản đồ liên kết (SVG local), Phân tích tác động, Hành động theo bộ phận,
  Kịch bản mô phỏng, Thông tin khảo sát.
- **Danh mục** 9 đối tượng (thêm/xem/sửa/ngừng), quan hệ qua cạnh đồ thị có kiểm tra loại hợp lệ.
- **Lớp hệ thống**: nguồn (MES/ERP/PLC/...), dataset, trường, luồng, ánh xạ dữ liệu–nghiệp vụ.
- **Ghi nhận vận hành**: trạng thái máy, dừng máy (không nhận end < start), QC (lỗi ≤ kiểm tra),
  vật tư; giữ nguyên form sản lượng cũ. Mỗi bản ghi có `event_time` và `received_at` riêng.
- **Engine**: duyệt đồ thị có `visited` (chống chu trình), đúng chiều/loại cạnh, không cộng lặp,
  phân loại DIRECT/INDIRECT/RISK/OBSERVED/ESTIMATED, định lượng chỉ khi đủ 2 tham số.
- **Lưu vết**: mỗi lần phân tích lưu run + impacts + hypotheses + actions (snapshot).
- **Migration có phiên bản**, lỗi thì báo rõ và không chạy tiếp với schema dở dang.

## Kiểm thử đã chạy

```powershell
python -m pytest -q   # 67 passed
```

- `test_engine.py`: lan truyền đúng chiều/loại cạnh, đồ thị có chu trình, không cộng lặp,
  cạnh ánh xạ không lan truyền (RISK), toán tử điều kiện.
- `test_d3_api.py` (integration, chạy trên DB test `denso_hackathon_test`): CRUD danh mục,
  nạp demo không trùng, bản đồ, kiểm tra cạnh, chống trùng sự cố, 3 kịch bản, định lượng,
  chu trình, tách demo/thật, công việc, khảo sát, form sản lượng cũ vẫn chạy.
- Integration test chỉ chạy trên database test riêng; nếu không có PostgreSQL sẽ **skip**,
  không đụng dữ liệu thật.

## Giới hạn trước khi dùng thật

- Engine dùng quy tắc có thể giải thích, **chưa** dùng ML; không tuyên bố dự báo đã kiểm chứng.
- Ngưỡng thiếu vật tư, công thức "dừng × tốc độ" là **giá trị demo**; chưa xét tồn đệm, sản xuất bù, máy thay thế.
- Chưa có HTTPS nội bộ, đăng nhập/phân quyền, tài khoản DB ít quyền, sao lưu.
- Chưa kết nối thật với MES/ERP/PLC — chỉ lưu metadata (đã phân biệt nguồn đã/xuất khai báo qua cờ `confirmed`).
- Đây là bản thử nghiệm để **khảo sát**; các giả định demo không phải câu trả lời chính thức của Denso.

## Thông tin cần khảo sát thêm tại Denso (menu 10)

Chín nhóm: quy trình & phụ thuộc; ảnh hưởng khi sự cố; dữ liệu vận hành đang thu thập;
nơi phát sinh & phương thức thu thập; hệ thống lưu trữ & khóa liên kết; tần suất cập nhật;
cách xác định nguyên nhân & quy tắc xử lý; bộ phận nhận việc & hành động; ba tình huống thực tế.
Mỗi mục có trạng thái *chưa xác nhận/đã xác nhận*, người cung cấp và thời điểm.
