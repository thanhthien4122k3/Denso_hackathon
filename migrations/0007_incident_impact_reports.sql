-- 0007: Incident Reports and Automated Impact Analysis (Trigger based)

CREATE TABLE IF NOT EXISTS production.incident_reports (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    incident_id BIGINT NOT NULL UNIQUE REFERENCES production.incidents(id) ON DELETE CASCADE,
    severity VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    affected_count INT NOT NULL DEFAULT 0,
    departments JSONB,
    task_count INT NOT NULL DEFAULT 0,
    latest_run_id BIGINT REFERENCES production.analysis_runs(id) ON DELETE SET NULL,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE OR REPLACE FUNCTION production.fn_incident_impact()
RETURNS TRIGGER AS $$
DECLARE
    v_incident_id BIGINT;
    v_source_type VARCHAR(30);
    v_source_id BIGINT;
    v_severity VARCHAR(20);
    v_status VARCHAR(20);
    v_is_simulated BOOLEAN;
    v_run_id BIGINT;
    v_affected_count INT := 0;
    v_task_count INT := 0;
    v_departments JSONB := '[]'::jsonb;
BEGIN
    -- Determine incident details based on TG_OP
    IF TG_OP = 'INSERT' AND TG_TABLE_NAME = 'incidents' THEN
        v_incident_id := NEW.id;
        v_source_type := NEW.source_object_type;
        v_source_id := NEW.source_object_id;
        v_severity := NEW.severity;
        v_status := NEW.status;
        v_is_simulated := NEW.is_simulated;
    ELSIF TG_OP = 'UPDATE' AND TG_TABLE_NAME = 'incidents' THEN
        v_incident_id := NEW.id;
        v_source_type := NEW.source_object_type;
        v_source_id := NEW.source_object_id;
        v_severity := NEW.severity;
        v_status := NEW.status;
        v_is_simulated := NEW.is_simulated;
    ELSIF TG_OP = 'INSERT' AND TG_TABLE_NAME = 'incident_links' THEN
        v_incident_id := NEW.incident_id;
        SELECT source_object_type, source_object_id, severity, status, is_simulated
        INTO v_source_type, v_source_id, v_severity, v_status, v_is_simulated
        FROM production.incidents WHERE id = v_incident_id;
    END IF;

    -- Only proceed if we have a source object to trace from
    IF v_source_type IS NOT NULL AND v_source_id IS NOT NULL THEN
        -- 1. Create analysis run
        INSERT INTO production.analysis_runs (source_type, source_id, input, rule_version, is_simulated, run_at)
        VALUES ('INCIDENT', v_incident_id, jsonb_build_object('trigger', 'auto', 'source_type', v_source_type, 'source_id', v_source_id), 'auto_trigger', v_is_simulated, CURRENT_TIMESTAMP)
        RETURNING id INTO v_run_id;

        -- 2. Trace impacts using recursive CTE (max depth 3)
        WITH RECURSIVE impact_trace AS (
            -- Base case: edges starting from the incident's source
            SELECT target_type, target_id, kind, 1 as depth, ARRAY[source_type || '#' || source_id] as path
            FROM production.graph_edges
            WHERE source_type = v_source_type AND source_id = v_source_id
            
            UNION ALL
            
            -- Recursive step
            SELECT e.target_type, e.target_id, e.kind, it.depth + 1, it.path || (e.source_type || '#' || e.source_id)
            FROM production.graph_edges e
            INNER JOIN impact_trace it ON e.source_type = it.target_type AND e.source_id = it.target_id
            WHERE it.depth < 3 AND NOT (e.target_type || '#' || e.target_id = ANY(it.path)) -- Prevent cycles
        )
        INSERT INTO production.analysis_impacts (run_id, node_type, node_id, node_name, impact_type, path, evidence)
        SELECT DISTINCT ON (target_type, target_id)
            v_run_id, 
            target_type, 
            target_id, 
            target_type || '#' || target_id, -- Placeholder name, Python can update this later if needed
            CASE WHEN depth = 1 THEN 'DIRECT' ELSE 'INDIRECT' END,
            to_jsonb(path),
            'Automated trace via ' || kind
        FROM impact_trace;

        GET DIAGNOSTICS v_affected_count = ROW_COUNT;
        
        -- Generate tasks for assigned departments from the incident if any, for simplicity
        -- In a real hybrid, Python rules would generate more specific tasks.
        -- We just count current tasks for the incident
        SELECT COUNT(*) INTO v_task_count FROM production.action_tasks WHERE source_incident_id = v_incident_id;
    ELSE
        -- If no source object, we can't trace graph
        v_run_id := NULL;
        v_affected_count := 0;
        SELECT COUNT(*) INTO v_task_count FROM production.action_tasks WHERE source_incident_id = v_incident_id;
    END IF;
    
    -- Extract distinct departments from action_tasks related to this incident
    SELECT COALESCE(jsonb_agg(DISTINCT jsonb_build_object('id', d.id, 'name', d.name)), '[]'::jsonb)
    INTO v_departments
    FROM production.action_tasks at
    JOIN production.departments d ON d.id = at.department_id
    WHERE at.source_incident_id = v_incident_id;

    -- 3. Upsert into incident_reports
    INSERT INTO production.incident_reports (
        incident_id, severity, status, affected_count, departments, task_count, latest_run_id, generated_at, updated_at
    ) VALUES (
        v_incident_id, v_severity, v_status, v_affected_count, v_departments, v_task_count, v_run_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    )
    ON CONFLICT (incident_id) DO UPDATE SET
        severity = EXCLUDED.severity,
        status = EXCLUDED.status,
        affected_count = EXCLUDED.affected_count,
        departments = EXCLUDED.departments,
        task_count = EXCLUDED.task_count,
        latest_run_id = EXCLUDED.latest_run_id,
        updated_at = CURRENT_TIMESTAMP;

    RETURN NEW;
EXCEPTION WHEN OTHERS THEN
    -- Fallback: Do not block incident creation on failure
    RAISE WARNING 'fn_incident_impact failed: %', SQLERRM;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_incident_impact_insert ON production.incidents;
CREATE TRIGGER trigger_incident_impact_insert
AFTER INSERT ON production.incidents
FOR EACH ROW EXECUTE FUNCTION production.fn_incident_impact();

DROP TRIGGER IF EXISTS trigger_incident_impact_update ON production.incidents;
CREATE TRIGGER trigger_incident_impact_update
AFTER UPDATE OF status, severity ON production.incidents
FOR EACH ROW EXECUTE FUNCTION production.fn_incident_impact();

DROP TRIGGER IF EXISTS trigger_incident_impact_link ON production.incident_links;
CREATE TRIGGER trigger_incident_impact_link
AFTER INSERT ON production.incident_links
FOR EACH ROW EXECUTE FUNCTION production.fn_incident_impact();
