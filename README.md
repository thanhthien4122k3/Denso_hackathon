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

Copy toàn bộ thư mục **`Denso_production_input`** vào máy tính của bạn (ví dụ `C:\Denso_production_input`).

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

## C. Dùng thử ngay (3 bước)

1. Bấm menu **9. Kịch bản mô phỏng** → **Nạp dữ liệu demo**.
2. Bấm menu **7. Phân tích tác động** → chọn sự cố `INC-001` → **Chạy phân tích**.
3. Xem kết quả: đối tượng bị ảnh hưởng, đường lan truyền, nguyên nhân gợi ý, việc cần làm.

## Các menu chính

| Menu | Dùng để làm gì |
|---|---|
| 1. Tổng quan | Xem số liệu nhanh |
| 2. Danh mục sản xuất | Thêm/sửa bộ phận, chuyền, công đoạn, máy, vật tư... |
| 3. Nguồn dữ liệu | Khai báo hệ thống MES/ERP, dataset, trường, luồng |
| 4. Ghi nhận vận hành | Nhập sản lượng, trạng thái máy, dừng máy, QC, vật tư |
| 5. Quản lý sự cố | Tạo sự cố, ghi nguyên nhân |
| 6. Bản đồ liên kết | Xem sơ đồ quan hệ máy/công đoạn/vật tư/dữ liệu |
| 7. Phân tích tác động | Chạy phân tích và xem kết quả |
| 8. Hành động theo bộ phận | Quản lý công việc |
| 9. Kịch bản mô phỏng | Nạp dữ liệu demo, thử 3 tình huống |
| 10. Thông tin khảo sát | Ghi các câu hỏi cần xác nhận với nhà máy |

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
