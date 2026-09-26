-- 0006: Lưu vết phân tích, công việc theo bộ phận, khảo sát.

CREATE TABLE IF NOT EXISTS production.analysis_runs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_type VARCHAR(20) NOT NULL CHECK (source_type IN ('INCIDENT','SCENARIO')),
    source_id BIGINT,
    run_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    input JSONB,
    rule_version VARCHAR(50),
    is_simulated BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS production.analysis_impacts (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES production.analysis_runs(id) ON DELETE CASCADE,
    node_type VARCHAR(30) NOT NULL,
    node_id BIGINT NOT NULL,
    node_name VARCHAR(300),
    impact_type VARCHAR(20) NOT NULL
        CHECK (impact_type IN ('DIRECT','INDIRECT','RISK','OBSERVED','ESTIMATED')),
    path JSONB,
    evidence TEXT,
    rule_id VARCHAR(50),
    assumptions TEXT,
    missing_info TEXT,
    departments JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS production.analysis_hypotheses (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES production.analysis_runs(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    evidence TEXT,
    check_more TEXT,
    rule_id VARCHAR(50),
    priority VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS production.analysis_actions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES production.analysis_runs(id) ON DELETE CASCADE,
    department_id BIGINT,
    department_name VARCHAR(200),
    action TEXT NOT NULL,
    priority VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS production.action_tasks (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    department_id BIGINT REFERENCES production.departments(id),
    title VARCHAR(300) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'TODO'
        CHECK (status IN ('TODO','IN_PROGRESS','DONE','DISMISSED')),
    priority VARCHAR(20),
    source_incident_id BIGINT REFERENCES production.incidents(id),
    source_analysis_run_id BIGINT REFERENCES production.analysis_runs(id),
    rule_id VARCHAR(50),
    is_simulated BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS production.survey_items (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    group_code VARCHAR(50) NOT NULL,
    question TEXT NOT NULL,
    answer TEXT,
    provided_by VARCHAR(100),
    provided_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'UNCONFIRMED'
        CHECK (status IN ('UNCONFIRMED','CONFIRMED')),
    note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_action_tasks_status ON production.action_tasks (status);
CREATE INDEX IF NOT EXISTS idx_action_tasks_department ON production.action_tasks (department_id);
