# Denso D3 — Hướng dẫn dùng thử (theo kịch bản mô phỏng)

Hướng dẫn thao tác từ khởi động đến đóng hồ sơ, dùng dữ liệu mô phỏng
`DEMO-D3-01` và `DEMO-D3-AMBIGUOUS-01`. Không đụng tới dữ liệu vận hành thật.

## 0. Khởi động và tạo tài khoản

```powershell
cd C:\Denso_production_input
.\.venv\Scripts\Activate.ps1
python run.py
```

Mở trình duyệt: **http://localhost:8000**

Tạo tài khoản quản trị đầu tiên (nhập mật khẩu an toàn, không hiện lên màn hình):

```powershell
python scripts/create_user.py
# Tên đăng nhập: admin
# Tên hiển thị: Quản trị
# Vai trò: ADMIN
# Mật khẩu: (gõ)
```

## 1. Nạp kịch bản mô phỏng và lấy tài khoản demo

Cách nhanh (tự sinh 4 tài khoản demo, in mật khẩu một lần):

```powershell
python scripts/demo_d3.py
```

Script in ra thông tin đăng nhập của `demo-recorder`, `demo-handler`,
`demo-coordinator`, `demo-admin` (mật khẩu sinh ngẫu nhiên, không lưu).

> Nếu dùng giao diện: đăng nhập bằng `admin`, vào **Kịch bản mô phỏng → Nạp dữ liệu mô phỏng**,
> sau đó tạo tài khoản demo ở **Tài khoản & quyền**.

## 2. Đăng nhập bằng người ghi nhận

1. Đăng xuất (nếu đang đăng nhập admin).
2. Đăng nhập bằng `demo-recorder` (vai trò OPERATOR — người ghi nhận).

## 3. Chọn chế độ Mô phỏng

- Ở header, bấm nút **Mô phỏng** (chuyển chế độ dữ liệu).
- Header và các màn hình hiện nhãn “Dữ liệu mô phỏng — chưa xác nhận bởi Denso”.

## 4. Nhập lỗi mới

Vào **Ghi nhận dữ liệu → Trạng thái máy** hoặc dùng API:

```http
POST /api/operations/report-machine-error
{
  "machine_id": <id của M10>, "event_time": "2026-10-06T10:00:00+07:00",
  "error_code": "E-DEMO-01",
  "observation": "Máy dừng, màn hình báo lỗi bộ phận cấp phôi",
  "is_simulated": true
}
```

> Endpoint này tạo đồng thời một sự kiện `STOPPED` và một khoảng dừng đang mở
> trong cùng transaction (không tạo hai khoảng dừng trùng).

Từ bản ghi, bấm **Báo cáo sự cố** (thông tin máy/thời điểm điền sẵn, không nhập lại ID).

## 5. Mở hồ sơ và chạy phân tích

1. Vào **Sự cố** → mở hồ sơ vừa tạo.
2. Bấm **Chạy phân tích tác động**.
3. Nhập giả định: **Thời lượng dừng = 15 phút**.

Kết quả hiển thị:
- **Bối cảnh sản xuất**: `MATCHED` với lô `LOT-B` tại công đoạn `P10` (không phải `LOT-A` đã rời máy trước 10:00).
- **Ước tính hàng đệm**: `60 ÷ 10 = 6 phút` → công đoạn sau có nguy cơ cạn hàng lúc `10:06`.
- **Ước tính công suất**: `15 × 12 = 180` (năng lực có nguy cơ, không phải thành phẩm chắc chắn mất).
- **Sự cố tương tự**: `INC-HIST-001` (khớp cùng máy + cùng mã lỗi).
- **Giả thuyết nguyên nhân**: `H_MACHINE_ERROR` (chỉ là giả thuyết, chưa xác nhận).
- **Hành động đề xuất**: MAINT, PROD, PLAN.

## 6. Mở “Vì sao?”

