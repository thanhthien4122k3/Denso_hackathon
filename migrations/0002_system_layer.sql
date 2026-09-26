-- 0002: Lớp logic hệ thống & nguồn dữ liệu.

CREATE TABLE IF NOT EXISTS production.data_sources (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    source_type VARCHAR(30) NOT NULL,
    collection_method VARCHAR(30),
    owner_department_id BIGINT REFERENCES production.departments(id),
    location_metadata TEXT,
    confirmed BOOLEAN NOT NULL DEFAULT FALSE,
    is_simulated BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS production.datasets (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    source_id BIGINT REFERENCES production.data_sources(id),
    dataset_type VARCHAR(30),
    storage_location TEXT,
    collection_method VARCHAR(30),
    owner_department_id BIGINT REFERENCES production.departments(id),
    generation_unit VARCHAR(30),
    update_schedule VARCHAR(30),
    event_time_field VARCHAR(100),
    timezone VARCHAR(50),
    update_frequency VARCHAR(100),
    expected_latency VARCHAR(100),
    last_received_at TIMESTAMPTZ,
    confirmed BOOLEAN NOT NULL DEFAULT FALSE,
    is_simulated BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS production.dataset_fields (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset_id BIGINT NOT NULL REFERENCES production.datasets(id) ON DELETE CASCADE,
    code VARCHAR(100) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    data_type VARCHAR(30),
    is_key BOOLEAN NOT NULL DEFAULT FALSE,
    confirmed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (dataset_id, code)
);

CREATE TABLE IF NOT EXISTS production.data_flows (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    source_dataset_id BIGINT NOT NULL REFERENCES production.datasets(id),
    target_dataset_id BIGINT NOT NULL REFERENCES production.datasets(id),
    description TEXT,
    confirmed BOOLEAN NOT NULL DEFAULT FALSE,
    is_simulated BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (source_dataset_id <> target_dataset_id)
);
