# Denso D3 — Hướng dẫn cài đặt và sử dụng

Ứng dụng **nhập liệu sản xuất** và **phân tích sự cố**, chạy trong mạng nội bộ.
Làm đúng theo các bước bên dưới trên **một máy tính mới** là chạy được.

---

## A. Cài đặt lần đầu (làm 1 lần)

### Bước 1: Cài Python 3.11

1. Vào <https://www.python.org/downloads/> tải bản **Python 3.11** cho Windows.
2. Chạy file cài, **tích chọn** ô **"Add Python to PATH"** rồi bấm **Install Now**.

Kiểm tra đã cài xong: mở PowerShell gõ:

```powershell
py -3.11 --version
```

### Bước 2: Cài PostgreSQL 16

1. Vào <https://www.enterprisedb.com/downloads/postgres-postgresql-downloads> tải **PostgreSQL 16** cho Windows.
2. Chạy file cài, để mặc định, **nhớ mật khẩu** bạn đặt cho tài khoản `postgres` (mật khẩu này sẽ dùng ở Bước 5).
3. Kết thúc cài đặt, bỏ chọn Stack Builder (không cần).

### Bước 3: Tạo database

Mở **SQL Shell (psql)** (có sẵn sau khi cài PostgreSQL) rồi gõ:

```
Server [localhost]:           (bấm Enter)
Database [postgres]:          (bấm Enter)
Port [5432]:                  (bấm Enter)
Username [postgres]:          (bấm Enter)
Password:                     (gõ mật khẩu postgres đã đặt ở Bước 2)
```

Sau khi vào, gõ lệnh tạo database:

```sql
CREATE DATABASE denso_hackathon;
```

Gõ `\q` để thoát.

> **Cách khác (dùng pgAdmin):** mở pgAdmin → chuột phải **Databases** → **Create** → **Database**,
> đặt tên `denso_hackathon` → Save.

### Bước 4: Lấy thư mục project

Clon repo **`Denso_hackathon`** vào máy tính của bạn (ví dụ `C:\Denso_hackathon`).

### Bước 5: Cài thư viện và cấu hình

Mở PowerShell, gõ:

```powershell
cd C:\Denso_production_input
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

Trong Notepad, sửa dòng:

```
DB_PASSWORD=CHANGE_ME
```

thành mật khẩu `postgres` bạn đã đặt ở Bước 2. Lưu và đóng.

> Nếu PostgreSQL của bạn không dùng `localhost`, cổng `5432` hay tài khoản `postgres`,
> sửa luôn các dòng `DB_HOST`, `DB_PORT`, `DB_USER` cho khớp.

**Các giá trị tùy chỉnh khác (không bắt buộc, có thể bỏ qua):**

| Biến trong `.env` | Ý nghĩa | Mặc định |
|---|---|---|
| `APP_PORT` | Cổng chạy ứng dụng | `8000` |
| `MAX_QUANTITY` | Số lượng tối đa mỗi ô (đạt/lỗi) | `1000000000` |
| `MATERIAL_LOW_THRESHOLD` | Ngưỡng cảnh báo thiếu vật tư | `50` |
| `QC_DEFECT_RATE_THRESHOLD` | Ngưỡng cảnh báo tỷ lệ lỗi QC (%) | `5` |
| `DEFAULT_PAGE_SIZE` | Số dòng mỗi trang danh sách | `20` |
| `MAX_PAGE_SIZE` | Số dòng tối đa mỗi trang | `100` |
| `DATABASE_YAML_PATH` | File SQL khởi tạo bảng | `config/database.yaml` |
| `PRODUCTION_QUERIES_YAML_PATH` | File SQL sản lượng | `config/production_queries.yaml` |
| `RULES_YAML_PATH` | File quy tắc phân tích | `config/rules.yaml` |
| `MIGRATIONS_DIR` | Thư mục migration | `migrations` |
| `STATIC_DIR` | Thư mục giao diện | `app/static` |

> Đường dẫn file/thư mục: để trống là dùng mặc định; muốn đổi thì ghi đường dẫn tuyệt đối
> (hoặc tương đối so với thư mục dự án).

---

## B. Chạy ứng dụng

Mỗi lần dùng, mở PowerShell:

```powershell
cd C:\Denso_production_input
.\.venv\Scripts\Activate.ps1
python run.py
```

Mở trình duyệt: **http://localhost:8000**

> Tắt app: bấm `Ctrl + C`.
> Lần đầu chạy, ứng dụng tự tạo bảng trong database (không xóa dữ liệu cũ).

---

## B.1. Đăng nhập và tạo tài khoản

Ứng dụng có đăng nhập bắt buộc. Mở **http://localhost:8000** sẽ hiện trang đăng nhập.

### Tạo tài khoản quản trị đầu tiên (làm 1 lần)

Mở PowerShell thứ hai (cùng thư mục project, đã kích hoạt `.venv`):

```powershell
python scripts/create_user.py
```

Làm theo hướng dẫn để nhập:
- Tên đăng nhập (ví dụ `admin`).
- Tên hiển thị.
- Vai trò: nhập `ADMIN`.
- Mật khẩu (gõ, không hiện lên màn hình).

### Tài khoản mặc định (đã tạo sẵn)

Nếu đã chạy bước tạo tài khoản demo, có sẵn 4 tài khoản theo từng vai trò, mật khẩu mặc định **`123456`**:

| Tên đăng nhập | Vai trò |
|---|---|
| `recorder` | OPERATOR (người ghi nhận) |
| `handler` | HANDLER (người xử lý) |
| `coordinator` | COORDINATOR (người điều phối) |
| `admin` | ADMIN (quản trị) |

### Đăng nhập

1. Mở **http://localhost:8000**.
2. Nhập tên đăng nhập và mật khẩu (mặc định `123456`) → bấm **Đăng nhập**.

### Các vai trò (phân quyền tối thiểu)

| Vai trò | Được làm gì |
|---|---|
| `OPERATOR` | Nhập vận hành, báo cáo sự cố (người ghi nhận) |
| `HANDLER` | Tiếp nhận và cập nhật công việc được giao |
| `COORDINATOR` | Xác minh bối cảnh, xác nhận khôi phục, đóng hồ sơ |
| `ADMIN` | Quản lý tài khoản, danh mục, cấu hình, quy tắc |

Sau khi đăng nhập bằng `ADMIN`, vào menu **Tài khoản & quyền** để tạo thêm tài khoản
hoặc dùng bộ tài khoản demo (xem bên dưới).

> Mật khẩu được băm (PBKDF2-SHA256), phiên dùng cookie. Không lưu mật khẩu dạng văn bản.
> Mật khẩu mặc định `123456` chỉ dùng cho môi trường nội bộ/demo — nên đổi lại trước khi đưa vào sử dụng thật.

### Hướng dẫn chi tiết từng bước

Xem tài liệu đầy đủ: **`docs/USAGE_GUIDE.md`** (khởi động → tạo tài khoản → đăng nhập →
nạp mô phỏng → nhập lỗi → phân tích → xác minh → đóng hồ sơ).

Mô tả chi tiết từng trường trong **Bản đồ liên kết** và **Phân tích tác động**:
**`docs/ANALYSIS_REFERENCE.md`**.

---

## C. Dùng thử ngay (3 bước)

> Cần đăng nhập trước (xem mục B.1).

1. Bấm menu **Kịch bản mô phỏng** (nhóm *Phân tích*) → **Nạp dữ liệu demo**.
2. Bấm menu **Phân tích tác động** → chọn sự cố `INC-001` → **Chạy phân tích**.
3. Xem kết quả: đối tượng bị ảnh hưởng, đường lan truyền, nguyên nhân gợi ý, việc cần làm.

## Các menu chính

| Nhóm | Menu | Dùng để làm gì |
|---|---|---|
| Tổng quan | Trung tâm vận hành | Xem số liệu nhanh |
| Vận hành | Ghi nhận dữ liệu | Nhập sản lượng, trạng thái máy, dừng máy, QC, vật tư |
| Vận hành | Sự cố | Tạo sự cố, ghi nguyên nhân, xác minh bối cảnh, đóng hồ sơ |
| Vận hành | Công việc theo bộ phận | Quản lý công việc |
| Phân tích | Bản đồ liên kết | Xem sơ đồ quan hệ máy/công đoạn/vật tư/dữ liệu |
| Phân tích | Phân tích tác động | Chạy phân tích và xem kết quả |
| Phân tích | Bảng gợi ý theo bộ phận | Xem hành động đề xuất của 3 tình huống, xếp theo bộ phận |
| Phân tích | Kịch bản mô phỏng | Nạp dữ liệu demo, thử tình huống |
| Thiết lập dữ liệu | Danh mục sản xuất | Thêm/sửa bộ phận, chuyền, công đoạn, máy, vật tư... |
| Thiết lập dữ liệu | Nguồn dữ liệu & ánh xạ | Khai báo hệ thống MES/ERP, dataset, trường, luồng |
| Thiết lập dữ liệu | Khảo sát & xác nhận | Ghi các câu hỏi cần xác nhận với nhà máy |
| Thiết lập dữ liệu | Tài khoản & quyền | Quản lý tài khoản (chỉ ADMIN) |

> Dữ liệu demo có nhãn **"Dữ liệu mô phỏng — chưa xác nhận bởi Denso"**, không trộn với dữ liệu thật.

---

## D. Mở từ điện thoại Android

1. Trên máy tính gõ `ipconfig`, tìm IP (ví dụ `192.168.1.10`).
2. Điện thoại cùng mạng Wi-Fi, mở trình duyệt: `http://192.168.1.10:8000`.
3. Không vào được? Do Wi-Fi chặn kết nối giữa thiết bị (client isolation) hoặc tường lửa chưa mở cổng 8000.

---

## E. Gặp lỗi?

- **"Không thể kết nối PostgreSQL"**: kiểm tra `.env` (mật khẩu `DB_PASSWORD`), kiểm tra dịch vụ PostgreSQL đang chạy.
- **Trang không hiển thị dữ liệu**: tải lại bằng `Ctrl + F5`.
- **Tài liệu API** (cho người phát triển): mở `http://localhost:8000/docs`.

---

## F. Chạy kiểm thử (cho người phát triển)

Kiểm thử tích hợp cần một **database test riêng** (mặc định `denso_hackathon_test`), không dùng database thật.

```powershell
cd C:\Denso_hackathon
.\.venv\Scripts\Activate.ps1
$env:TEST_DB_NAME = "denso_hackathon_test"   # tên database test (mặc định)
python -m pytest -q
```

- Nếu chưa có database test, conftest sẽ tự tạo rồi chạy migration/seed.
- Không chạy test khi biến `DB_NAME` đang trỏ vào database thật (production).
- Test sẽ **skip** nếu không kết nối được PostgreSQL.
