-- 0011: Hoàn thiện COMMENT cho toàn bộ cột còn thiếu (id, code, name, description, active, is_simulated, created_at, updated_at và các cột đặc thù).
-- Chỉ thêm metadata, không đổi cấu trúc/dữ liệu.

-- ===== Cột chung =====
-- (id = khóa chính; created_at/updated_at = thời gian ghi nhận thay đổi, KHÁC thời gian hiệu lực)

-- departments
COMMENT ON COLUMN production.departments.id IS 'Khóa chính (tự tăng).';
COMMENT ON COLUMN production.departments.created_at IS 'Thời điểm tạo.';
COMMENT ON COLUMN production.departments.updated_at IS 'Thời điểm cập nhật gần nhất.';

-- production_lines
COMMENT ON COLUMN production.production_lines.id IS 'Khóa chính.';
COMMENT ON COLUMN production.production_lines.code IS 'Mã chuyền (duy nhất).';
COMMENT ON COLUMN production.production_lines.name IS 'Tên chuyền.';
COMMENT ON COLUMN production.production_lines.description IS 'Mô tả.';
COMMENT ON COLUMN production.production_lines.active IS 'Đang hoạt động.';
COMMENT ON COLUMN production.production_lines.is_simulated IS 'Dữ liệu mô phỏng.';
COMMENT ON COLUMN production.production_lines.created_at IS 'Thời điểm tạo.';
COMMENT ON COLUMN production.production_lines.updated_at IS 'Thời điểm cập nhật gần nhất.';

-- processes
COMMENT ON COLUMN production.processes.id IS 'Khóa chính.';
COMMENT ON COLUMN production.processes.code IS 'Mã công đoạn (duy nhất).';
COMMENT ON COLUMN production.processes.name IS 'Tên công đoạn.';
COMMENT ON COLUMN production.processes.description IS 'Mô tả.';
COMMENT ON COLUMN production.processes.active IS 'Đang hoạt động.';
COMMENT ON COLUMN production.processes.is_simulated IS 'Dữ liệu mô phỏng.';
COMMENT ON COLUMN production.processes.created_at IS 'Thời điểm tạo.';
COMMENT ON COLUMN production.processes.updated_at IS 'Thời điểm cập nhật gần nhất.';

-- machines
COMMENT ON COLUMN production.machines.id IS 'Khóa chính.';
COMMENT ON COLUMN production.machines.code IS 'Mã máy (duy nhất).';
COMMENT ON COLUMN production.machines.name IS 'Tên máy.';
COMMENT ON COLUMN production.machines.description IS 'Mô tả.';
COMMENT ON COLUMN production.machines.active IS 'Đang hoạt động.';
COMMENT ON COLUMN production.machines.is_simulated IS 'Dữ liệu mô phỏng.';
COMMENT ON COLUMN production.machines.created_at IS 'Thời điểm tạo.';
COMMENT ON COLUMN production.machines.updated_at IS 'Thời điểm cập nhật gần nhất.';

-- materials
COMMENT ON COLUMN production.materials.id IS 'Khóa chính.';
COMMENT ON COLUMN production.materials.code IS 'Mã vật tư (duy nhất).';
COMMENT ON COLUMN production.materials.name IS 'Tên vật tư.';
COMMENT ON COLUMN production.materials.description IS 'Mô tả.';
COMMENT ON COLUMN production.materials.active IS 'Đang hoạt động.';
COMMENT ON COLUMN production.materials.is_simulated IS 'Dữ liệu mô phỏng.';
COMMENT ON COLUMN production.materials.created_at IS 'Thời điểm tạo.';
COMMENT ON COLUMN production.materials.updated_at IS 'Thời điểm cập nhật gần nhất.';

-- products
COMMENT ON COLUMN production.products.id IS 'Khóa chính.';
COMMENT ON COLUMN production.products.code IS 'Mã sản phẩm (duy nhất).';
COMMENT ON COLUMN production.products.name IS 'Tên sản phẩm.';
COMMENT ON COLUMN production.products.description IS 'Mô tả.';
COMMENT ON COLUMN production.products.active IS 'Đang hoạt động.';
COMMENT ON COLUMN production.products.is_simulated IS 'Dữ liệu mô phỏng.';
COMMENT ON COLUMN production.products.created_at IS 'Thời điểm tạo.';
COMMENT ON COLUMN production.products.updated_at IS 'Thời điểm cập nhật gần nhất.';

