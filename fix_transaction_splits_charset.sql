-- 修复transaction_splits表的字符集和排序规则问题
-- 将表的字符集从utf8mb4_0900_ai_ci改为utf8mb4_unicode_ci

-- 1. 修改表的字符集和排序规则
ALTER TABLE `transaction_splits` 
CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 2. 修改各个字符串列的字符集和排序规则
ALTER TABLE `transaction_splits` 
MODIFY `holder_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '持有人名称',
MODIFY `stock_code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
MODIFY `stock_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票名称',
MODIFY `market` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '市场',
MODIFY `transaction_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '交易编号',
MODIFY `transaction_type` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '交易类型(买入/卖出)',
MODIFY `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '备注';

-- 3. 修复avg_price字段，确保它存在且有正确的类型
-- 检查avg_price字段是否存在，如果不存在则添加
SET @column_exists = 0;
SELECT COUNT(*) INTO @column_exists 
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = 'stock' 
AND TABLE_NAME = 'transaction_splits' 
AND COLUMN_NAME = 'avg_price';

SET @add_column = CONCAT("ALTER TABLE `transaction_splits` ADD COLUMN `avg_price` decimal(10,4) DEFAULT NULL COMMENT '平均价格'");
SET @alter_column = CONCAT("ALTER TABLE `transaction_splits` MODIFY COLUMN `avg_price` decimal(10,4) DEFAULT NULL COMMENT '平均价格'");

SET @sql = IF(@column_exists > 0, @alter_column, @add_column);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 4. 检查并修复running_quantity和running_cost字段
-- 确保这些字段存在且有正确的类型
ALTER TABLE `transaction_splits` 
MODIFY `running_quantity` int DEFAULT NULL COMMENT '累计数量',
MODIFY `running_cost` decimal(10,2) DEFAULT NULL COMMENT '累计成本';

-- 5. 更新表注释
ALTER TABLE `transaction_splits` COMMENT='交易分单记录';

-- 6. 确保外键约束正确
-- 检查外键约束是否存在
SELECT COUNT(*) INTO @fk_exists 
FROM information_schema.TABLE_CONSTRAINTS 
WHERE CONSTRAINT_SCHEMA = 'stock' 
AND TABLE_NAME = 'transaction_splits' 
AND CONSTRAINT_NAME = 'fk_original_transaction_id' 
AND CONSTRAINT_TYPE = 'FOREIGN KEY';

-- 如果外键约束不存在，添加它
SET @add_fk = CONCAT("ALTER TABLE `transaction_splits` ADD CONSTRAINT `fk_original_transaction_id` FOREIGN KEY (`original_transaction_id`) REFERENCES `stock_transactions` (`id`) ON DELETE CASCADE");

SET @sql = IF(@fk_exists = 0, @add_fk, 'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查holder_id外键约束是否存在
SELECT COUNT(*) INTO @fk_holder_exists 
FROM information_schema.TABLE_CONSTRAINTS 
WHERE CONSTRAINT_SCHEMA = 'stock' 
AND TABLE_NAME = 'transaction_splits' 
AND CONSTRAINT_NAME = 'fk_ts_holder_id' 
AND CONSTRAINT_TYPE = 'FOREIGN KEY';

-- 如果holder_id外键约束不存在，添加它
SET @add_holder_fk = CONCAT("ALTER TABLE `transaction_splits` ADD CONSTRAINT `fk_ts_holder_id` FOREIGN KEY (`holder_id`) REFERENCES `holders` (`id`)");

SET @sql = IF(@fk_holder_exists = 0, @add_holder_fk, 'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt; 