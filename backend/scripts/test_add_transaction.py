#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试添加交易记录的功能
"""

import sys
import os
import logging
import json
from datetime import datetime
import random

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import db
from services.transaction_calculator import TransactionCalculator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_transaction_code(prefix='P'):
    """生成交易编号"""
    return f"{prefix}-{random.randint(100000, 999999)}"

def test_add_transaction():
    """测试添加交易记录"""
    # 准备测试数据
    transaction_data = {
        'transaction_date': datetime.now().strftime('%Y-%m-%d'),
        'stock_code': '01347',
        'market': 'HK',
        'transaction_type': 'buy',
        'transaction_code': generate_transaction_code(),
        'total_quantity': 1000,
        'total_amount': 41000,
        'broker_fee': 100,
        'stamp_duty': 41,
        'transaction_levy': 0.58,
        'trading_fee': 1.16,
        'deposit_fee': 30,
        'split_ratio': 1.0,
        'remarks': '系统自动创建的100%分单',
        'details': [
            {
                'quantity': 1000,
                'price': 41
            }
        ]
    }
    
    holder_id = 3  # 假设用户ID为3
    
    logger.info(f"测试数据: {json.dumps(transaction_data, indent=2)}")
    
    try:
        # 调用处理交易的方法
        success, result = TransactionCalculator.process_transaction(
            db_conn=db,
            transaction_data=transaction_data,
            operation_type='add',
            holder_id=holder_id
        )
        
        logger.info(f"处理结果: success={success}, result={result}")
        
        if success:
            # 验证交易记录是否成功插入
            transaction_id = result.get('id')
            if transaction_id is not None:
                # 查询交易记录
                query = "SELECT * FROM stock_transactions WHERE id = %s"
                transaction = db.fetch_one(query, [transaction_id])
                
                if transaction:
                    logger.info(f"交易记录已成功插入: {transaction}")
                    
                    # 查询交易明细
                    detail_query = "SELECT * FROM stock_transaction_details WHERE transaction_id = %s"
                    details = db.fetch_all(detail_query, [transaction_id])
                    
                    if details:
                        logger.info(f"交易明细已成功插入: {details}")
                    else:
                        logger.error("交易明细未成功插入")
                else:
                    logger.error(f"交易记录未成功插入，ID={transaction_id}")
            else:
                logger.error("未获取到交易记录ID")
        else:
            logger.error(f"处理交易失败: {result.get('message')}")
            
        return success, result
    except Exception as e:
        logger.error(f"测试添加交易记录失败: {str(e)}", exc_info=True)
        return False, {'message': f'测试添加交易记录失败: {str(e)}'}

if __name__ == "__main__":
    logger.info("开始测试添加交易记录")
    success, result = test_add_transaction()
    
    if success:
        logger.info("测试成功")
        sys.exit(0)
    else:
        logger.error(f"测试失败: {result.get('message')}")
        sys.exit(1) 