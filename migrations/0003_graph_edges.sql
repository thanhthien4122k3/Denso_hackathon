-- 0003: Đồ thị liên kết hai lớp (node/edge).

CREATE TABLE IF NOT EXISTS production.graph_edges (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_type VARCHAR(30) NOT NULL
        CHECK (source_type IN ('department','line','process','machine','material',
                               'product','order','lot','shift','source','dataset','field')),
    source_id BIGINT NOT NULL,
    target_type VARCHAR(30) NOT NULL
        CHECK (target_type IN ('department','line','process','machine','material',
                               'product','order','lot','shift','source','dataset','field')),
    target_id BIGINT NOT NULL,
    kind VARCHAR(40) NOT NULL
        CHECK (kind IN ('production_dependency','data_flow','data_mapping',
                        'department_responsibility')),
    label VARCHAR(200),
    description TEXT,
    source_confirmation VARCHAR(100),
    valid_from TIMESTAMPTZ,
    valid_to TIMESTAMPTZ,
    is_simulated BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_graph_edges_source ON production.graph_edges (source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_graph_edges_target ON production.graph_edges (target_type, target_id);