-- production_orders
COMMENT ON COLUMN production.production_orders.id IS 'Khóa chính.';
COMMENT ON COLUMN production.production_orders.code IS 'Mã lệnh (duy nhất).';
COMMENT ON COLUMN production.production_orders.name IS 'Tên lệnh.';
COMMENT ON COLUMN production.production_orders.description IS 'Mô tả.';
COMMENT ON COLUMN production.production_orders.active IS 'Đang hoạt động.';
COMMENT ON COLUMN production.production_orders.is_simulated IS 'Dữ liệu mô phỏng.';
COMMENT ON COLUMN production.production_orders.created_at IS 'Thời điểm tạo.';
COMMENT ON COLUMN production.production_orders.updated_at IS 'Thời điểm cập nhật gần nhất.';

-- lots
COMMENT ON COLUMN production.lots.id IS 'Khóa chính.';
COMMENT ON COLUMN production.lots.code IS 'Mã lot (duy nhất).';
COMMENT ON COLUMN production.lots.name IS 'Tên lot.';
COMMENT ON COLUMN production.lots.description IS 'Mô tả.';
COMMENT ON COLUMN production.lots.active IS 'Đang hoạt động.';
COMMENT ON COLUMN production.lots.is_simulated IS 'Dữ liệu mô phỏng.';
COMMENT ON COLUMN production.lots.created_at IS 'Thời điểm tạo.';
COMMENT ON COLUMN production.lots.updated_at IS 'Thời điểm cập nhật gần nhất.';

-- shifts
COMMENT ON TABLE production.shifts IS 'Ca sản xuất.';
COMMENT ON COLUMN production.shifts.id IS 'Khóa chính.';
COMMENT ON COLUMN production.shifts.code IS 'Mã ca (duy nhất).';
COMMENT ON COLUMN production.shifts.name IS 'Tên ca.';
COMMENT ON COLUMN production.shifts.description IS 'Mô tả.';
COMMENT ON COLUMN production.shifts.active IS 'Đang hoạt động.';
COMMENT ON COLUMN production.shifts.is_simulated IS 'Dữ liệu mô phỏng.';
COMMENT ON COLUMN production.shifts.created_at IS 'Thời điểm tạo.';
COMMENT ON COLUMN production.shifts.updated_at IS 'Thời điểm cập nhật gần nhất.';

-- ===== Lớp hệ thống (bổ sung) =====
COMMENT ON COLUMN production.data_sources.id IS 'Khóa chính.';
COMMENT ON COLUMN production.data_sources.code IS 'Mã nguồn (duy nhất).';
COMMENT ON COLUMN production.data_sources.name IS 'Tên nguồn.';
COMMENT ON COLUMN production.data_sources.is_simulated IS 'Dữ liệu mô phỏng.';
COMMENT ON COLUMN production.data_sources.created_at IS 'Thời điểm tạo.';
COMMENT ON COLUMN production.data_sources.updated_at IS 'Thời điểm cập nhật gần nhất.';

COMMENT ON COLUMN production.datasets.id IS 'Khóa chính.';
COMMENT ON COLUMN production.datasets.code IS 'Mã dataset (duy nhất).';
COMMENT ON COLUMN production.datasets.name IS 'Tên dataset.';
COMMENT ON COLUMN production.datasets.storage_location IS 'Vị trí lưu trữ (metadata).';
COMMENT ON COLUMN production.datasets.collection_method IS 'Phương thức thu thập.';
COMMENT ON COLUMN production.datasets.owner_department_id IS 'Bộ phận sở hữu.';
COMMENT ON COLUMN production.datasets.update_frequency IS 'Tần suất cập nhật.';
COMMENT ON COLUMN production.datasets.expected_latency IS 'Độ trễ dự kiến (nếu biết).';
COMMENT ON COLUMN production.datasets.is_simulated IS 'Dữ liệu mô phỏng.';
COMMENT ON COLUMN production.datasets.created_at IS 'Thời điểm tạo.';
COMMENT ON COLUMN production.datasets.updated_at IS 'Thời điểm cập nhật gần nhất.';

