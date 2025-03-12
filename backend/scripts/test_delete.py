#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试删除交易记录功能
"""

import sys
import os
import logging
import pymysql
from pymysql.cursors import DictCursor

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.db import get_db_connection
from services.transaction_calculator import TransactionCalculator
from config.db_config import get_db_config

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_delete_transaction(transaction_id):
    """测试删除交易记录"""
    try:
        # 获取数据库连接
        config = get_db_config()
        conn = pymysql.connect(
            **config,
            cursorclass=DictCursor,
            autocommit=False
        )
        
        # 获取交易记录
        with conn.cursor() as cursor:
            sql = "SELECT * FROM stock_transactions WHERE id = %s"
            cursor.execute(sql, [transaction_id])
            transaction = cursor.fetchone()
        
        if not transaction:
            logger.error(f"交易记录不存在: ID={transaction_id}")
            return False
        
        logger.info(f"获取到交易记录: {transaction}")
        
        try:
            # 开始事务
            conn.begin()
            
            # 1. 先删除交易分单记录
            with conn.cursor() as cursor:
                split_sql = "DELETE FROM transaction_splits WHERE original_transaction_id = %s"
                cursor.execute(split_sql, [transaction_id])
                split_rows = cursor.rowcount
                logger.info(f"删除分单记录: 影响行数={split_rows}")
            
            # 2. 删除交易明细记录
            with conn.cursor() as cursor:
                detail_sql = "DELETE FROM stock_transaction_details WHERE transaction_id = %s"
                cursor.execute(detail_sql, [transaction_id])
                detail_rows = cursor.rowcount
                logger.info(f"删除交易明细记录: 影响行数={detail_rows}")
            
            # 3. 删除交易记录
            with conn.cursor() as cursor:
                delete_sql = "DELETE FROM stock_transactions WHERE id = %s"
                cursor.execute(delete_sql, [transaction_id])
                affected_rows = cursor.rowcount
                
                if affected_rows == 0:
                    logger.error(f"删除交易记录失败: 影响行数为0")
                    conn.rollback()
                    return False
                
                logger.info(f"删除交易记录成功: 影响行数={affected_rows}")
            
            # 提交事务
            conn.commit()
            return True
            
        except Exception as e:
            # 回滚事务
            conn.rollback()
            raise e
            
    except Exception as e:
        logger.error(f"测试删除交易记录失败: {str(e)}")
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python test_delete.py <transaction_id>")
        sys.exit(1)
    
    transaction_id = int(sys.argv[1])
    success = test_delete_transaction(transaction_id)
    
    if success:
        print(f"成功删除交易记录: ID={transaction_id}")
        sys.exit(0)
    else:
        print(f"删除交易记录失败: ID={transaction_id}")
        sys.exit(1) 