-- 0004: Ghi nhận vận hành (trạng thái thiết bị, dừng máy, QC, vật tư).

CREATE TABLE IF NOT EXISTS production.machine_states (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    machine_id BIGINT NOT NULL REFERENCES production.machines(id),
    event_time TIMESTAMPTZ NOT NULL,
    state VARCHAR(20) NOT NULL
        CHECK (state IN ('RUNNING','STOPPED','MAINTENANCE','UNKNOWN')),
    error_code VARCHAR(100),
    note TEXT,
    received_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_simulated BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS production.machine_downtimes (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    machine_id BIGINT NOT NULL REFERENCES production.machines(id),
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    reason VARCHAR(200),
    error_code VARCHAR(100),
    operator_name VARCHAR(100),
    received_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_simulated BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (end_time IS NULL OR end_time >= start_time)
);

CREATE TABLE IF NOT EXISTS production.qc_results (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    lot_id BIGINT NOT NULL REFERENCES production.lots(id),
    product_id BIGINT REFERENCES production.products(id),
    process_id BIGINT REFERENCES production.processes(id),
    check_time TIMESTAMPTZ NOT NULL,
    inspected_qty INTEGER NOT NULL CHECK (inspected_qty >= 0),
    defect_qty INTEGER NOT NULL CHECK (defect_qty >= 0),
    defect_type VARCHAR(100),
    result VARCHAR(10) NOT NULL CHECK (result IN ('PASS','FAIL','HOLD')),
    note TEXT,
    received_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_simulated BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (defect_qty <= inspected_qty)
);

CREATE TABLE IF NOT EXISTS production.material_statuses (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    material_id BIGINT NOT NULL REFERENCES production.materials(id),
    recorded_at TIMESTAMPTZ NOT NULL,
    available_qty NUMERIC NOT NULL,
    unit VARCHAR(20),
    scope VARCHAR(100),
    received_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_simulated BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
