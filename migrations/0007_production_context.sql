-- 0007: Bối cảnh sản xuất, truy vết dữ liệu, hồ sơ kinh nghiệm và lịch sử sự cố.
-- Không DROP/TRUNCATE dữ liệu đã có. Chỉ ALTER ADD COLUMN và CREATE TABLE IF NOT EXISTS.

-- ---------------------------------------------------------------------------
-- Người dùng (tài khoản local, phân quyền tối thiểu cho demo xác nhận)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS production.users (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(200) NOT NULL,
    role VARCHAR(30) NOT NULL DEFAULT 'OPERATOR',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    is_simulated BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------------
-- Bối cảnh sản xuất: một lần lô được thực hiện tại công đoạn trên máy
-- trong một khoảng thời gian. Đối chiếu theo [started_at, ended_at).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS production.production_operations (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    lot_id BIGINT NOT NULL REFERENCES production.lots(id),
    process_id BIGINT NOT NULL REFERENCES production.processes(id),
    machine_id BIGINT REFERENCES production.machines(id),
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    status VARCHAR(30) NOT NULL DEFAULT 'IN_PROGRESS',
    context_status VARCHAR(30),
    source VARCHAR(100),
    confirmed_by VARCHAR(100),
    scenario_id VARCHAR(50),
    is_simulated BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (ended_at IS NULL OR ended_at >= started_at)
);

CREATE INDEX IF NOT EXISTS idx_production_operations_context
    ON production.production_operations (machine_id, started_at, ended_at);
CREATE INDEX IF NOT EXISTS idx_production_operations_lot
    ON production.production_operations (lot_id);

-- ---------------------------------------------------------------------------
-- Hàng đệm (buffer) giữa hai công đoạn.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS production.buffer_snapshots (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    upstream_process_id BIGINT REFERENCES production.processes(id),
    downstream_process_id BIGINT REFERENCES production.processes(id),
    product_id BIGINT REFERENCES production.products(id),
    lot_id BIGINT REFERENCES production.lots(id),
    available_qty NUMERIC NOT NULL,
    unit VARCHAR(20),
    recorded_at TIMESTAMPTZ NOT NULL,
    source VARCHAR(100),
    confirmed BOOLEAN NOT NULL DEFAULT FALSE,
    scenario_id VARCHAR(50),
    is_simulated BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (available_qty >= 0)
);

-- ---------------------------------------------------------------------------
-- Công suất tham chiếu (tốc độ) theo công đoạn/máy/sản phẩm, có hiệu lực.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS production.capacity_profiles (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    process_id BIGINT REFERENCES production.processes(id),
    machine_id BIGINT REFERENCES production.machines(id),
    product_id BIGINT REFERENCES production.products(id),
    rate_per_minute NUMERIC NOT NULL,
    unit VARCHAR(20),
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ,
    source_confirmation VARCHAR(100),
    scenario_id VARCHAR(50),
    is_simulated BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (rate_per_minute >= 0),
    CHECK (valid_to IS NULL OR valid_to >= valid_from)
);

-- ---------------------------------------------------------------------------
-- Ánh xạ mã nguồn (bên ngoài) -> đối tượng chuẩn, có phạm vi nguồn và hiệu lực.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS production.source_object_mappings (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_id BIGINT REFERENCES production.data_sources(id),
    object_type VARCHAR(30) NOT NULL,
    source_code VARCHAR(200) NOT NULL,
    node_id BIGINT,
    valid_from TIMESTAMPTZ,
    valid_to TIMESTAMPTZ,
    confirmed BOOLEAN NOT NULL DEFAULT FALSE,
    scenario_id VARCHAR(50),
    is_simulated BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (source_id, object_type, source_code)
);

-- ---------------------------------------------------------------------------
-- Nhật ký tiếp nhận dữ liệu (payload vào, trạng thái kiểm tra và lỗi).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS production.ingestion_records (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_id BIGINT REFERENCES production.data_sources(id),
    request_id UUID NOT NULL,
    event_time TIMESTAMPTZ,
    received_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    payload JSONB,
    status VARCHAR(30) NOT NULL DEFAULT 'VALID',
    error TEXT,
    created_business_ids JSONB,
    scenario_id VARCHAR(50),
    is_simulated BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ingestion_request_id ON production.ingestion_records (request_id);

-- ---------------------------------------------------------------------------
-- Hồ sơ kinh nghiệm xử lý (lessons learned).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS production.incident_experiences (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_incident_id BIGINT REFERENCES production.incidents(id),
    incident_type VARCHAR(30),
    error_code VARCHAR(100),
    machine_id BIGINT REFERENCES production.machines(id),
    process_id BIGINT REFERENCES production.processes(id),
    symptom TEXT,
    root_cause TEXT,
    actions TEXT,
    result TEXT,
    approved_by VARCHAR(100),
    approved_at TIMESTAMPTZ,
    scenario_id VARCHAR(50),
    is_simulated BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------------
-- Nhật ký diễn biến sự cố (audit).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS production.incident_history (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    incident_id BIGINT NOT NULL REFERENCES production.incidents(id) ON DELETE CASCADE,
    action VARCHAR(40) NOT NULL,
    changed_by VARCHAR(100),
    changed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    detail JSONB
);

CREATE INDEX IF NOT EXISTS idx_incident_history_incident
    ON production.incident_history (incident_id);

-- ---------------------------------------------------------------------------
-- Sự cố tương tự đã tham chiếu trong một lần phân tích.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS production.analysis_related_incidents (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES production.analysis_runs(id) ON DELETE CASCADE,
    related_incident_id BIGINT REFERENCES production.incidents(id),
    match_criteria TEXT,
    note TEXT
);

-- ---------------------------------------------------------------------------
-- Cột bổ sung cho hồ sơ sự cố: khôi phục, đóng, nguyên nhân.
-- ---------------------------------------------------------------------------
ALTER TABLE production.incidents
    ADD COLUMN IF NOT EXISTS recovered_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS recovered_by VARCHAR(100),
    ADD COLUMN IF NOT EXISTS closed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS closed_by VARCHAR(100),
    ADD COLUMN IF NOT EXISTS resolution_summary TEXT,
    ADD COLUMN IF NOT EXISTS root_cause_status VARCHAR(20) NOT NULL DEFAULT 'UNKNOWN'
        CHECK (root_cause_status IN ('UNKNOWN','HYPOTHESIS','CONFIRMED'));

-- ---------------------------------------------------------------------------
-- Cột bổ sung cho kết quả tác động: độ sâu quan hệ và trạng thái bằng chứng.
-- ---------------------------------------------------------------------------
ALTER TABLE production.analysis_impacts
    ADD COLUMN IF NOT EXISTS relation_depth VARCHAR(10)
        CHECK (relation_depth IN ('DIRECT','INDIRECT')),
    ADD COLUMN IF NOT EXISTS evidence_status VARCHAR(20)
        CHECK (evidence_status IN ('OBSERVED','POTENTIAL','ESTIMATED'));

-- ---------------------------------------------------------------------------
-- Công việc sinh từ đề xuất: truy được analysis_action_id.
-- ---------------------------------------------------------------------------
ALTER TABLE production.action_tasks
    ADD COLUMN IF NOT EXISTS analysis_action_id BIGINT
        REFERENCES production.analysis_actions(id) ON DELETE SET NULL;