COMMENT ON COLUMN production.dataset_fields.id IS 'Khóa chính.';
COMMENT ON COLUMN production.dataset_fields.code IS 'Mã trường.';
COMMENT ON COLUMN production.dataset_fields.name IS 'Tên trường.';
COMMENT ON COLUMN production.dataset_fields.description IS 'Mô tả.';
COMMENT ON COLUMN production.dataset_fields.confirmed IS 'Đã xác nhận.';
COMMENT ON COLUMN production.dataset_fields.created_at IS 'Thời điểm tạo.';

COMMENT ON COLUMN production.data_flows.id IS 'Khóa chính.';
COMMENT ON COLUMN production.data_flows.code IS 'Mã luồng (duy nhất).';
COMMENT ON COLUMN production.data_flows.name IS 'Tên luồng.';
COMMENT ON COLUMN production.data_flows.description IS 'Mô tả.';
COMMENT ON COLUMN production.data_flows.confirmed IS 'Đã xác nhận.';
COMMENT ON COLUMN production.data_flows.is_simulated IS 'Dữ liệu mô phỏng.';
COMMENT ON COLUMN production.data_flows.created_at IS 'Thời điểm tạo.';
COMMENT ON COLUMN production.data_flows.updated_at IS 'Thời điểm cập nhật gần nhất.';

-- ===== Đồ thị (bổ sung) =====
COMMENT ON COLUMN production.graph_edges.id IS 'Khóa chính.';
COMMENT ON COLUMN production.graph_edges.description IS 'Mô tả dài hơn (tùy chọn).';
COMMENT ON COLUMN production.graph_edges.created_at IS 'Thời điểm tạo.';
COMMENT ON COLUMN production.graph_edges.updated_at IS 'Thời điểm cập nhật gần nhất.';

-- ===== Vận hành (bổ sung) =====
COMMENT ON COLUMN production.machine_states.id IS 'Khóa chính.';
COMMENT ON COLUMN production.machine_states.note IS 'Ghi chú.';
COMMENT ON COLUMN production.machine_states.is_simulated IS 'Dữ liệu mô phỏng.';
COMMENT ON COLUMN production.machine_states.created_at IS 'Thời điểm tạo.';

COMMENT ON COLUMN production.machine_downtimes.id IS 'Khóa chính.';
COMMENT ON COLUMN production.machine_downtimes.machine_id IS 'Máy.';
COMMENT ON COLUMN production.machine_downtimes.received_at IS 'Thời gian hệ thống tiếp nhận.';
COMMENT ON COLUMN production.machine_downtimes.is_simulated IS 'Dữ liệu mô phỏng.';
COMMENT ON COLUMN production.machine_downtimes.created_at IS 'Thời điểm tạo.';

COMMENT ON COLUMN production.qc_results.id IS 'Khóa chính.';
COMMENT ON COLUMN production.qc_results.note IS 'Ghi chú.';
COMMENT ON COLUMN production.qc_results.received_at IS 'Thời gian hệ thống tiếp nhận.';
COMMENT ON COLUMN production.qc_results.is_simulated IS 'Dữ liệu mô phỏng.';
COMMENT ON COLUMN production.qc_results.created_at IS 'Thời điểm tạo.';

COMMENT ON COLUMN production.material_statuses.id IS 'Khóa chính.';
COMMENT ON COLUMN production.material_statuses.received_at IS 'Thời gian hệ thống tiếp nhận.';
COMMENT ON COLUMN production.material_statuses.is_simulated IS 'Dữ liệu mô phỏng.';
COMMENT ON COLUMN production.material_statuses.created_at IS 'Thời điểm tạo.';

