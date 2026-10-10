# Phân tích — Tài liệu tham chiếu chi tiết

Tài liệu mô tả chi tiết các mục trong nhóm menu **Phân tích**:
**Bản đồ liên kết** và **Phân tích tác động**, kèm mô tả từng trường (field).

---

## 1. Bản đồ liên kết

Bản đồ thể hiện quan hệ giữa hai lớp: **nghiệp vụ sản xuất** và **logic hệ thống dữ liệu**.

### 1.1. Ba chế độ hiển thị

| Chế độ | Hiển thị gì |
|---|---|
| **Nghiệp vụ sản xuất** | Chỉ các node nghiệp vụ (bộ phận, chuyền, công đoạn, máy, vật tư, sản phẩm, lệnh, lô, ca) và quan hệ giữa chúng. |
| **Logic hệ thống** | Chỉ nguồn dữ liệu, dataset, trường dữ liệu và luồng giữa chúng. |
| **Kết hợp hai lớp** | Cả hai lớp và các cạnh nối chúng (ánh xạ dữ liệu–nghiệp vụ). |

### 1.2. Loại node (12 loại)

| `node_type` | Nhãn | Bảng dữ liệu | Lớp |
|---|---|---|---|
| `department` | Bộ phận | `departments` | Nghiệp vụ |
| `line` | Chuyền | `production_lines` | Nghiệp vụ |
| `process` | Công đoạn | `processes` | Nghiệp vụ |
| `machine` | Máy | `machines` | Nghiệp vụ |
| `material` | Vật tư | `materials` | Nghiệp vụ |
| `product` | Sản phẩm | `products` | Nghiệp vụ |
| `order` | Lệnh sản xuất | `production_orders` | Nghiệp vụ |
| `lot` | Lot | `lots` | Nghiệp vụ |
| `shift` | Ca sản xuất | `shifts` | Nghiệp vụ |
| `source` | Hệ thống nguồn | `data_sources` | Hệ thống |
| `dataset` | Dataset | `datasets` | Hệ thống |
| `field` | Trường dữ liệu | `dataset_fields` | Hệ thống |

### 1.3. Loại cạnh (4 loại)

| `kind` | Nhãn | Ý nghĩa | Có lan truyền tác động? |
|---|---|---|---|
| `production_dependency` | Phụ thuộc sản xuất | Quan hệ vật lý/sản xuất (máy → công đoạn, công đoạn → công đoạn...). | **Có** (truyền tác động) |
| `data_flow` | Luồng dữ liệu | Dữ liệu chảy từ dataset/source này sang dataset/source khác. | Không (chỉ mô tả dữ liệu) |
| `data_mapping` | Ánh xạ dữ liệu–nghiệp vụ | Trường dữ liệu ánh xạ tới đối tượng nghiệp vụ (ví dụ `machine_code` → máy M10). | Không (chỉ là ánh xạ) |
| `department_responsibility` | Trách nhiệm bộ phận | Bộ phận chịu trách nhiệm một đối tượng. | Không |

> **Lưu ý quan trọng:** cạnh `data_mapping` **không** tự động được dùng để lan truyền sự cố vật lý.

### 1.4. Các trường của một cạnh (`graph_edges`)

| Trường | Kiểu | Mô tả |
|---|---|---|
| `id` | bigint | Khóa chính. |
| `source_type` | text | Loại node nguồn (xem 1.2). |
| `source_id` | bigint | ID node nguồn trong bảng tương ứng. |
| `target_type` | text | Loại node đích. |
| `target_id` | bigint | ID node đích. |
| `kind` | text | Loại cạnh (xem 1.3). |
| `label` | text | Mô tả ngắn quan hệ (ví dụ "Máy phục vụ công đoạn"). |
| `description` | text | Mô tả dài hơn (tùy chọn). |
| `source_confirmation` | text | Nguồn xác nhận quan hệ (ví dụ "Demo", tên người/đơn vị). |
| `valid_from` | timestamptz | Thời điểm quan hệ bắt đầu có hiệu lực. |
| `valid_to` | timestamptz | Thời điểm quan hệ hết hiệu lực (null = còn hiệu lực). |
| `is_simulated` | boolean | `true` nếu là dữ liệu mô phỏng. |
| `created_at` / `updated_at` | timestamptz | Thời gian tạo/cập nhật (khác với thời gian hiệu lực). |

