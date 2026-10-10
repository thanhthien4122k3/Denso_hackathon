-- 0009: Mô tả bảng và cột (COMMENT) cho các bảng phân tích, bản đồ liên kết và bối cảnh.
-- Chỉ thêm metadata (COMMENT), không đổi cấu trúc hay dữ liệu.

-- ===== Bản đồ liên kết =====
COMMENT ON TABLE production.graph_edges IS 'Cạnh đồ thị liên kết hai lớp (nghiệp vụ sản xuất và logic hệ thống).';
COMMENT ON COLUMN production.graph_edges.source_type IS 'Loại node nguồn (department/line/process/machine/material/product/order/lot/shift/source/dataset/field).';
COMMENT ON COLUMN production.graph_edges.source_id IS 'ID node nguồn trong bảng tương ứng.';
COMMENT ON COLUMN production.graph_edges.target_type IS 'Loại node đích.';
COMMENT ON COLUMN production.graph_edges.target_id IS 'ID node đích.';
COMMENT ON COLUMN production.graph_edges.kind IS 'Loại cạnh: production_dependency, data_flow, data_mapping, department_responsibility.';
COMMENT ON COLUMN production.graph_edges.label IS 'Mô tả ngắn quan hệ (ví dụ "Máy phục vụ công đoạn").';
COMMENT ON COLUMN production.graph_edges.source_confirmation IS 'Nguồn xác nhận quan hệ.';
COMMENT ON COLUMN production.graph_edges.valid_from IS 'Thời điểm quan hệ bắt đầu có hiệu lực.';
COMMENT ON COLUMN production.graph_edges.valid_to IS 'Thời điểm quan hệ hết hiệu lực (null = còn hiệu lực).';
COMMENT ON COLUMN production.graph_edges.is_simulated IS 'true nếu là dữ liệu mô phỏng.';

-- ===== Bối cảnh sản xuất =====
COMMENT ON TABLE production.production_operations IS 'Một lần lô được thực hiện tại công đoạn trên máy trong khoảng [started_at, ended_at).';
COMMENT ON COLUMN production.production_operations.lot_id IS 'Lô đang thực hiện.';
COMMENT ON COLUMN production.production_operations.process_id IS 'Công đoạn thực hiện.';
COMMENT ON COLUMN production.production_operations.machine_id IS 'Máy thực hiện (null nếu công đoạn thủ công).';
COMMENT ON COLUMN production.production_operations.started_at IS 'Thời điểm bắt đầu.';
COMMENT ON COLUMN production.production_operations.ended_at IS 'Thời điểm kết thúc (null = chưa kết thúc được ghi nhận).';
COMMENT ON COLUMN production.production_operations.status IS 'Trạng thái thực hiện (IN_PROGRESS/COMPLETED...).';
COMMENT ON COLUMN production.production_operations.source IS 'Nguồn thông tin.';
COMMENT ON COLUMN production.production_operations.scenario_id IS 'Mã kịch bản mô phỏng (nếu là dữ liệu demo).';

-- ===== Hàng đệm =====
COMMENT ON TABLE production.buffer_snapshots IS 'Lượng hàng đệm khả dụng giữa hai công đoạn tại một thời điểm.';
COMMENT ON COLUMN production.buffer_snapshots.upstream_process_id IS 'Công đoạn trước.';
COMMENT ON COLUMN production.buffer_snapshots.downstream_process_id IS 'Công đoạn sau.';
COMMENT ON COLUMN production.buffer_snapshots.product_id IS 'Sản phẩm trong hàng đệm.';
COMMENT ON COLUMN production.buffer_snapshots.lot_id IS 'Lô (nếu biết).';
COMMENT ON COLUMN production.buffer_snapshots.available_qty IS 'Số lượng khả dụng.';
COMMENT ON COLUMN production.buffer_snapshots.recorded_at IS 'Thời điểm ghi nhận.';

-- ===== Công suất =====
COMMENT ON TABLE production.capacity_profiles IS 'Công suất tham chiếu (tốc độ) theo công đoạn/máy/sản phẩm.';
COMMENT ON COLUMN production.capacity_profiles.rate_per_minute IS 'Tốc độ (đơn vị/phút).';
COMMENT ON COLUMN production.capacity_profiles.valid_from IS 'Thời điểm bắt đầu hiệu lực.';
COMMENT ON COLUMN production.capacity_profiles.valid_to IS 'Thời điểm hết hiệu lực (null = còn hiệu lực).';

-- ===== Lưu vết phân tích =====
COMMENT ON TABLE production.analysis_runs IS 'Một lần chạy phân tích tác động (snapshot bất biến).';
COMMENT ON COLUMN production.analysis_runs.source_type IS 'INCIDENT (theo sự cố) hoặc SCENARIO (what-if).';
COMMENT ON COLUMN production.analysis_runs.source_id IS 'ID sự cố hoặc đối tượng giả định.';
COMMENT ON COLUMN production.analysis_runs.input IS 'Đầu vào (JSONB): incident_id, max_depth, duration_minutes, rate_per_minute, assumptions.';
COMMENT ON COLUMN production.analysis_runs.rule_version IS 'Phiên bản bộ quy tắc đã dùng.';