-- ===== Sự cố (bổ sung) =====
COMMENT ON COLUMN production.incidents.id IS 'Khóa chính.';
COMMENT ON COLUMN production.incidents.code IS 'Mã sự cố (duy nhất).';
COMMENT ON COLUMN production.incidents.title IS 'Tiêu đề.';
COMMENT ON COLUMN production.incidents.incident_type IS 'Loại: MACHINE_STOP/QUALITY/MATERIAL_SHORTAGE/DATA_DELAY/OTHER.';
COMMENT ON COLUMN production.incidents.start_time IS 'Thời điểm bắt đầu sự cố.';
COMMENT ON COLUMN production.incidents.end_time IS 'Thời điểm kết thúc sự cố.';
COMMENT ON COLUMN production.incidents.severity IS 'Mức nghiêm trọng: LOW/MEDIUM/HIGH/CRITICAL.';
COMMENT ON COLUMN production.incidents.description IS 'Mô tả quan sát (triệu chứng).';
COMMENT ON COLUMN production.incidents.status IS 'OPEN/INVESTIGATING/MITIGATING/RESOLVED.';
COMMENT ON COLUMN production.incidents.assigned_department_id IS 'Bộ phận phụ trách.';
COMMENT ON COLUMN production.incidents.request_id IS 'UUID chống gửi trùng.';
COMMENT ON COLUMN production.incidents.is_simulated IS 'Dữ liệu mô phỏng.';
COMMENT ON COLUMN production.incidents.created_at IS 'Thời điểm tạo.';
COMMENT ON COLUMN production.incidents.updated_at IS 'Thời điểm cập nhật gần nhất.';

COMMENT ON COLUMN production.incident_causes.id IS 'Khóa chính.';
COMMENT ON COLUMN production.incident_causes.incident_id IS 'Sự cố.';
COMMENT ON COLUMN production.incident_causes.content IS 'Nội dung nguyên nhân.';
COMMENT ON COLUMN production.incident_causes.evidence IS 'Bằng chứng.';
COMMENT ON COLUMN production.incident_causes.rule_id IS 'Quy tắc liên quan.';
COMMENT ON COLUMN production.incident_causes.priority IS 'Mức ưu tiên.';
COMMENT ON COLUMN production.incident_causes.confirmed_by IS 'Người xác nhận.';
COMMENT ON COLUMN production.incident_causes.confirmed_at IS 'Thời điểm xác nhận.';
COMMENT ON COLUMN production.incident_causes.created_at IS 'Thời điểm tạo.';

COMMENT ON COLUMN production.incident_links.id IS 'Khóa chính.';
COMMENT ON COLUMN production.incident_links.incident_id IS 'Sự cố.';
COMMENT ON COLUMN production.incident_links.created_at IS 'Thời điểm tạo.';

COMMENT ON COLUMN production.incident_context_verifications.id IS 'Khóa chính.';
COMMENT ON COLUMN production.incident_context_verifications.incident_id IS 'Sự cố.';
COMMENT ON COLUMN production.incident_context_verifications.decided_at IS 'Thời điểm xác minh.';
COMMENT ON COLUMN production.incident_context_verifications.evidence IS 'Bằng chứng.';
COMMENT ON COLUMN production.incident_context_verifications.created_at IS 'Thời điểm tạo.';

-- ===== Phân tích (bổ sung) =====
COMMENT ON COLUMN production.analysis_runs.id IS 'Khóa chính.';
COMMENT ON COLUMN production.analysis_runs.run_at IS 'Thời điểm chạy phân tích.';
COMMENT ON COLUMN production.analysis_runs.is_simulated IS 'Dữ liệu mô phỏng.';
COMMENT ON COLUMN production.analysis_runs.created_at IS 'Thời điểm tạo.';

COMMENT ON COLUMN production.analysis_impacts.id IS 'Khóa chính.';
COMMENT ON COLUMN production.analysis_impacts.run_id IS 'Lần chạy phân tích.';
COMMENT ON COLUMN production.analysis_impacts.node_type IS 'Loại node bị ảnh hưởng.';
COMMENT ON COLUMN production.analysis_impacts.node_id IS 'ID node.';
COMMENT ON COLUMN production.analysis_impacts.node_name IS 'Tên/mã node.';
COMMENT ON COLUMN production.analysis_impacts.departments IS 'Bộ phận liên quan (JSONB).';
COMMENT ON COLUMN production.analysis_impacts.created_at IS 'Thời điểm tạo.';

