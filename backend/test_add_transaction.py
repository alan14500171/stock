#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试添加交易记录
"""

import logging
from config.database import db
from datetime import datetime
import json
from services.transaction_calculator import TransactionCalculator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_add_transaction():
    """测试添加交易记录"""
    try:
        # 获取用户ID
        user_query = "SELECT id FROM users LIMIT 1"
        user_result = db.fetch_one(user_query)
        if not user_result:
            logger.error("未找到用户记录")
            return False
        
        user_id = user_result['id']
        logger.info(f"使用用户ID: {user_id}")
        
        # 获取持有人ID
        holder_query = "SELECT id FROM holders WHERE user_id = %s LIMIT 1"
        holder_result = db.fetch_one(holder_query, [user_id])
        if not holder_result:
            # 尝试获取任意持有人
            holder_query = "SELECT id FROM holders LIMIT 1"
            holder_result = db.fetch_one(holder_query)
            if not holder_result:
                logger.error("未找到持有人记录")
                return False
        
        holder_id = holder_result['id']
        logger.info(f"使用持有人ID: {holder_id}")
        
        # 构建交易数据
        transaction_data = {
            'user_id': user_id,  # 使用用户ID而不是持有人ID
            'transaction_date': '2025-03-13',
            'stock_code': '01347',
            'market': 'HK',
            'transaction_type': 'buy',
            'total_quantity': 1000,
            'total_amount': 42000,
            'broker_fee': 100,
            'stamp_duty': 50,
            'transaction_levy': 30,
            'trading_fee': 20,
            'deposit_fee': 10,
            'transaction_code': f'TEST-{datetime.now().strftime("%Y%m%d%H%M%S")}'
        }
        
        # 调用交易计算器添加交易
        success, result = TransactionCalculator.process_transaction(
            db,
            transaction_data,
            'add',
            holder_id
        )
        
        if not success:
            logger.error(f"添加交易记录失败: {result.get('message', '')}")
            return False
        
        transaction_id = result.get('id')
        logger.info(f"添加交易记录成功，ID: {transaction_id}")
        
        # 查询新添加的交易记录
        query = """
        SELECT id, stock_code, market, transaction_type, total_quantity, total_amount,
               total_fees, net_amount, running_quantity, running_cost, has_splits
        FROM stock_transactions
        WHERE id = %s
        """
        transaction = db.fetch_one(query, [transaction_id])
        
        if not transaction:
            logger.error(f"未找到新添加的交易记录: ID={transaction_id}")
            return False
        
        # 打印交易记录详情
        logger.info(f"新添加的交易记录详情: {json.dumps(transaction, indent=2, default=str)}")
        
        # 检查字段是否正确设置
        total_fees = transaction.get('total_fees')
        net_amount = transaction.get('net_amount')
        has_splits = transaction.get('has_splits')
        running_quantity = transaction.get('running_quantity')
        running_cost = transaction.get('running_cost')
        
        logger.info(f"total_fees: {total_fees}")
        logger.info(f"net_amount: {net_amount}")
        logger.info(f"has_splits: {has_splits}")
        logger.info(f"running_quantity: {running_quantity}")
        logger.info(f"running_cost: {running_cost}")
        
        # 检查分单记录
        split_query = """
        SELECT id, original_transaction_id, holder_id, total_quantity, total_amount,
               total_fees, net_amount, running_quantity, running_cost
        FROM transaction_splits
        WHERE original_transaction_id = %s
        """
        split = db.fetch_one(split_query, [transaction_id])
        
        if split:
            logger.info(f"分单记录详情: {json.dumps(split, indent=2, default=str)}")
            logger.info(f"分单记录 total_fees: {split.get('total_fees')}")
            logger.info(f"分单记录 net_amount: {split.get('net_amount')}")
            logger.info(f"分单记录 running_quantity: {split.get('running_quantity')}")
            logger.info(f"分单记录 running_cost: {split.get('running_cost')}")
        else:
            logger.warning(f"未找到分单记录: original_transaction_id={transaction_id}")
        
        return True
    except Exception as e:
        logger.error(f"测试添加交易记录失败: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("开始测试添加交易记录")
    success = test_add_transaction()
    if success:
        logger.info("测试添加交易记录成功")
    else:
        logger.error("测试添加交易记录失败") 