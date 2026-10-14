-- 0015: Kết nối database nguồn và batch nhập dữ liệu (staging).
-- Chỉ phục vụ đọc dữ liệu nguồn bên ngoài và theo dõi các batch nhập.

CREATE TABLE IF NOT EXISTS production.source_connection_profiles (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_id BIGINT REFERENCES production.data_sources(id) ON DELETE SET NULL,
    db_type VARCHAR(30) NOT NULL,
    host VARCHAR(255) NOT NULL,
    port INTEGER,
    database_name VARCHAR(255),
    username VARCHAR(255),
    password_encrypted TEXT,
    ssl_mode VARCHAR(30),
    extra_options JSONB,
    last_status VARCHAR(30),
    last_checked_at TIMESTAMPTZ,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS production.ingestion_batches (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_id BIGINT REFERENCES production.data_sources(id) ON DELETE SET NULL,
    connection_id BIGINT REFERENCES production.source_connection_profiles(id) ON DELETE SET NULL,
    dataset_id BIGINT REFERENCES production.datasets(id) ON DELETE SET NULL,
    input_type VARCHAR(20) NOT NULL,
    source_name VARCHAR(255),
    checksum VARCHAR(64),
    target_type VARCHAR(50),
    created_by VARCHAR(100),
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_rows INTEGER NOT NULL DEFAULT 0,
    valid_rows INTEGER NOT NULL DEFAULT 0,
    error_rows INTEGER NOT NULL DEFAULT 0,
    duplicate_rows INTEGER NOT NULL DEFAULT 0,
    imported_rows INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
    error_summary JSONB,
    mapping JSONB,
    rows JSONB,
    created_business_ids JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON COLUMN production.source_connection_profiles.password_encrypted IS 'Mật khẩu đã mã hóa (không lưu plaintext).';
COMMENT ON COLUMN production.ingestion_batches.rows IS 'Dữ liệu staging đã ánh xạ trước khi xác nhận nhập.';