COMMENT ON COLUMN production.analysis_hypotheses.id IS 'Khóa chính.';
COMMENT ON COLUMN production.analysis_hypotheses.run_id IS 'Lần chạy phân tích.';
COMMENT ON COLUMN production.analysis_hypotheses.rule_id IS 'Quy tắc/giả thuyết.';
COMMENT ON COLUMN production.analysis_hypotheses.priority IS 'Mức ưu tiên kiểm tra.';
COMMENT ON COLUMN production.analysis_hypotheses.created_at IS 'Thời điểm tạo.';

COMMENT ON COLUMN production.analysis_actions.id IS 'Khóa chính.';
COMMENT ON COLUMN production.analysis_actions.run_id IS 'Lần chạy phân tích.';
COMMENT ON COLUMN production.analysis_actions.department_id IS 'Bộ phận (null nếu không khớp danh mục).';
COMMENT ON COLUMN production.analysis_actions.priority IS 'Mức ưu tiên.';
COMMENT ON COLUMN production.analysis_actions.created_at IS 'Thời điểm tạo.';

COMMENT ON COLUMN production.analysis_related_incidents.id IS 'Khóa chính.';
COMMENT ON COLUMN production.analysis_related_incidents.run_id IS 'Lần chạy phân tích.';
COMMENT ON COLUMN production.analysis_related_incidents.note IS 'Ghi chú.';

-- ===== Công việc & khảo sát (bổ sung) =====
COMMENT ON COLUMN production.action_tasks.id IS 'Khóa chính.';
COMMENT ON COLUMN production.action_tasks.description IS 'Lý do / mô tả.';
COMMENT ON COLUMN production.action_tasks.rule_id IS 'Quy tắc liên quan.';
COMMENT ON COLUMN production.action_tasks.is_simulated IS 'Dữ liệu mô phỏng.';
COMMENT ON COLUMN production.action_tasks.created_at IS 'Thời điểm tạo.';
COMMENT ON COLUMN production.action_tasks.updated_at IS 'Thời điểm cập nhật gần nhất.';

COMMENT ON COLUMN production.survey_items.id IS 'Khóa chính.';
COMMENT ON COLUMN production.survey_items.provided_at IS 'Thời điểm cung cấp.';
COMMENT ON COLUMN production.survey_items.note IS 'Ghi chú.';
COMMENT ON COLUMN production.survey_items.created_at IS 'Thời điểm tạo.';
COMMENT ON COLUMN production.survey_items.updated_at IS 'Thời điểm cập nhật gần nhất.';

-- ===== Tài khoản (bổ sung) =====
COMMENT ON COLUMN production.users.id IS 'Khóa chính.';
COMMENT ON COLUMN production.users.is_simulated IS 'Dữ liệu mô phỏng.';
COMMENT ON COLUMN production.users.created_at IS 'Thời điểm tạo.';
COMMENT ON COLUMN production.users.updated_at IS 'Thời điểm cập nhật gần nhất.';

COMMENT ON COLUMN production.user_roles.id IS 'Khóa chính.';

COMMENT ON COLUMN production.sessions.id IS 'Khóa chính.';
COMMENT ON COLUMN production.sessions.created_at IS 'Thời điểm tạo phiên.';

-- ===== Kinh nghiệm (bổ sung) =====
COMMENT ON COLUMN production.incident_experiences.id IS 'Khóa chính.';
COMMENT ON COLUMN production.incident_experiences.process_id IS 'Công đoạn liên quan.';
COMMENT ON COLUMN production.incident_experiences.approved_at IS 'Thời điểm duyệt.';
COMMENT ON COLUMN production.incident_experiences.scenario_id IS 'Mã kịch bản mô phỏng.';
COMMENT ON COLUMN production.incident_experiences.is_simulated IS 'Dữ liệu mô phỏng.';
COMMENT ON COLUMN production.incident_experiences.created_at IS 'Thời điểm tạo.';

COMMENT ON COLUMN production.incident_history.id IS 'Khóa chính.';

-- ===== Bối cảnh (bổ sung) =====
COMMENT ON COLUMN production.production_operations.id IS 'Khóa chính.';
COMMENT ON COLUMN production.production_operations.context_status IS 'Trạng thái bối cảnh (di sản).';
COMMENT ON COLUMN production.production_operations.confirmed_by IS 'Người xác nhận.';
COMMENT ON COLUMN production.production_operations.is_simulated IS 'Dữ liệu mô phỏng.';
COMMENT ON COLUMN production.production_operations.created_at IS 'Thời điểm tạo.';
COMMENT ON COLUMN production.production_operations.updated_at IS 'Thời điểm cập nhật gần nhất.';

