-- 0010: Mô tả đầy đủ bảng + cột cho toàn bộ schema (danh mục, hệ thống, vận hành, sự cố, công việc, tài khoản).
-- Chỉ thêm COMMENT (metadata), không đổi cấu trúc/dữ liệu. Bổ sung phần còn thiếu của 0009.

-- ===== Danh mục nghiệp vụ =====
COMMENT ON TABLE production.departments IS 'Bộ phận trong nhà máy (Sản xuất, Bảo trì, QC, Kho, Kế hoạch, IT/Data...).';
COMMENT ON COLUMN production.departments.code IS 'Mã bộ phận (duy nhất).';
COMMENT ON COLUMN production.departments.name IS 'Tên bộ phận.';
COMMENT ON COLUMN production.departments.description IS 'Mô tả.';
COMMENT ON COLUMN production.departments.active IS 'Đang hoạt động (false = đã ngừng, không xóa vật lý).';
COMMENT ON COLUMN production.departments.is_simulated IS 'true nếu là dữ liệu mô phỏng.';

COMMENT ON TABLE production.production_lines IS 'Chuyền sản xuất.';
COMMENT ON COLUMN production.production_lines.department_id IS 'Bộ phận sở hữu chuyền.';

COMMENT ON TABLE production.processes IS 'Công đoạn trong chuyền.';
COMMENT ON COLUMN production.processes.line_id IS 'Chuyền chứa công đoạn.';

COMMENT ON TABLE production.machines IS 'Máy móc/thiết bị.';
COMMENT ON COLUMN production.machines.department_id IS 'Bộ phận sở hữu máy.';

COMMENT ON TABLE production.materials IS 'Vật tư/linh kiện.';
COMMENT ON COLUMN production.materials.unit IS 'Đơn vị tính (pcs, kg...).';
COMMENT ON COLUMN production.materials.department_id IS 'Bộ phận sở hữu vật tư.';

COMMENT ON TABLE production.products IS 'Sản phẩm.';
COMMENT ON COLUMN production.products.department_id IS 'Bộ phận sở hữu sản phẩm.';

COMMENT ON TABLE production.production_orders IS 'Lệnh sản xuất.';
COMMENT ON COLUMN production.production_orders.product_id IS 'Sản phẩm của lệnh.';
COMMENT ON COLUMN production.production_orders.status IS 'Trạng thái lệnh (PLANNED/IN_PROGRESS...).';

COMMENT ON TABLE production.lots IS 'Lot (lô) sản xuất.';
COMMENT ON COLUMN production.lots.production_order_id IS 'Lệnh sản xuất chứa lot.';

COMMENT ON TABLE production.shifts IS 'Ca sản xuất.';

-- ===== Lớp logic hệ thống =====
COMMENT ON TABLE production.data_sources IS 'Hệ thống nguồn dữ liệu (MES/ERP/PLC/APP/Excel/API...).';
COMMENT ON COLUMN production.data_sources.source_type IS 'Loại nguồn (MES, ERP, PLC, APP...).';
COMMENT ON COLUMN production.data_sources.collection_method IS 'Phương thức thu thập (cảm biến, PLC, barcode, nhập tay, file, API).';
COMMENT ON COLUMN production.data_sources.owner_department_id IS 'Bộ phận sở hữu nguồn.';
COMMENT ON COLUMN production.data_sources.location_metadata IS 'Vị trí lưu trữ dạng metadata (không lưu credentials).';
COMMENT ON COLUMN production.data_sources.confirmed IS 'Đã tích hợp thật (false = mới khai báo metadata).';

COMMENT ON TABLE production.datasets IS 'Dataset (bảng/file/endpoint).';
COMMENT ON COLUMN production.datasets.source_id IS 'Hệ thống nguồn.';
COMMENT ON COLUMN production.datasets.dataset_type IS 'Loại dataset (table/file/endpoint).';
COMMENT ON COLUMN production.datasets.generation_unit IS 'Đơn vị phát sinh: per_pcs / per_lot / per_event.';
COMMENT ON COLUMN production.datasets.update_schedule IS 'Lịch cập nhật: realtime / per_shift / daily / batch / manual.';
COMMENT ON COLUMN production.datasets.event_time_field IS 'Trường thời gian sự kiện.';
COMMENT ON COLUMN production.datasets.timezone IS 'Múi giờ.';
COMMENT ON COLUMN production.datasets.last_received_at IS 'Thời điểm nhận dữ liệu gần nhất.';
COMMENT ON COLUMN production.datasets.confirmed IS 'Đã xác nhận hay chưa.';

COMMENT ON TABLE production.dataset_fields IS 'Trường dữ liệu trong dataset.';
COMMENT ON COLUMN production.dataset_fields.dataset_id IS 'Dataset chứa trường.';
COMMENT ON COLUMN production.dataset_fields.is_key IS 'Là khóa liên kết (machine_code, lot_code...).';
COMMENT ON COLUMN production.dataset_fields.data_type IS 'Kiểu dữ liệu (string/timestamp/number...).';