COMMENT ON TABLE production.analysis_impacts IS 'Đối tượng bị ảnh hưởng trong một lần phân tích.';
COMMENT ON COLUMN production.analysis_impacts.impact_type IS 'DIRECT/INDIRECT/RISK/OBSERVED/ESTIMATED.';
COMMENT ON COLUMN production.analysis_impacts.relation_depth IS 'Độ sâu quan hệ: DIRECT hoặc INDIRECT.';
COMMENT ON COLUMN production.analysis_impacts.evidence_status IS 'Trạng thái bằng chứng: OBSERVED/POTENTIAL/ESTIMATED.';
COMMENT ON COLUMN production.analysis_impacts.path IS 'Đường lan truyền (JSONB).';
COMMENT ON COLUMN production.analysis_impacts.evidence IS 'Bằng chứng đã dùng.';
COMMENT ON COLUMN production.analysis_impacts.rule_id IS 'Quy tắc áp dụng.';
COMMENT ON COLUMN production.analysis_impacts.assumptions IS 'Giả định đã dùng.';
COMMENT ON COLUMN production.analysis_impacts.missing_info IS 'Thông tin còn thiếu.';

COMMENT ON TABLE production.analysis_hypotheses IS 'Giả thuyết nguyên nhân trong một lần phân tích.';
COMMENT ON COLUMN production.analysis_hypotheses.content IS 'Nội dung giả thuyết.';
COMMENT ON COLUMN production.analysis_hypotheses.evidence IS 'Bằng chứng ủng hộ.';
COMMENT ON COLUMN production.analysis_hypotheses.check_more IS 'Thông tin cần kiểm tra thêm.';

COMMENT ON TABLE production.analysis_actions IS 'Hành động đề xuất theo bộ phận trong một lần phân tích.';
COMMENT ON COLUMN production.analysis_actions.department_name IS 'Tên bộ phận nhận việc.';
COMMENT ON COLUMN production.analysis_actions.action IS 'Nội dung hành động đề xuất.';

COMMENT ON TABLE production.analysis_related_incidents IS 'Sự cố cũ tương tự được tham chiếu trong một lần phân tích.';
COMMENT ON COLUMN production.analysis_related_incidents.related_incident_id IS 'ID sự cố cũ tương tự.';
COMMENT ON COLUMN production.analysis_related_incidents.match_criteria IS 'Tiêu chí khớp (ví dụ: cùng máy, cùng mã lỗi).';

-- ===== Sự cố =====
COMMENT ON TABLE production.incidents IS 'Hồ sơ sự cố.';
COMMENT ON COLUMN production.incidents.source_object_type IS 'Loại đối tượng phát sinh (machine/lot/material/process/product/dataset/line/order).';
COMMENT ON COLUMN production.incidents.source_object_id IS 'ID đối tượng phát sinh.';
COMMENT ON COLUMN production.incidents.root_cause_status IS 'Trạng thái nguyên nhân: UNKNOWN/HYPOTHESIS/CONFIRMED.';
COMMENT ON COLUMN production.incidents.recovered_at IS 'Thời điểm khôi phục.';
COMMENT ON COLUMN production.incidents.recovered_by IS 'Người xác nhận khôi phục.';
COMMENT ON COLUMN production.incidents.closed_at IS 'Thời điểm đóng hồ sơ.';
COMMENT ON COLUMN production.incidents.closed_by IS 'Người đóng hồ sơ.';
COMMENT ON COLUMN production.incidents.resolution_summary IS 'Tóm tắt kết quả xử lý.';

COMMENT ON TABLE production.incident_causes IS 'Nguyên nhân sự cố (giả thuyết hoặc đã xác nhận).';
COMMENT ON COLUMN production.incident_causes.kind IS 'HYPOTHESIS (giả thuyết) hoặc CONFIRMED (đã xác nhận).';

COMMENT ON TABLE production.incident_context_verifications IS 'Xác minh bối cảnh sản xuất của sự cố.';
COMMENT ON COLUMN production.incident_context_verifications.operation_ids IS 'Danh sách ID production_operations đã chọn.';
COMMENT ON COLUMN production.incident_context_verifications.status IS 'CONFIRMED/REJECTED/UNRESOLVED.';
COMMENT ON COLUMN production.incident_context_verifications.decided_by IS 'Người xác minh.';
COMMENT ON COLUMN production.incident_context_verifications.reason IS 'Lý do xác minh.';
COMMENT ON COLUMN production.incident_context_verifications.candidate_snapshot IS 'Snapshot các ứng viên tại thời điểm xác minh.';

-- ===== Truy vết dữ liệu =====
COMMENT ON TABLE production.source_object_mappings IS 'Ánh xạ mã nguồn (bên ngoài) -> đối tượng chuẩn.';
COMMENT ON COLUMN production.source_object_mappings.source_code IS 'Mã nguồn bên ngoài (ví dụ CNC-01).';
COMMENT ON COLUMN production.source_object_mappings.node_id IS 'ID đối tượng chuẩn (null = chưa ánh xạ).';

COMMENT ON TABLE production.ingestion_records IS 'Nhật ký tiếp nhận dữ liệu (payload, trạng thái kiểm tra, lỗi).';
COMMENT ON COLUMN production.ingestion_records.status IS 'VALID/NEEDS_MAPPING/NEEDS_LINKING/REJECTED.';
COMMENT ON COLUMN production.ingestion_records.payload IS 'Payload nhận vào (JSONB).';
COMMENT ON COLUMN production.ingestion_records.error IS 'Lỗi khi kiểm tra/chuẩn hóa.';
