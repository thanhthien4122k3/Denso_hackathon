# Kịch bản demo từng bước — Denso D3

Thời lượng: khoảng 5–7 phút. Toàn bộ dữ liệu là **mô phỏng** (chưa xác nhận bởi Denso).

> Trước khi bắt đầu: đã cài đặt app theo `README.md`, PostgreSQL đang chạy, tài khoản demo đã được nạp.

---

## Bước 0 — Chuẩn bị

- **Ai làm:** Admin (`demo-admin`).
- **Thao tác:**
  1. Chạy `python run.py`, mở `http://localhost:8000`, đăng nhập bằng `demo-admin` (hoặc tài khoản admin).
  2. Menu **Kịch bản mô phỏng** → bấm **Nạp dữ liệu mô phỏng**.
  3. Ghi lại mật khẩu 4 tài khoản demo trong hộp thoại "Tài khoản demo" (chỉ hiện một lần).
  4. Ở header, bật chế độ **Mô phỏng**.
- **Kết quả mong đợi:** màn hình hiện "Đã nạp.", xuất hiện nút "Xem Bản đồ liên kết" và gợi ý bước kế tiếp.
- **Lời dẫn:** "Đây là dữ liệu mô phỏng DEMO-D3-01 — một chuyền sản xuất có 3 công đoạn. Chúng ta sẽ thấy dữ liệu liên kết thế nào rồi mô phỏng một sự cố máy dừng."

---

## Bước 1 — Bức tranh tổng thể

- **Ai làm:** Admin.
- **Thao tác:** Menu **Bản đồ liên kết** → chế độ **Chuỗi sản xuất** → mở khung **"Cách đọc bản đồ"**.
- **Kết quả mong đợi:** đọc theo cột từ trái sang phải: Vật tư (MAT-100, MAT-200) → Máy (M10, M20, M30) → Công đoạn (Gia công, Kiểm tra, Đóng gói) → Chuyền LINE-01 → Sản phẩm SP-A/Lệnh PO-001/Lot LOT-A, LOT-B.
- **Lời dẫn:** "Mũi tên chỉ hướng quan hệ. Máy phục vụ công đoạn, công đoạn trước cung cấp bán thành phẩm cho công đoạn sau."

---

## Bước 2 — Hai lớp dữ liệu

- **Ai làm:** Admin.
- **Thao tác:** chuyển chế độ **Luồng dữ liệu** rồi **Kết hợp**; chỉ vào các cạnh nét đứt màu tím (data_mapping) nối dữ liệu với máy/công đoạn.
- **Kết quả mong đợi:** vùng "Logic hệ thống dữ liệu" hiện ở phía dưới; cạnh data_mapping nổi bật (nét đứt đậm) nối dataset/field với M10, P10, P20.
- **Lời dẫn:** "Lớp trên là dữ liệu thu thập được; cạnh ánh xạ cho biết mã lỗi trong dataset trạng thái máy tương ứng với máy M10."

---

## Bước 3 — Ghi nhận máy dừng

- **Ai làm:** `demo-recorder` (OPERATOR).
- **Thao tác:**
  1. Đăng xuất, đăng nhập bằng `demo-recorder`.
  2. Menu **Ghi nhận dữ liệu** → tab **Trạng thái máy** → máy **M10**, thời điểm **10:00**, trạng thái **STOPPED**, mã lỗi **E-DEMO-01**, ghi chú "Máy dừng, màn hình báo lỗi bộ phận cấp phôi".
  3. Bấm **Báo cáo sự cố** (header), điền thông tin có sẵn, lưu.
- **Kết quả mong đợi:** có bản ghi trạng thái STOPPED và một sự cố mới (mã tự đặt, ví dụ INC-DEMO-01) gắn máy M10, thời điểm 10:00.
- **Lời dẫn:** "Người ghi nhận chỉ ghi quan sát — máy dừng và mã lỗi — không kết luận nguyên nhân."

---

## Bước 4 — Chạy phân tích

- **Ai làm:** `demo-coordinator`.
- **Thao tác:** đăng nhập `demo-coordinator` → menu **Sự cố** → mở hồ sơ vừa tạo → **Chạy phân tích tác động**, nhập thời lượng dừng **15 phút**.
- **Kết quả mong đợi:**
  - Bối cảnh **MATCHED** với **LOT-B** tại công đoạn **P10**.
  - Ảnh hưởng: **Gia công (trực tiếp)**, **Kiểm tra (gián tiếp)**, **Đóng gói (gián tiếp)**, **LOT-B (đã quan sát)**.
  - Hàng đệm cạn sau **6 phút** (10:00 + 6 = **10:06**), công thức 60 ÷ 10.
  - Năng lực có nguy cơ **180 pcs** (15 × 12).
  - Sự cố tương tự **INC-HIST-001**; giả thuyết **H_MACHINE_ERROR**; hành động cho **MAINT, PROD, PLAN**.
- **Lời dẫn:** "Con số 180 là năng lực có nguy cơ, không phải thành phẩm chắc chắn mất — giả định chưa tính tồn đệm và sản xuất bù."

---

## Bước 5 — Xem trên bản đồ