---

## 2. Phân tích tác động

Endpoint: `POST /api/analysis/run` (theo sự cố) và `POST /api/analysis/whatif` (giả định).

### 2.1. Đầu vào (input)

| Trường | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `incident_id` | int | có (`/run`) | ID sự cố cần phân tích. |
| `incident_type` | text | có (`/whatif`) | Loại sự cố: `MACHINE_STOP`, `QUALITY`, `MATERIAL_SHORTAGE`, `DATA_DELAY`, `OTHER`. |
| `source_type` | text | có (`/whatif`) | Loại đối tượng khởi phát (ví dụ `machine`). |
| `source_id` | int | có (`/whatif`) | ID đối tượng khởi phát. |
| `max_depth` | int | không (mặc định 3) | Giới hạn số bước lan truyền trên đồ thị. |
| `duration_minutes` | number | không | Thời lượng dừng giả định (phút) để ước tính định lượng. |
| `rate_per_minute` | number | không | Tốc độ (pcs/phút) để ước tính định lượng (nếu không có, engine dùng `capacity_profiles`). |
| `assumptions` | text | không | Giả định người dùng nhập, được lưu riêng và hiển thị rõ. |
| `at_time` | datetime | không | Mốc thời gian đánh giá (mặc định lấy `start_time` của sự cố). |

### 2.2. Kết quả (result)

| Trường | Kiểu | Mô tả |
|---|---|---|
| `rule_version` | text | Phiên bản bộ quy tắc đã dùng. |
| `rules` | list | Danh sách ID quy tắc khớp loại sự cố. |
| `signals` | object | Tín hiệu trích từ dữ liệu vận hành (xem 2.8). |
| `context` | object | Bối cảnh sản xuất tại thời điểm sự cố (xem 2.3). |
| `impacts` | list | Các đối tượng bị ảnh hưởng (xem 2.4). |
| `hypotheses` | list | Giả thuyết nguyên nhân (xem 2.5). |
| `actions` | list | Hành động đề xuất theo bộ phận (xem 2.6). |
| `quantification` | object | Định lượng sản lượng có nguy cơ mất (xem 2.7). |
| `buffer_estimate` | object | Ước tính cạn hàng đệm (xem 2.7). |
| `capacity_estimate` | object | Ước tính năng lực theo công suất tham chiếu (xem 2.7). |
| `related_past_incidents` | list | Sự cố cũ tương tự (xem 2.7). |
| `run_id` | int | ID lần chạy (đã lưu vết). |
| `run_at` | datetime | Thời điểm phân tích. |
| `incident_id` | int | ID sự cố (`/run`). |

### 2.3. `context` — bối cảnh sản xuất

| Trường | Kiểu | Mô tả |
|---|---|---|
| `status` | text | `MATCHED` / `AMBIGUOUS` / `NOT_FOUND` / `CONFIRMED` / `NEEDS_REVIEW`. |
| `resolved` | boolean | `true` khi xác định được đúng một lô/công đoạn. |
| `selected_operation_id` | int | ID `production_operations` được chọn (null nếu mơ hồ). |
| `candidates` | list | Các bối cảnh phù hợp (mỗi phần tử xem 2.3.1). |
| `machine_id` / `machine_code` | — | Máy đang xét. |
| `process_id` / `process_code` | — | Công đoạn đang xét. |
| `lot_id` / `lot_code` | — | Lô đang chạy (chỉ khi `resolved`). |
| `order_code` | text | Lệnh sản xuất của lô. |
| `started_at` / `ended_at` | datetime | Khoảng thực hiện `[started_at, ended_at)`. |
| `message` | text | Giải thích khi không xác định/mơ hồ. |
| `verified` | object | Thông tin xác minh (nếu có): `decided_by`, `decided_at`, `reason`, `evidence`, `status`. |

#### 2.3.1. Mỗi ứng viên (`candidates[]`)

| Trường | Mô tả |
|---|---|
| `operation_id` | ID `production_operations`. |
| `machine_id` / `machine_code` | Máy. |
| `process_id` / `process_code` | Công đoạn. |
| `lot_id` / `lot_code` | Lô. |
| `order_code` | Lệnh sản xuất. |
| `started_at` / `ended_at` | Khoảng thời gian thực hiện. |
| `source` | Nguồn thông tin. |
| `status` | Trạng thái thực hiện (`IN_PROGRESS`, `COMPLETED`...). |

