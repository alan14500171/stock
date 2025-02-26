#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import logging
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db
import logging

logger = logging.getLogger(__name__)

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def get_all_transactions():
    """获取所有交易记录"""
    sql = """
        SELECT id, current_quantity, current_cost
        FROM stock.stock_transactions
        ORDER BY id
    """
    return db.fetch_all(sql)

def update_running_fields():
    """更新所有交易记录的running_quantity和running_cost字段"""
    try:
        # 获取所有交易记录
        transactions = get_all_transactions()
        
        if not transactions:
            logger.info("没有找到交易记录")
            return True
        
        logger.info(f"共找到 {len(transactions)} 条交易记录需要更新")
        
        # 开始事务
        db.execute("START TRANSACTION")
        
        try:
            success = 0
            failed = 0
            
            for trans in transactions:
                try:
                    # 更新running_quantity和running_cost字段
                    update_sql = """
                        UPDATE stock.stock_transactions
                        SET running_quantity = %s,
                            running_cost = %s,
                            updated_at = NOW()
                        WHERE id = %s
                    """
                    
                    result = db.execute(update_sql, [
                        trans['current_quantity'],
                        trans['current_cost'],
                        trans['id']
                    ])
                    
                    if result:
                        success += 1
                    else:
                        failed += 1
                        logger.error(f"更新交易记录ID={trans['id']}失败")
                        
                except Exception as e:
                    failed += 1
                    logger.error(f"更新交易记录ID={trans['id']}时发生错误: {str(e)}")
            
            # 提交事务
            db.execute("COMMIT")
            logger.info(f"更新完成: 成功 {success} 条, 失败 {failed} 条")
            return True
            
        except Exception as e:
            db.execute("ROLLBACK")
            logger.error(f"更新交易记录失败: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"获取交易记录失败: {str(e)}")
        return False

def main():
    """主函数"""
    setup_logging()
    logger.info("开始更新交易记录的running_quantity和running_cost字段...")
    
    if update_running_fields():
        logger.info("更新成功")
    else:
        logger.error("更新失败")

if __name__ == '__main__':
    main() 