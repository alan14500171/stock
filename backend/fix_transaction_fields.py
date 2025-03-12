#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复交易记录中缺少的字段

此脚本用于修复stock_transactions表中缺少的running_quantity、running_cost、updated_at字段，
以及transaction_splits表中缺少的running_quantity、running_cost字段。
"""

import logging
from config.database import db
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def fix_transaction_fields():
    """修复交易记录中缺少的字段"""
    try:
        # 查询缺少running_quantity或running_cost的记录数
        null_check_query = """
        SELECT COUNT(*) as count_null 
        FROM stock_transactions 
        WHERE running_quantity IS NULL OR running_cost IS NULL
        """
        null_results = db.fetch_one(null_check_query)
        logger.info(f"发现缺少running_quantity或running_cost的记录数: {null_results['count_null']}")

        # 查询缺少updated_at的记录数
        updated_check_query = """
        SELECT COUNT(*) as count_null 
        FROM stock_transactions 
        WHERE updated_at IS NULL
        """
        updated_results = db.fetch_one(updated_check_query)
        logger.info(f"发现缺少updated_at的记录数: {updated_results['count_null']}")

        # 更新主交易记录
        update_query = """
        UPDATE stock_transactions 
        SET running_quantity = current_quantity, 
            running_cost = current_cost, 
            updated_at = COALESCE(updated_at, created_at, NOW())
        WHERE running_quantity IS NULL OR running_cost IS NULL OR updated_at IS NULL
        """
        db.execute(update_query)
        logger.info("已更新主交易记录")

        # 查询分单记录中缺少running_quantity或running_cost的记录数
        splits_null_check_query = """
        SELECT COUNT(*) as count_null 
        FROM transaction_splits 
        WHERE running_quantity IS NULL OR running_cost IS NULL
        """
        splits_null_results = db.fetch_one(splits_null_check_query)
        logger.info(f"发现缺少running_quantity或running_cost的分单记录数: {splits_null_results['count_null']}")

        # 更新分单记录
        splits_update_query = """
        UPDATE transaction_splits 
        SET running_quantity = current_quantity, 
            running_cost = current_cost
        WHERE running_quantity IS NULL OR running_cost IS NULL
        """
        db.execute(splits_update_query)
        logger.info("已更新分单记录")

        # 检查has_splits字段与实际分单记录是否一致
        splits_check_query = """
        SELECT 
            COUNT(*) as total_count,
            SUM(CASE WHEN (has_splits = 1 AND split_count > 0) OR (has_splits = 0 AND split_count = 0) THEN 1 ELSE 0 END) as correct_count
        FROM (
            SELECT 
                t.id, 
                t.has_splits,
                COUNT(ts.id) as split_count
            FROM stock_transactions t
            LEFT JOIN transaction_splits ts ON t.id = ts.original_transaction_id
            GROUP BY t.id
        ) as subquery
        """
        splits_results = db.fetch_one(splits_check_query)
        logger.info(f"has_splits字段与实际分单记录一致的比例: {splits_results['correct_count']}/{splits_results['total_count']}")

        # 修复has_splits字段
        fix_has_splits_query = """
        UPDATE stock_transactions t
        LEFT JOIN (
            SELECT 
                original_transaction_id,
                COUNT(*) as split_count
            FROM transaction_splits
            GROUP BY original_transaction_id
        ) ts ON t.id = ts.original_transaction_id
        SET t.has_splits = CASE WHEN ts.split_count > 0 THEN 1 ELSE 0 END
        WHERE (ts.split_count > 0 AND t.has_splits = 0) OR (ts.split_count IS NULL AND t.has_splits = 1)
        """
        db.execute(fix_has_splits_query)
        logger.info("已修复has_splits字段")

        # 再次检查has_splits字段与实际分单记录是否一致
        splits_results = db.fetch_one(splits_check_query)
        logger.info(f"修复后has_splits字段与实际分单记录一致的比例: {splits_results['correct_count']}/{splits_results['total_count']}")

        return True
    except Exception as e:
        logger.error(f"修复交易记录字段失败: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("开始修复交易记录字段")
    success = fix_transaction_fields()
    if success:
        logger.info("修复交易记录字段成功")
    else:
        logger.error("修复交易记录字段失败") 