Bên mỗi kết luận (tác động/giả thuyết/ước tính) bấm **Vì sao?** để xem:
- Đường quan hệ đã dùng.
- Bằng chứng và thời điểm.
- Quy tắc + phiên bản.
- Công thức, tham số, đơn vị.
- Giả định và dữ liệu còn thiếu.

## 7. Quan sát trạng thái bối cảnh mơ hồ

Nạp scenario mơ hồ và chạy phân tích:

```http
POST /api/scenarios/d3-ambiguous/load
```

Sự cố `INC-AMB-01` (máy `AMB-M01`, hai lô `AMB-LOT-A`/`AMB-LOT-B` chồng lấn tại 10:00)
cho kết quả `AMBIGUOUS` với 2 ứng viên — hệ thống **không tự chọn** lô, vẫn phân tích
được mức máy/công đoạn.

## 8. Đăng nhập bằng người điều phối và xác minh

1. Đăng xuất, đăng nhập bằng `demo-coordinator`.
2. Mở hồ sơ `INC-AMB-01` → khối **Bối cảnh sản xuất** có bảng ứng viên + nút **Xác minh**.
3. Chọn một lô, nhập **lý do**, bấm **Xác minh** (bắt buộc lý do).
4. Backend lưu người xác minh, thời điểm, lựa chọn, lý do và snapshot ứng viên.

## 9. Chạy lại và đối chiếu

Chạy lại phân tích: bối cảnh chuyển sang `CONFIRMED`, dùng đúng lô đã chọn.
Lần chạy cũ vẫn giữ trạng thái `AMBIGUOUS` (snapshot bất biến, không sửa kết quả cũ).

## 10. Tạo và cập nhật công việc

1. Trong kết quả phân tích, bấm **Tạo công việc** ở một hành động đề xuất.
2. Công việc truy được `analysis_action_id` (chống trùng).
3. Vào **Công việc** để chuyển trạng thái TODO → IN_PROGRESS → DONE.

## 11. Xác nhận khôi phục

Đến 10:12 (người điều phối):
- Ghi nhận trạng thái máy `RUNNING` (hoặc qua API `POST /api/operations/machine-states`).
- Đóng khoảng dừng (`POST /api/operations/downtimes/{id}/close`).
- Trong hồ sơ, bấm **Xác nhận khôi phục** (ghi `recovered_at/by`).
- Chạy lại phân tích với 12 phút → `12 × 12 = 144` (ước tính năng lực).

> Nút **Xác nhận khôi phục**/**Đóng hồ sơ** chỉ hiện với `COORDINATOR`/`ADMIN`;
> tài khoản khác chỉ thấy dòng giải thích. Sau khi lưu, hồ sơ hiện thời điểm và
> người khôi phục, thẻ **Dòng thời gian** có dòng "Xác nhận khôi phục" kèm ghi chú.

## 12. Đóng hồ sơ theo quyền

Chỉ `COORDINATOR`/`ADMIN` đóng được hồ sơ:
- Bấm **Đóng hồ sơ**, nhập **tóm tắt kết quả xử lý** và **trạng thái nguyên nhân**
  (có thể để `UNKNOWN` nếu chưa xác định được — không bắt buộc bịa nguyên nhân).
- Sau khi đóng, hồ sơ về `RESOLVED`, hiện người đóng/thời điểm đóng, và hai nút
  thao tác biến mất (thay bằng dòng **Hồ sơ đã đóng**).

## Ví dụ request/response

Xem thêm `scripts/demo_d3.py` (chạy end-to-end qua API) và `docs/SQL_READONLY.md`
(truy vấn read-only đối chiếu JSON/DB/UI).

## Lưu ý bảo mật

- Mật khẩu được băm bằng PBKDF2-SHA256; phiên dùng cookie HttpOnly + SameSite.
- Không nhúng tài khoản/mật khẩu mặc định; không lưu token ở localStorage.
- Mọi thao tác thay đổi dữ liệu đều lấy danh tính từ phiên (không tin `user_id` do client gửi).
- Chế độ Mô phỏng tách biệt dữ liệu vận hành; backend kiểm tra phạm vi, không chỉ lọc bằng JS.
