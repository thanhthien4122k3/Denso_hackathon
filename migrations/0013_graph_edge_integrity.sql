-- 0013: Toàn vẹn dữ liệu đồ thị — chặn cạnh tự nối và cạnh trùng.
-- Không DROP; chỉ xóa dữ liệu sai và thêm ràng buộc.

-- 1) Xóa cạnh tự nối (cùng source_type + source_id với target).
DELETE FROM production.graph_edges
WHERE source_type = target_type AND source_id = target_id;

-- 2) Xóa cạnh trùng lặp (giữ bản ghi id nhỏ nhất).
DELETE FROM production.graph_edges a
USING production.graph_edges b
WHERE a.source_type = b.source_type
  AND a.source_id = b.source_id
  AND a.target_type = b.target_type
  AND a.target_id = b.target_id
  AND a.kind = b.kind
  AND a.id > b.id;

-- 3) Thêm ràng buộc.
ALTER TABLE production.graph_edges
    ADD CONSTRAINT graph_edges_no_self_loop
        CHECK (source_type <> target_type OR source_id <> target_id);

ALTER TABLE production.graph_edges
    ADD CONSTRAINT graph_edges_unique_relation
        UNIQUE (source_type, source_id, target_type, target_id, kind);