COMMENT ON TABLE production.data_flows IS 'Luồng xử lý/truyền dữ liệu giữa các dataset.';
COMMENT ON COLUMN production.data_flows.source_dataset_id IS 'Dataset nguồn.';
COMMENT ON COLUMN production.data_flows.target_dataset_id IS 'Dataset đích.';

-- ===== Vận hành =====
COMMENT ON TABLE production.machine_states IS 'Sự kiện trạng thái máy (RUNNING/STOPPED/MAINTENANCE/UNKNOWN).';
COMMENT ON COLUMN production.machine_states.machine_id IS 'Máy.';
COMMENT ON COLUMN production.machine_states.event_time IS 'Thời điểm sự kiện (khác với thời gian hệ thống nhận).';
COMMENT ON COLUMN production.machine_states.state IS 'RUNNING / STOPPED / MAINTENANCE / UNKNOWN.';
COMMENT ON COLUMN production.machine_states.error_code IS 'Mã lỗi (nếu có).';
COMMENT ON COLUMN production.machine_states.received_at IS 'Thời gian hệ thống tiếp nhận.';

COMMENT ON TABLE production.machine_downtimes IS 'Khoảng dừng máy.';
COMMENT ON COLUMN production.machine_downtimes.start_time IS 'Thời điểm bắt đầu dừng.';
COMMENT ON COLUMN production.machine_downtimes.end_time IS 'Thời điểm kết thúc (null = đang dừng).';
COMMENT ON COLUMN production.machine_downtimes.reason IS 'Lý do dừng.';
COMMENT ON COLUMN production.machine_downtimes.error_code IS 'Mã lỗi.';
COMMENT ON COLUMN production.machine_downtimes.operator_name IS 'Người ghi nhận.';

COMMENT ON TABLE production.qc_results IS 'Kết quả kiểm tra chất lượng (QC).';
COMMENT ON COLUMN production.qc_results.lot_id IS 'Lot được kiểm tra.';
COMMENT ON COLUMN production.qc_results.product_id IS 'Sản phẩm.';
COMMENT ON COLUMN production.qc_results.process_id IS 'Công đoạn kiểm tra.';
COMMENT ON COLUMN production.qc_results.check_time IS 'Thời điểm kiểm tra.';
COMMENT ON COLUMN production.qc_results.inspected_qty IS 'Số lượng kiểm tra.';
COMMENT ON COLUMN production.qc_results.defect_qty IS 'Số lượng lỗi (<= inspected_qty).';
COMMENT ON COLUMN production.qc_results.defect_type IS 'Loại lỗi.';
COMMENT ON COLUMN production.qc_results.result IS 'PASS / FAIL / HOLD.';

COMMENT ON TABLE production.material_statuses IS 'Tình trạng vật tư khả dụng.';
COMMENT ON COLUMN production.material_statuses.material_id IS 'Vật tư.';
COMMENT ON COLUMN production.material_statuses.available_qty IS 'Số lượng khả dụng.';
COMMENT ON COLUMN production.material_statuses.unit IS 'Đơn vị tính.';
COMMENT ON COLUMN production.material_statuses.scope IS 'Phạm vi kho/chuyền.';
COMMENT ON COLUMN production.material_statuses.recorded_at IS 'Thời điểm ghi nhận.';

-- ===== Sự cố (bổ sung) =====
COMMENT ON TABLE production.incident_links IS 'Liên kết bản ghi vận hành làm bằng chứng cho sự cố.';
COMMENT ON COLUMN production.incident_links.source_type IS 'Loại bản ghi: machine_state/downtime/qc/material_status/production_record.';
COMMENT ON COLUMN production.incident_links.source_id IS 'ID bản ghi vận hành.';

-- ===== Công việc & khảo sát =====
COMMENT ON TABLE production.action_tasks IS 'Công việc theo bộ phận (được tạo từ đề xuất hoặc thủ công).';
COMMENT ON COLUMN production.action_tasks.department_id IS 'Bộ phận phụ trách.';
COMMENT ON COLUMN production.action_tasks.title IS 'Việc cần làm.';
COMMENT ON COLUMN production.action_tasks.status IS 'TODO / IN_PROGRESS / DONE / DISMISSED.';
COMMENT ON COLUMN production.action_tasks.priority IS 'Mức ưu tiên.';
COMMENT ON COLUMN production.action_tasks.source_incident_id IS 'Sự cố liên quan.';
COMMENT ON COLUMN production.action_tasks.source_analysis_run_id IS 'Lần phân tích nguồn.';
COMMENT ON COLUMN production.action_tasks.analysis_action_id IS 'Đề xuất (analysis_actions) sinh ra công việc (chống trùng).';

COMMENT ON TABLE production.survey_items IS 'Câu hỏi khảo sát cần xác nhận với nhà máy.';
COMMENT ON COLUMN production.survey_items.group_code IS 'Nhóm (G1..G9).';
COMMENT ON COLUMN production.survey_items.question IS 'Câu hỏi.';
COMMENT ON COLUMN production.survey_items.answer IS 'Câu trả lời.';
COMMENT ON COLUMN production.survey_items.provided_by IS 'Người cung cấp.';
COMMENT ON COLUMN production.survey_items.status IS 'UNCONFIRMED / CONFIRMED.';

