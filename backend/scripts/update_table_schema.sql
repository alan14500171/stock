-- 更新 stock_transactions 表结构
ALTER TABLE stock.stock_transactions
ADD COLUMN realized_pnl DECIMAL(20,5) DEFAULT 0.00000 COMMENT '已实现盈亏',
ADD COLUMN realized_pnl_ratio DECIMAL(10,5) DEFAULT 0.00000 COMMENT '盈亏比率（%）';

-- 更新现有记录的默认值
UPDATE stock.stock_transactions
SET realized_pnl = 0.00000,
    realized_pnl_ratio = 0.00000
WHERE realized_pnl IS NULL
   OR realized_pnl_ratio IS NULL; 