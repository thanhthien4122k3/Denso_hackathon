-- 0005: Quản lý sự cố + nguyên nhân (giả thuyết / đã xác nhận) + liên kết bản ghi vận hành.

CREATE TABLE IF NOT EXISTS production.incidents (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    title VARCHAR(300) NOT NULL,
    incident_type VARCHAR(30) NOT NULL
        CHECK (incident_type IN ('MACHINE_STOP','QUALITY','MATERIAL_SHORTAGE','DATA_DELAY','OTHER')),
    source_object_type VARCHAR(30),
    source_object_id BIGINT,
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    severity VARCHAR(20) NOT NULL DEFAULT 'MEDIUM'
        CHECK (severity IN ('LOW','MEDIUM','HIGH','CRITICAL')),
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN'
        CHECK (status IN ('OPEN','INVESTIGATING','MITIGATING','RESOLVED')),
    assigned_department_id BIGINT REFERENCES production.departments(id),
    request_id UUID NOT NULL UNIQUE,
    is_simulated BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS production.incident_causes (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    incident_id BIGINT NOT NULL REFERENCES production.incidents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    kind VARCHAR(20) NOT NULL CHECK (kind IN ('HYPOTHESIS','CONFIRMED')),
    evidence TEXT,
    rule_id VARCHAR(50),
    priority VARCHAR(20),
    confirmed_by VARCHAR(100),
    confirmed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS production.incident_links (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    incident_id BIGINT NOT NULL REFERENCES production.incidents(id) ON DELETE CASCADE,
    source_type VARCHAR(30) NOT NULL,
    source_id BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_incidents_status ON production.incidents (status);
CREATE INDEX IF NOT EXISTS idx_incidents_type ON production.incidents (incident_type);