- **Ai làm:** `demo-coordinator`.
- **Thao tác:** menu **Bản đồ liên kết** → chế độ **Theo sự cố** → chọn sự cố vừa tạo.
- **Kết quả mong đợi:** đường lan truyền **M10 → Gia công → Kiểm tra → Đóng gói** được tô sáng; node phân biệt **Trực tiếp/Gián tiếp**.
- **Lời dẫn:** "Bản đồ cho thấy cùng một sự cố nhưng ở dạng trực quan — ai bị ảnh hưởng và theo đường nào."

---

## Bước 6 — "Vì sao?"

- **Ai làm:** `demo-coordinator`.
- **Thao tác:** trên kết quả phân tích, bấm **"Vì sao?"** ở một kết luận.
- **Kết quả mong đợi:** hiện bằng chứng, đường quan hệ, quy tắc + phiên bản, công thức và giả định.
- **Lời dẫn:** "Mỗi kết luận đều giải thích được — không có con số bí ẩn."

---

## Bước 7 — Bối cảnh mơ hồ

- **Ai làm:** `demo-coordinator`.
- **Thao tác:** nạp thêm kịch bản mơ hồ (nếu chưa), mở **INC-AMB-01** → chạy phân tích.
- **Kết quả mong đợi:** trạng thái **AMBIGUOUS** với **2 lô ứng viên**; coordinator chọn một lô, nhập lý do, **Xác minh**; chạy lại → **CONFIRMED** (lần chạy cũ vẫn giữ AMBIGUOUS).
- **Lời dẫn:** "Khi dữ liệu mơ hồ, hệ thống không tự chọn — cần con người xác minh và lưu vết."

---

## Bước 8 — Giao việc

- **Ai làm:** `demo-coordinator` → `demo-handler`.
- **Thao tác:** từ hành động đề xuất của **MAINT**, bấm **Tạo công việc**; `demo-handler` chuyển trạng thái **TODO → IN_PROGRESS → DONE**.
- **Kết quả mong đợi:** công việc xuất hiện trong **Công việc theo bộ phận**, bấm lại không tạo trùng.
- **Lời dẫn:** "Đề xuất phân tích được chuyển thành công việc cụ thể cho từng bộ phận."

---

## Bước 9 — Khôi phục lúc 10:12

- **Ai làm:** `demo-coordinator`.
- **Thao tác:** ghi trạng thái **RUNNING** cho M10, đóng khoảng dừng, bấm **Xác nhận khôi phục** với thời điểm **10:12**; chạy lại phân tích với **12 phút**.
- **Kết quả mong đợi:** hồ sơ hiện "Khôi phục lúc 10:12" và "Người xác nhận: demo-coordinator", trạng thái **Đang xử lý**, thẻ **Dòng thời gian** có dòng "Xác nhận khôi phục" kèm ghi chú; năng lực có nguy cơ **144 pcs** (12 × 12); snapshot 15 phút cũ vẫn là **180**.
- **Lưu ý:** nút **Xác nhận khôi phục**/**Đóng hồ sơ** chỉ hiện với tài khoản điều phối (hoặc admin); tài khoản khác chỉ thấy dòng giải thích.
- **Lời dẫn:** "Khôi phục là hành động riêng, có thời điểm và người xác nhận; lịch sử phân tích cũ không bị sửa."

---

## Bước 10 — Đóng hồ sơ

- **Ai làm:** `demo-coordinator`.
- **Thao tác:** bấm **Đóng hồ sơ**, nhập **tóm tắt kết quả xử lý**, trạng thái nguyên nhân (có thể **UNKNOWN** nếu chưa xác định).
- **Kết quả mong đợi:** hồ sơ về **RESOLVED**, hiện người đóng, thời điểm đóng, tóm tắt; hai nút thao tác biến mất, thay bằng dòng **Hồ sơ đã đóng**.
- **Lời dẫn:** "Cho phép đóng với nguyên nhân chưa xác định, miễn có tóm tắt xử lý đầy đủ."

---

## Nếu có sự cố khi demo

- **DB không kết nối:** kiểm tra `.env` (DB_PASSWORD) và dịch vụ PostgreSQL; đọc README mục "Gặp lỗi?".
- **Quên mật khẩu demo:** không lấy lại được (chỉ hiện một lần); nạp lại kịch bản trên database test hoặc tạo tài khoản mới.
- **Bản đồ trống:** vào **Kịch bản mô phỏng** → bấm lại **Nạp dữ liệu mô phỏng**.

---

## Bảng số liệu chuẩn

| Hạng mục | Giá trị |
|---|---|
| Bối cảnh tại 10:00 | MATCHED — LOT-B / P10 / M10 |
| Hàng đệm P10→P20 | 60 pcs, tiêu thụ 10 pcs/phút |
| Thời điểm cạn hàng đệm | 10:06 (60 ÷ 10 = 6 phút) |
| Công suất tham chiếu M10/P10 | 12 pcs/phút |
| Năng lực có nguy cơ (dừng 15 phút) | 15 × 12 = **180 pcs** |
| Năng lực có nguy cơ (dừng 12 phút) | 12 × 12 = **144 pcs** |
| Tác động từ M10 | Gia công (DIRECT), Kiểm tra + Đóng gói (INDIRECT), LOT-B (OBSERVED) |
| Sự cố tương tự | INC-HIST-001 (cùng máy + mã lỗi E-DEMO-01) |
| Giả thuyết nguyên nhân | H_MACHINE_ERROR |
| Hành động đề xuất | MAINT, PROD, PLAN |