#### 2.3.2. Ý nghĩa các trạng thái

| `status` | Ý nghĩa |
|---|---|
| `MATCHED` | Một bối cảnh phù hợp (chưa cần người xác minh). |
| `AMBIGUOUS` | Nhiều ứng viên, chưa đủ căn cứ chọn → **không tự chọn**, cần xác minh. |
| `NOT_FOUND` | Chưa tìm được bối cảnh. |
| `CONFIRMED` | Người có quyền đã xác minh một/nhiều bối cảnh. |
| `NEEDS_REVIEW` | Dữ liệu đã thay đổi sau khi xác minh → cần kiểm tra lại. |

### 2.4. `impacts[]` — đối tượng bị ảnh hưởng

| Trường | Kiểu | Mô tả |
|---|---|---|
| `node_type` | text | Loại node (xem 1.2). |
| `node_id` | int | ID node. |
| `node_name` | text | Tên/mã hiển thị. |
| `impact_type` | text | `DIRECT` / `INDIRECT` / `RISK` / `OBSERVED` / `ESTIMATED` (xem 2.4.1). |
| `relation_depth` | text | `DIRECT` / `INDIRECT` — độ sâu quan hệ (xem 2.4.2). |
| `evidence_status` | text | `OBSERVED` / `POTENTIAL` / `ESTIMATED` — trạng thái bằng chứng (xem 2.4.2). |
| `path` | list | Đường lan truyền (mỗi bước có `from_type/from_id/kind/to_type/to_id/label`). |
| `evidence` | text | Bằng chứng (cạnh/quy tắc đã dùng). |
| `rule_id` | text | Quy tắc áp dụng. |
| `assumptions` | text | Giả định đã dùng. |
| `missing_info` | text | Thông tin còn thiếu. |
| `departments` | list | Bộ phận liên quan (`{code, name}`). |

#### 2.4.1. `impact_type`

| Giá trị | Ý nghĩa |
|---|---|
| `DIRECT` | Ảnh hưởng trực tiếp (1 bước từ node khởi phát). |
| `INDIRECT` | Ảnh hưởng gián tiếp (nhiều bước). |
| `RISK` | Rủi ro tiềm năng do chỉ biết quan hệ phụ thuộc (cạnh không truyền tác động). |
| `OBSERVED` | Ảnh hưởng quan sát được từ dữ liệu (ví dụ lô đang chạy tại máy). |
| `ESTIMATED` | Ảnh hưởng ước tính có đủ tham số. |

#### 2.4.2. Phân biệt `relation_depth` và `evidence_status`

Hai khái niệm **độc lập**, một tác động có thể vừa `INDIRECT` vừa `ESTIMATED`:

| Trường | Giá trị | Trả lời câu hỏi |
|---|---|---|
| `relation_depth` | `DIRECT` / `INDIRECT` | Cách bao xa so với node khởi phát? |
| `evidence_status` | `OBSERVED` / `POTENTIAL` / `ESTIMATED` | Có bằng chứng mạnh tới đâu? |

- `OBSERVED`: có dữ liệu vận hành xác nhận.
- `POTENTIAL`: suy ra từ quan hệ (rủi ro), chưa có dữ liệu xác nhận.
- `ESTIMATED`: con số ước tính từ công thức/tham số, không phải đo đạc thực tế.

### 2.5. `hypotheses[]` — giả thuyết nguyên nhân

| Trường | Mô tả |
|---|---|
| `content` | Nội dung giả thuyết. |
| `evidence` | Bằng chứng ủng hộ. |
| `check_more` | Thông tin cần kiểm tra thêm. |
| `rule_id` | ID giả thuyết/quy tắc (ví dụ `H_MACHINE_ERROR`). |
| `priority` | Mức ưu tiên kiểm tra (`LOW`/`MEDIUM`/`HIGH`/`CRITICAL`). |

> Giả thuyết **không phải nguyên nhân đã xác nhận**; cũng không phải xác suất.

### 2.6. `actions[]` — hành động đề xuất

| Trường | Mô tả |
|---|---|
| `department_id` | ID bộ phận (null nếu không khớp danh mục). |
| `department_name` | Tên bộ phận. |
| `department_code` | Mã bộ phận (ví dụ `MAINT`). |
| `action` | Nội dung hành động. |
| `priority` | Mức ưu tiên. |
| `id` | ID `analysis_actions` (dùng để tạo công việc, chống trùng). |

