#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pymysql
import logging
from decimal import Decimal
import argparse
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("transaction_recalculate.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("transaction_recalculator")

class TransactionRecalculator:
    def __init__(self, host, port, user, password, database):
        self.db_config = {
            'host': host,
            'port': int(port),
            'user': user, 
            'password': password,
            'database': database,
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }
        self.conn = None
        self.cursor = None
        
    def connect(self):
        try:
            self.conn = pymysql.connect(**self.db_config)
            self.cursor = self.conn.cursor()
            logger.info("数据库连接成功")
        except Exception as e:
            logger.error(f"数据库连接失败: {str(e)}")
            raise
    
    def disconnect(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("数据库连接已关闭")
    
    def get_all_holder_stock_pairs(self):
        """获取所有持有人-股票对"""
        sql = """
        SELECT DISTINCT 
            holder_id, 
            market COLLATE utf8mb4_unicode_ci AS market, 
            stock_code COLLATE utf8mb4_unicode_ci AS stock_code 
        FROM transaction_splits
        """
        self.cursor.execute(sql)
        return self.cursor.fetchall()
    
    def get_transactions_for_stock(self, holder_id, market, stock_code):
        """获取指定持有人和股票的所有交易记录，按交易日期排序"""
        sql = """
        SELECT 
            ts.id,
            ts.original_transaction_id,
            ts.transaction_date,
            ts.transaction_type,
            ts.total_quantity,
            ts.total_amount,
            ts.broker_fee,
            ts.transaction_levy,
            ts.stamp_duty,
            ts.trading_fee,
            ts.deposit_fee,
            ts.holder_id,
            ts.holder_name,
            ts.market,
            ts.stock_code,
            ts.stock_name,
            ts.split_ratio
        FROM transaction_splits ts
        WHERE ts.holder_id = %s 
          AND ts.market COLLATE utf8mb4_unicode_ci = %s COLLATE utf8mb4_unicode_ci
          AND ts.stock_code COLLATE utf8mb4_unicode_ci = %s COLLATE utf8mb4_unicode_ci
        ORDER BY ts.transaction_date ASC, ts.id ASC
        """
        self.cursor.execute(sql, (holder_id, market, stock_code))
        return self.cursor.fetchall()
    
    def update_transaction_split(self, transaction_id, update_data):
        """更新交易分单记录"""
        fields = []
        values = []
        
        for field, value in update_data.items():
            fields.append(f"{field} = %s")
            values.append(value)
        
        values.append(transaction_id)  # WHERE条件的参数
        
        sql = f"""
        UPDATE transaction_splits SET 
            {', '.join(fields)},
            updated_at = NOW()
        WHERE id = %s
        """
        
        try:
            self.cursor.execute(sql, values)
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            logger.error(f"更新交易ID {transaction_id} 失败: {str(e)}")
            return False
    
    def recalculate_all(self):
        """重新计算所有交易记录"""
        try:
            # 获取所有持有人-股票对
            holder_stock_pairs = self.get_all_holder_stock_pairs()
            total_pairs = len(holder_stock_pairs)
            logger.info(f"总共找到 {total_pairs} 个持有人-股票对")
            
            updated_count = 0
            failed_count = 0
            
            # 处理每个持有人-股票对
            for i, pair in enumerate(holder_stock_pairs, 1):
                holder_id = pair['holder_id']
                market = pair['market']
                stock_code = pair['stock_code']
                
                logger.info(f"处理 ({i}/{total_pairs}) - 持有人ID: {holder_id}, 市场: {market}, 股票: {stock_code}")
                
                # 获取该持有人-股票对的所有交易
                transactions = self.get_transactions_for_stock(holder_id, market, stock_code)
                if not transactions:
                    logger.warning(f"未找到交易记录: 持有人ID: {holder_id}, 市场: {market}, 股票: {stock_code}")
                    continue
                
                logger.info(f"找到 {len(transactions)} 条交易记录")
                
                # 跟踪变量
                running_quantity = 0
                running_cost = Decimal('0.00')
                running_avg_cost = Decimal('0.00')
                
                # 按时间顺序处理每笔交易
                for tx in transactions:
                    tx_id = tx['id']
                    tx_type = tx['transaction_type'].upper()
                    quantity = Decimal(str(tx['total_quantity']))
                    amount = Decimal(str(tx['total_amount']))
                    
                    # 计算总费用
                    fees = sum(Decimal(str(tx.get(fee, 0) or 0)) for fee in 
                              ['broker_fee', 'transaction_levy', 'stamp_duty', 'trading_fee', 'deposit_fee'])
                    
                    # 交易前数据
                    prev_quantity = running_quantity
                    prev_cost = running_cost
                    prev_avg_cost = running_avg_cost if running_quantity > 0 else Decimal('0.00')
                    
                    # 更新持仓数据
                    if tx_type == 'BUY':
                        # 买入交易
                        current_quantity = prev_quantity + quantity
                        current_cost = prev_cost + amount
                        
                        # 计算新的平均成本
                        if current_quantity > 0:
                            current_avg_cost = current_cost / current_quantity
                        else:
                            current_avg_cost = Decimal('0.00')
                        
                        realized_profit = Decimal('0.00')
                        profit_rate = Decimal('0.00')
                        
                    elif tx_type == 'SELL':
                        # 卖出交易
                        current_quantity = prev_quantity - quantity
                        
                        # 计算已实现盈亏
                        sell_value = amount
                        cost_basis = quantity * prev_avg_cost if prev_quantity > 0 else Decimal('0.00')
                        realized_profit = sell_value - cost_basis - fees
                        
                        if current_quantity >= 0:
                            # 仍有剩余持仓
                            current_cost = prev_cost * (current_quantity / prev_quantity) if prev_quantity > 0 else Decimal('0.00')
                            current_avg_cost = prev_avg_cost  # 卖出不改变平均成本
                        else:
                            # 卖空情况（不应该发生，但为安全起见处理）
                            current_cost = Decimal('0.00')
                            current_avg_cost = Decimal('0.00')
                        
                        # 计算盈亏率
                        if cost_basis > 0:
                            profit_rate = (realized_profit / cost_basis) * 100
                        else:
                            profit_rate = Decimal('0.00')
                    else:
                        # 未知交易类型，保持不变
                        logger.warning(f"未知交易类型 {tx_type}，跳过ID: {tx_id}")
                        continue
                    
                    # 更新运行中的变量
                    running_quantity = current_quantity
                    running_cost = current_cost
                    running_avg_cost = current_avg_cost
                    
                    # 准备更新数据
                    update_data = {
                        'prev_quantity': int(prev_quantity),
                        'prev_cost': float(prev_cost),
                        'prev_avg_cost': float(prev_avg_cost),
                        'current_quantity': int(current_quantity),
                        'current_cost': float(current_cost),
                        'current_avg_cost': float(current_avg_cost),
                        'total_fees': float(fees),
                        'running_quantity': int(running_quantity),
                        'running_cost': float(running_cost),
                        'realized_profit': float(realized_profit),
                        'profit_rate': float(profit_rate)
                    }
                    
                    # 更新数据库
                    if self.update_transaction_split(tx_id, update_data):
                        updated_count += 1
                    else:
                        failed_count += 1
            
            logger.info(f"更新完成: {updated_count} 条记录更新成功, {failed_count} 条记录更新失败")
            return updated_count, failed_count
            
        except Exception as e:
            logger.error(f"重新计算过程中发生错误: {str(e)}", exc_info=True)
            return 0, 0

def main():
    parser = argparse.ArgumentParser(description='交易分单数据重新计算工具')
    parser.add_argument('--host', default='localhost', help='数据库主机')
    parser.add_argument('--port', default=3306, help='数据库端口')
    parser.add_argument('--user', required=True, help='数据库用户名')
    parser.add_argument('--password', required=True, help='数据库密码')
    parser.add_argument('--database', default='stock', help='数据库名称')
    
    args = parser.parse_args()
    
    logger.info("开始重新计算交易分单数据...")
    
    recalculator = TransactionRecalculator(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database
    )
    
    try:
        recalculator.connect()
        updated, failed = recalculator.recalculate_all()
        logger.info(f"处理完成: {updated} 条记录更新成功, {failed} 条记录更新失败")
    except Exception as e:
        logger.error(f"处理过程中发生错误: {str(e)}", exc_info=True)
    finally:
        recalculator.disconnect()

if __name__ == "__main__":
    main()