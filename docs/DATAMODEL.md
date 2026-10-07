# Denso D3 — Tài liệu mô hình dữ liệu (Data Model)

Tài liệu mô tả bảng, mức chi tiết bản ghi, PK/FK, mapping và cách lưu lịch sử.
Schema: `production` (PostgreSQL). Migration quản lý phiên bản trong `migrations/`.

## 1. Mapping tên logic -> tên bảng thực tế

| Tên logic trong đặc tả | Bảng thực tế | Ghi chú |
|---|---|---|
| Danh mục (bộ phận, chuyền, công đoạn, máy, vật tư, sản phẩm, lệnh, lô, ca) | `departments`, `production_lines`, `processes`, `machines`, `materials`, `products`, `production_orders`, `lots`, `shifts` | Kế thừa, không đổi |
| Người dùng | `users` | Bổ sung (0007 + 0008) |
| Vai trò người dùng | `user_roles` | Bổ sung (0008), một người nhiều vai trò |
| Phiên đăng nhập | `sessions` | Bổ sung (0008), cookie HttpOnly + hash token |
| Bối cảnh sản xuất | `production_operations` | Bổ sung (0007) |
| Xác minh bối cảnh | `incident_context_verifications` | Bổ sung (0008) |
| Hàng đệm | `buffer_snapshots` | Bổ sung (0007) |
| Công suất | `capacity_profiles` | Bổ sung (0007) |
| Nguồn, dataset, trường, luồng | `data_sources`, `datasets`, `dataset_fields`, `data_flows` | Kế thừa |
| Ánh xạ mã nguồn -> mã chuẩn | `source_object_mappings` | Bổ sung (0007) |
| Nhật ký tiếp nhận | `ingestion_records` | Bổ sung (0007) |
| Đồ thị liên kết | `graph_edges` | Kế thừa |
| Sản lượng (form cũ) | `production_records` | Kế thừa (không đổi) |
| Vận hành | `machine_states`, `machine_downtimes`, `qc_results`, `material_statuses` | Kế thừa |
| Sự cố | `incidents`, `incident_causes`, `incident_links` | Kế thừa + cột mới (0007) |
| Nhật ký diễn biến sự cố | `incident_history` | Bổ sung (0007) |
| Hồ sơ kinh nghiệm | `incident_experiences` | Bổ sung (0007) |
| Phân tích | `analysis_runs`, `analysis_impacts`, `analysis_hypotheses`, `analysis_actions` | Kế thừa + cột mới |
| Sự cố tương tự tham chiếu | `analysis_related_incidents` | Bổ sung (0007) |
| Công việc | `action_tasks` | Kế thừa + cột mới |
| Khảo sát | `survey_items` | Kế thừa |

## 2. Bảng mới (migration 0007)

### users
Tài khoản local, phân quyền tối thiểu cho demo xác nhận (chưa phải danh tính xác thực).
- PK `id`, UNIQUE `username`.
- `role`: OPERATOR/SUPERVISOR/...
- 0008 bổ sung: `password_hash`, `failed_attempts`, `locked_until`, `last_login_at`.

### user_roles (0008)
Một người nhiều vai trò: `user_id`, `role` (OPERATOR/HANDLER/COORDINATOR/ADMIN), UNIQUE(user_id, role).

### sessions (0008)
Phiên phía server: `token_hash` (SHA-256 của token cookie), `user_id`, `expires_at`, `revoked_at`.

### incident_context_verifications (0008)
Xác minh bối cảnh: `incident_id`, `operation_ids` (JSONB), `status` (CONFIRMED/REJECTED/UNRESOLVED),
`decided_by`, `decided_at`, `reason`, `evidence`, `candidate_snapshot` (JSONB).

### production_operations
Một dòng = một lần lô được thực hiện tại công đoạn trên máy trong khoảng `[started_at, ended_at)`.
- FK: `lot_id -> lots`, `process_id -> processes`, `machine_id -> machines` (null nếu công đoạn thủ công).
- `ended_at` null = chưa kết thúc được ghi nhận.
- `scenario_id` (DEMO-D3-01), `is_simulated`.

### buffer_snapshots
Hàng đệm giữa hai công đoạn tại một thời điểm.
- FK: `upstream_process_id`, `downstream_process_id -> processes`, `product_id -> products`, `lot_id -> lots`.
- `available_qty NUMERIC`, `unit`, `recorded_at`.

### capacity_profiles
Công suất tham chiếu theo công đoạn/máy/sản phẩm, có hiệu lực `[valid_from, valid_to)`.
- FK tùy chọn tới processes/machines/products.
- `rate_per_minute NUMERIC`, `unit`, `source_confirmation`.