COMMENT ON COLUMN production.buffer_snapshots.id IS 'Khóa chính.';
COMMENT ON COLUMN production.buffer_snapshots.unit IS 'Đơn vị tính.';
COMMENT ON COLUMN production.buffer_snapshots.source IS 'Nguồn thông tin.';
COMMENT ON COLUMN production.buffer_snapshots.confirmed IS 'Đã xác nhận.';
COMMENT ON COLUMN production.buffer_snapshots.scenario_id IS 'Mã kịch bản mô phỏng.';
COMMENT ON COLUMN production.buffer_snapshots.is_simulated IS 'Dữ liệu mô phỏng.';
COMMENT ON COLUMN production.buffer_snapshots.created_at IS 'Thời điểm tạo.';

COMMENT ON COLUMN production.capacity_profiles.id IS 'Khóa chính.';
COMMENT ON COLUMN production.capacity_profiles.process_id IS 'Công đoạn.';
COMMENT ON COLUMN production.capacity_profiles.machine_id IS 'Máy.';
COMMENT ON COLUMN production.capacity_profiles.product_id IS 'Sản phẩm.';
COMMENT ON COLUMN production.capacity_profiles.unit IS 'Đơn vị (pcs/min).';
COMMENT ON COLUMN production.capacity_profiles.source_confirmation IS 'Nguồn xác nhận.';
COMMENT ON COLUMN production.capacity_profiles.scenario_id IS 'Mã kịch bản mô phỏng.';
COMMENT ON COLUMN production.capacity_profiles.is_simulated IS 'Dữ liệu mô phỏng.';
COMMENT ON COLUMN production.capacity_profiles.created_at IS 'Thời điểm tạo.';

-- ===== Truy vết (bổ sung) =====
COMMENT ON COLUMN production.source_object_mappings.id IS 'Khóa chính.';
COMMENT ON COLUMN production.source_object_mappings.source_id IS 'Hệ thống nguồn.';
COMMENT ON COLUMN production.source_object_mappings.object_type IS 'Loại đối tượng (machine/lot/process/product/material).';
COMMENT ON COLUMN production.source_object_mappings.valid_from IS 'Thời điểm bắt đầu hiệu lực.';
COMMENT ON COLUMN production.source_object_mappings.valid_to IS 'Thời điểm hết hiệu lực.';
COMMENT ON COLUMN production.source_object_mappings.confirmed IS 'Đã xác nhận.';
COMMENT ON COLUMN production.source_object_mappings.scenario_id IS 'Mã kịch bản mô phỏng.';
COMMENT ON COLUMN production.source_object_mappings.is_simulated IS 'Dữ liệu mô phỏng.';
COMMENT ON COLUMN production.source_object_mappings.created_at IS 'Thời điểm tạo.';

COMMENT ON COLUMN production.ingestion_records.id IS 'Khóa chính.';
COMMENT ON COLUMN production.ingestion_records.source_id IS 'Hệ thống nguồn.';
COMMENT ON COLUMN production.ingestion_records.request_id IS 'UUID chống gửi trùng.';
COMMENT ON COLUMN production.ingestion_records.event_time IS 'Thời gian sự kiện (do nguồn cung cấp).';
COMMENT ON COLUMN production.ingestion_records.received_at IS 'Thời gian hệ thống tiếp nhận.';
COMMENT ON COLUMN production.ingestion_records.created_business_ids IS 'ID bản ghi nghiệp vụ đã tạo (JSONB).';
COMMENT ON COLUMN production.ingestion_records.scenario_id IS 'Mã kịch bản mô phỏng.';
COMMENT ON COLUMN production.ingestion_records.is_simulated IS 'Dữ liệu mô phỏng.';
COMMENT ON COLUMN production.ingestion_records.created_at IS 'Thời điểm tạo.';

-- ===== Form sản lượng (bổ sung) =====
COMMENT ON COLUMN production.production_records.id IS 'Khóa chính.';
COMMENT ON COLUMN production.production_records.created_at IS 'Thời điểm tạo.';