### 2.7. Định lượng và ước tính

#### `quantification` (sản lượng có nguy cơ mất — dùng tham số người dùng)

| Trường | Mô tả |
|---|---|
| `available` | `true` nếu đủ 2 đầu vào (thời lượng + tốc độ). |
| `message` | Giải thích khi chưa đủ dữ liệu. |
| `formula` | Công thức: `thời gian dừng × tốc độ`. |
| `duration_minutes` | Thời lượng dừng (phút). |
| `rate_per_minute` | Tốc độ (pcs/phút). |
| `lost_quantity` | Kết quả ước tính. |
| `assumptions` | Giả định (chưa xét tồn đệm, sản xuất bù, máy thay thế). |

#### `capacity_estimate` (năng lực theo công suất tham chiếu)

| Trường | Mô tả |
|---|---|
| `process_id` / `machine_id` | Công đoạn/máy. |
| `rate_per_minute` | Công suất tham chiếu (từ `capacity_profiles`). |
| `duration_minutes` | Thời lượng dừng. |
| `estimated_quantity` | `thời lượng × công suất` — **năng lực có nguy cơ**, không phải thành phẩm chắc chắn mất. |
| `unit` | Đơn vị (pcs/min). |
| `formula` | Công thức. |
| `assumptions` | Giả định. |

#### `buffer_estimate` (nguy cơ cạn hàng đệm)

| Trường | Mô tả |
|---|---|
| `available` | `true` nếu có dữ liệu đệm + công suất công đoạn sau. |
| `upstream_process_id` / `downstream_process_id` | Công đoạn trước/sau. |
| `downstream_name` | Tên công đoạn sau. |
| `buffer_qty` / `buffer_unit` | Lượng hàng đệm khả dụng. |
| `rate_per_minute` | Tốc độ tiêu thụ công đoạn sau. |
| `depletion_minutes` | Số phút để cạn hàng (`buffer_qty ÷ rate`). |
| `depletion_time` | Thời điểm dự kiến cạn hàng (ISO). |
| `assumptions` | Giả định (không bổ sung hàng, tốc độ không đổi...). |

#### `related_past_incidents[]` — sự cố cũ tương tự

| Trường | Mô tả |
|---|---|
| `incident_id` | ID sự cố cũ. |
| `code` | Mã sự cố cũ. |
| `matched_criteria` | Tiêu chí khớp (ví dụ "cùng máy", "cùng mã lỗi", "cùng loại sự cố"). |

> Nguyên nhân cũ **chỉ để tham khảo**, không tự áp dụng cho sự cố hiện tại.

### 2.8. `signals` — tín hiệu từ dữ liệu vận hành

| Trường | Kiểu | Ý nghĩa |
|---|---|---|
| `has_machine_stop` | boolean | Loại sự cố là dừng máy. |
| `has_error_code` | boolean | Có mã lỗi thiết bị trong dữ liệu. |
| `qc_fail` | boolean | Có kết quả QC không đạt. |
| `low_material` | boolean | Vật tư dưới ngưỡng cấu hình. |
| `dataset_delay` | boolean | Loại sự cố là chậm dữ liệu. |
| `defect_rate` | number/null | Tỷ lệ lỗi QC (%). |
| `material_available` | number/null | Số lượng vật tư khả dụng. |

---

## 3. Ví dụ đọc kết quả

Kịch bản máy M10 dừng lúc 10:00, giả định dừng 15 phút:

- `context.status = MATCHED`, `lot_code = LOT-B` (lô đang chạy, không phải LOT-A đã rời máy trước đó).
- `buffer_estimate`: `60 ÷ 10 = 6 phút` → công đoạn sau có nguy cơ cạn hàng lúc `10:06` (là **ước tính**, không phải bằng chứng đã dừng).
- `capacity_estimate.estimated_quantity = 180` (15 × 12) — năng lực có nguy cơ, không cộng thêm ở từng công đoạn.
- `related_past_incidents` chứa `INC-HIST-001` (khớp cùng máy + mã lỗi).
- `hypotheses` chứa `H_MACHINE_ERROR` (giả thuyết, chưa xác nhận).
- `actions` gồm MAINT (kiểm tra máy), PROD (xác minh hàng đệm), PLAN (đánh giá bù tiến độ).
