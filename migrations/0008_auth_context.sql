-- 0008: Đăng nhập local, phân quyền, phiên đăng nhập và xác minh bối cảnh.
-- Không DROP/TRUNCATE. Chỉ ALTER ADD COLUMN và CREATE TABLE IF NOT EXISTS.

-- ---------------------------------------------------------------------------
-- Tài khoản: thêm trường băm mật khẩu và chống đoán mật khẩu.
-- ---------------------------------------------------------------------------
ALTER TABLE production.users
    ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255),
    ADD COLUMN IF NOT EXISTS failed_attempts INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS locked_until TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMPTZ;

-- ---------------------------------------------------------------------------
-- Vai trò: một người có thể có nhiều vai trò.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS production.user_roles (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES production.users(id) ON DELETE CASCADE,
    role VARCHAR(30) NOT NULL,
    UNIQUE (user_id, role)
);

-- ---------------------------------------------------------------------------
-- Phiên đăng nhập phía server (cookie HttpOnly lưu token, DB lưu hash).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS production.sessions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    user_id BIGINT NOT NULL REFERENCES production.users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON production.sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON production.sessions (expires_at);

-- ---------------------------------------------------------------------------
-- Xác minh bối cảnh sản xuất của sự cố (ai xác minh, khi nào, lựa chọn, lý do).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS production.incident_context_verifications (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    incident_id BIGINT NOT NULL REFERENCES production.incidents(id) ON DELETE CASCADE,
    operation_ids JSONB NOT NULL DEFAULT '[]',
    status VARCHAR(20) NOT NULL,
    decided_by BIGINT REFERENCES production.users(id),
    decided_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reason TEXT,
    evidence TEXT,
    candidate_snapshot JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (status IN ('CONFIRMED', 'REJECTED', 'UNRESOLVED'))
);

CREATE INDEX IF NOT EXISTS idx_context_verifications_incident
    ON production.incident_context_verifications (incident_id);
