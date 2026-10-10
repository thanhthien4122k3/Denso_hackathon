-- 0012: Snapshot đầy đủ kết quả phân tích để tái hiện run cũ mà không tính lại
-- bằng dữ liệu hiện tại. Không DROP/TRUNCATE; chỉ ALTER ADD COLUMN.

ALTER TABLE production.analysis_runs
    ADD COLUMN IF NOT EXISTS result JSONB;
