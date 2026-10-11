-- 0014: Bổ sung cột định lượng cho lot và lệnh sản xuất.
-- lots.qty: quy mô lô (số lượng); production_orders.plan_qty: kế hoạch sản lượng.

ALTER TABLE production.lots
    ADD COLUMN IF NOT EXISTS qty NUMERIC;

ALTER TABLE production.production_orders
    ADD COLUMN IF NOT EXISTS plan_qty NUMERIC;

COMMENT ON COLUMN production.lots.qty IS 'Quy mô lô (số lượng, nullable).';
COMMENT ON COLUMN production.production_orders.plan_qty IS 'Kế hoạch sản lượng của lệnh (nullable).';
