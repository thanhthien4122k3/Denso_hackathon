# Denso D3 — SQL read-only kiểm tra dữ liệu từng bước

Chạy trong `psql` hoặc pgAdmin trên database demo (`denso_hackathon_demo`).
Mọi truy vấn chỉ đọc. Thay `$incident_code` / `$incident_id` bằng giá trị thực tế.

## Bước 1 — Dữ liệu nền đã nạp

```sql
SELECT code, name, is_simulated FROM production.departments ORDER BY id;
SELECT code, name FROM production.processes ORDER BY id;
SELECT code, name FROM production.machines ORDER BY id;
SELECT code, name, production_order_id FROM production.lots ORDER BY id;

-- Lịch sử thực hiện
SELECT l.code AS lot, p.code AS process, m.code AS machine,
       started_at, ended_at, status
FROM production.production_operations po
JOIN production.lots l ON l.id = po.lot_id
JOIN production.processes p ON p.id = po.process_id
LEFT JOIN production.machines m ON m.id = po.machine_id
ORDER BY po.id;

-- Quan hệ (phụ thuộc sản xuất)
SELECT source_type, source_id, target_type, target_id, kind, label, valid_from
FROM production.graph_edges ORDER BY id;

-- Mẫu nhập sai mã (chưa ánh xạ)
SELECT request_id, status, error, payload FROM production.ingestion_records
WHERE status = 'NEEDS_MAPPING';
```

## Bước 2 — Bản ghi lỗi mới và sự cố

```sql
-- Sự kiện trạng thái
SELECT * FROM production.machine_states WHERE state = 'STOPPED' ORDER BY id DESC LIMIT 5;

-- Khoảng dừng đang mở
SELECT * FROM production.machine_downtimes WHERE end_time IS NULL ORDER BY id DESC;

-- Sự cố mới
SELECT * FROM production.incidents WHERE code = '$incident_code';
```

## Bước 3 — Lần chạy phân tích

```sql
SELECT id, run_at, rule_version, input, is_simulated
FROM production.analysis_runs WHERE source_id = $incident_id ORDER BY id DESC;

SELECT impact_type, relation_depth, evidence_status, node_type, node_name, evidence
FROM production.analysis_impacts WHERE run_id = $run_id ORDER BY id;

SELECT content, evidence, check_more, rule_id, priority
FROM production.analysis_hypotheses WHERE run_id = $run_id ORDER BY id;

SELECT department_name, action, priority
FROM production.analysis_actions WHERE run_id = $run_id ORDER BY id;

SELECT ri.related_incident_id, i.code, ri.match_criteria
FROM production.analysis_related_incidents ri
LEFT JOIN production.incidents i ON i.id = ri.related_incident_id
WHERE ri.run_id = $run_id;
```

## Bước 5 — Công việc từ đề xuất (chống trùng)

```sql
SELECT id, title, status, analysis_action_id, source_incident_id
FROM production.action_tasks WHERE source_incident_id = $incident_id ORDER BY id;
```

## Bước 6 — Phục hồi và phân tích lại

```sql
-- Trạng thái RUNNING sau phục hồi
SELECT * FROM production.machine_states WHERE state = 'RUNNING'
ORDER BY id DESC LIMIT 3;

-- Khoảng dừng đã đóng (tính thời lượng)
SELECT id, start_time, end_time, error_code,
       EXTRACT(EPOCH FROM (end_time - start_time))/60 AS duration_minutes
FROM production.machine_downtimes WHERE end_time IS NOT NULL ORDER BY id DESC;
```

## Bước 7 — Đóng hồ sơ và kinh nghiệm

```sql
SELECT code, status, root_cause_status, recovered_at, closed_at, closed_by,
       resolution_summary
FROM production.incidents WHERE id = $incident_id;

SELECT * FROM production.incident_experiences WHERE source_incident_id = $incident_id;

SELECT action, changed_by, changed_at, detail
FROM production.incident_history WHERE incident_id = $incident_id ORDER BY id;
```

## Đối chiếu JSON API / DB / UI

Bảng đối chiếu chính:

| JSON API (analysis result) | Cột DB |
|---|---|
| `context.lot_code` | `production_operations` + `lots.code` |
| `buffer_estimate.depletion_minutes` | tính từ `buffer_snapshots` / `capacity_profiles` |
| `capacity_estimate.estimated_quantity` | tính từ `capacity_profiles.rate_per_minute` |
| `related_past_incidents[].code` | `analysis_related_incidents` + `incidents.code` |
| `impacts[].relation_depth` | `analysis_impacts.relation_depth` |
| `impacts[].evidence_status` | `analysis_impacts.evidence_status` |

## Bối cảnh mơ hồ và xác minh

```sql
-- Ứng viên bối cảnh của sự cố (nhiều kết quả, không LIMIT 1)
SELECT po.id, l.code AS lot, p.code AS process, m.code AS machine,
       po.started_at, po.ended_at
FROM production.production_operations po
JOIN production.lots l ON l.id = po.lot_id
JOIN production.processes p ON p.id = po.process_id
LEFT JOIN production.machines m ON m.id = po.machine_id
WHERE po.machine_id = $machine_id
  AND po.started_at <= $at_time
  AND (po.ended_at IS NULL OR po.ended_at > $at_time)
ORDER BY po.started_at;

-- Xác minh bối cảnh (ai, khi nào, lựa chọn, lý do)
SELECT status, operation_ids, decided_by, decided_at, reason, evidence,
       candidate_snapshot
FROM production.incident_context_verifications
WHERE incident_id = $incident_id ORDER BY id;
```

## Xác thực & phiên

```sql
-- Tài khoản + vai trò
SELECT u.id, u.username, u.display_name, u.active, u.failed_attempts,
       array_agg(r.role) AS roles
FROM production.users u
LEFT JOIN production.user_roles r ON r.user_id = u.id
GROUP BY u.id ORDER BY u.id;

-- Phiên đang hoạt động (token đã băm, không lưu token thô)
SELECT user_id, created_at, expires_at, revoked_at
FROM production.sessions WHERE revoked_at IS NULL AND expires_at > now();

-- Nhật ký diễn biến sự cố (ai thao tác)
SELECT action, changed_by, changed_at, detail
FROM production.incident_history WHERE incident_id = $incident_id ORDER BY id;
```