-- ===== Tài khoản & phiên =====
COMMENT ON TABLE production.users IS 'Tài khoản local (mật khẩu băm PBKDF2).';
COMMENT ON COLUMN production.users.username IS 'Tên đăng nhập (duy nhất).';
COMMENT ON COLUMN production.users.display_name IS 'Tên hiển thị.';
COMMENT ON COLUMN production.users.role IS 'Vai trò mặc định (di sản).';
COMMENT ON COLUMN production.users.active IS 'Đang hoạt động (false = bị khóa).';
COMMENT ON COLUMN production.users.password_hash IS 'Hash mật khẩu (PBKDF2-SHA256), không lưu plaintext.';
COMMENT ON COLUMN production.users.failed_attempts IS 'Số lần đăng nhập sai liên tiếp.';
COMMENT ON COLUMN production.users.locked_until IS 'Thời điểm mở khóa sau khi bị khóa tạm thời.';
COMMENT ON COLUMN production.users.last_login_at IS 'Thời điểm đăng nhập gần nhất.';

COMMENT ON TABLE production.user_roles IS 'Vai trò của người dùng (một người nhiều vai trò).';
COMMENT ON COLUMN production.user_roles.user_id IS 'Người dùng.';
COMMENT ON COLUMN production.user_roles.role IS 'OPERATOR / HANDLER / COORDINATOR / ADMIN.';

COMMENT ON TABLE production.sessions IS 'Phiên đăng nhập phía server (cookie HttpOnly + hash token).';
COMMENT ON COLUMN production.sessions.token_hash IS 'SHA-256 của token phiên (không lưu token thô).';
COMMENT ON COLUMN production.sessions.user_id IS 'Người dùng của phiên.';
COMMENT ON COLUMN production.sessions.expires_at IS 'Thời điểm hết hạn phiên.';
COMMENT ON COLUMN production.sessions.revoked_at IS 'Thời điểm thu hồi (null = còn hiệu lực).';

-- ===== Kinh nghiệm & lịch sử =====
COMMENT ON TABLE production.incident_experiences IS 'Hồ sơ kinh nghiệm xử lý sự cố (lessons learned).';
COMMENT ON COLUMN production.incident_experiences.source_incident_id IS 'Sự cố nguồn.';
COMMENT ON COLUMN production.incident_experiences.incident_type IS 'Loại sự cố.';
COMMENT ON COLUMN production.incident_experiences.error_code IS 'Mã lỗi.';
COMMENT ON COLUMN production.incident_experiences.machine_id IS 'Máy liên quan.';
COMMENT ON COLUMN production.incident_experiences.symptom IS 'Triệu chứng.';
COMMENT ON COLUMN production.incident_experiences.root_cause IS 'Nguyên nhân đã xác nhận.';
COMMENT ON COLUMN production.incident_experiences.actions IS 'Hành động đã thực hiện.';
COMMENT ON COLUMN production.incident_experiences.result IS 'Kết quả xử lý.';
COMMENT ON COLUMN production.incident_experiences.approved_by IS 'Người duyệt.';

COMMENT ON TABLE production.incident_history IS 'Nhật ký diễn biến sự cố (audit).';
COMMENT ON COLUMN production.incident_history.incident_id IS 'Sự cố.';
COMMENT ON COLUMN production.incident_history.action IS 'Hành động (CREATED/UPDATED/RECOVERED/CLOSED/CONTEXT_VERIFIED...).';
COMMENT ON COLUMN production.incident_history.changed_by IS 'Người thao tác (từ phiên xác thực).';
COMMENT ON COLUMN production.incident_history.changed_at IS 'Thời điểm thao tác.';
COMMENT ON COLUMN production.incident_history.detail IS 'Chi tiết (JSONB).';

-- ===== Form sản lượng (di sản) =====
COMMENT ON TABLE production.production_records IS 'Bản ghi sản lượng công đoạn (form cũ).';
COMMENT ON COLUMN production.production_records.request_id IS 'UUID chống gửi trùng (idempotent).';
COMMENT ON COLUMN production.production_records.production_date IS 'Ngày sản xuất.';
COMMENT ON COLUMN production.production_records.shift IS 'Ca sản xuất (CA_1/CA_2/CA_3).';
COMMENT ON COLUMN production.production_records.line_code IS 'Mã chuyền.';
COMMENT ON COLUMN production.production_records.process_code IS 'Mã công đoạn.';
COMMENT ON COLUMN production.production_records.product_code IS 'Mã sản phẩm.';
COMMENT ON COLUMN production.production_records.lot_code IS 'Mã lot.';
COMMENT ON COLUMN production.production_records.good_quantity IS 'Số lượng đạt.';
COMMENT ON COLUMN production.production_records.defect_quantity IS 'Số lượng lỗi.';
COMMENT ON COLUMN production.production_records.operator_name IS 'Người nhập.';
COMMENT ON COLUMN production.production_records.note IS 'Ghi chú.';