### source_object_mappings
Ánh xạ mã nguồn (bên ngoài) -> đối tượng chuẩn, có phạm vi nguồn và hiệu lực.
- FK: `source_id -> data_sources`. `object_type` (machine/lot/process/product/material).
- UNIQUE `(source_id, object_type, source_code)`.
- `node_id` null khi chưa ánh xạ (bản ghi "thiếu liên kết").

### ingestion_records
Nhật ký tiếp nhận payload: nguồn, request_id, event_time, received_at, trạng thái và lỗi.
- `status`: VALID / NEEDS_MAPPING / NEEDS_LINKING / REJECTED.
- `payload JSONB`, `created_business_ids JSONB` (liên kết bản ghi nghiệp vụ được tạo).

### incident_history
Nhật ký diễn biến sự cố (audit): action, changed_by, changed_at, detail JSONB.
- FK `incident_id -> incidents ON DELETE CASCADE`.

### incident_experiences
Hồ sơ kinh nghiệm: triệu chứng, mã lỗi, máy/công đoạn, nguyên nhân đã xác nhận, hành động, kết quả, người duyệt.
- FK: `source_incident_id -> incidents`, `machine_id`, `process_id`.

### analysis_related_incidents
Sự cố tương tự được tham chiếu trong một lần phân tích.
- FK `run_id -> analysis_runs`, `related_incident_id -> incidents`.

## 3. Cột bổ sung cho bảng hiện có

### incidents
- `recovered_at`, `recovered_by` — thời điểm/người khôi phục.
- `closed_at`, `closed_by` — thời điểm/người đóng.
- `resolution_summary` — tóm tắt kết quả xử lý.
- `root_cause_status` — UNKNOWN/HYPOTHESIS/CONFIRMED (mặc định UNKNOWN).

### analysis_impacts
- `relation_depth` — DIRECT/INDIRECT.
- `evidence_status` — OBSERVED/POTENTIAL/ESTIMATED.
- Một tác động có thể vừa INDIRECT vừa ESTIMATED.

### action_tasks
- `analysis_action_id -> analysis_actions(id)` — truy vết công việc sinh từ đề xuất (chống trùng khi phân tích lại).

## 4. Cách lưu lịch sử (SCD có chọn lọc)

- Sửa tên/mô tả thông thường: cập nhật trực tiếp (SCD1) + `updated_at`.
- Quan hệ máy–công đoạn / phụ thuộc sản xuất / trách nhiệm: `graph_edges.valid_from/valid_to` (hoặc `source_object_mappings`, `capacity_profiles` có valid_from/valid_to).
- Sự kiện và diễn biến sự cố: lưu bổ sung vào `machine_states`/`machine_downtimes`; diễn biến vào `incident_history`.
- Phân tích: snapshot bất biến theo `analysis_runs` (input JSONB + impacts/hypotheses/actions + related_incidents + rule_version).
- Quy tắc mới không ghi đè kết quả cũ (mỗi run lưu `rule_version`).
- Phân biệt thời gian hiệu lực (valid_from/valid_to) với thời gian ghi nhận thay đổi (created_at/updated_at/changed_at).

## 5. Đối chiếu bối cảnh sản xuất

- Đối chiếu sự kiện theo `[started_at, ended_at)`; `ended_at IS NULL` = đang chạy/chưa kết thúc.
- `analysis_service._resolve_context` tìm TẤT CẢ `production_operations` của máy tại thời điểm lỗi
  (không dùng LIMIT 1), trả trạng thái:
  - `MATCHED` — một ứng viên phù hợp.
  - `AMBIGUOUS` — nhiều ứng viên, chưa đủ căn cứ chọn (không tự chọn).
  - `NOT_FOUND` — không tìm được bối cảnh.
  - `CONFIRMED` — đã có xác minh từ người có quyền (`incident_context_verifications`).
  - `NEEDS_REVIEW` — dữ liệu đã thay đổi sau khi xác minh.
- Không tự chọn khi nhiều bối cảnh phù hợp; không coi mọi lô cùng chuyền là bị ảnh hưởng.

## 6. Xác thực & phân quyền

- Mật khẩu băm PBKDF2-SHA256 (`app/security.py`), không lưu plaintext.
- Phiên: cookie HttpOnly + SameSite=Lax + Secure (khi HTTPS); DB lưu hash token.
- Vai trò: OPERATOR (ghi nhận), HANDLER (xử lý), COORDINATOR (điều phối/xác minh/đóng hồ sơ), ADMIN (quản trị).
- Danh tính audit lấy từ phiên (`request.state.user`), không tin `user_id` do client gửi.
- Tài khoản demo tạo qua seed chủ động, mật khẩu sinh ngẫu nhiên, không commit.
- CSRF: SameSite=Lax + kiểm tra Origin trên thao tác đổi dữ liệu.

