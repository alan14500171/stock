from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import logging
from typing import Dict, List, Tuple, Optional, Any
from utils.db import get_db_connection
import pymysql

logger = logging.getLogger(__name__)

class TransactionCalculator:
    @staticmethod
    def calculate_fees(transaction):
        """计算交易的总费用"""
        fees = [
            'broker_fee', 'transaction_levy', 'stamp_duty',
            'trading_fee', 'deposit_fee'
        ]
        return sum(Decimal(str(transaction.get(fee) or 0)) for fee in fees)

    @staticmethod
    def calculate_net_amount(transaction, total_fees):
        """计算交易的净金额"""
        total_amount = Decimal(str(transaction['total_amount']))
        if transaction['transaction_type'].lower() == 'buy':
            return total_amount + total_fees
        else:
            return total_amount - total_fees

    @staticmethod
    def calculate_position_change(transaction, prev_state, is_split=False, skip_validation=False):
        """
        计算持仓变化
        
        Args:
            transaction: 交易数据
            prev_state: 之前的状态
            is_split: 是否为分单操作
            skip_validation: 是否跳过验证（添加交易记录时设为True）
            
        Returns:
            Dict: 计算结果
        """
        total_quantity = Decimal(str(transaction['total_quantity']))
        total_amount = Decimal(str(transaction['total_amount']))
        total_fees = TransactionCalculator.calculate_fees(transaction)
        
        # 获取之前的状态
        prev_quantity = Decimal(str(prev_state.get('quantity', 0)))
        prev_cost = Decimal(str(prev_state.get('cost', 0)))
        prev_avg_cost = Decimal(str(prev_state.get('avg_cost', 0)))
        
        # 初始化结果
        result = {
            'prev_quantity': prev_quantity,
            'prev_cost': prev_cost,
            'prev_avg_cost': prev_avg_cost,
            'realized_profit': Decimal('0'),
            'profit_rate': Decimal('0'),
            'total_fees': total_fees,
            'net_amount': Decimal('0'),
            'avg_price': Decimal('0')
        }
        
        # 计算净金额
        result['net_amount'] = TransactionCalculator.calculate_net_amount(transaction, total_fees)
        
        # 计算平均价格（单价）
        if total_quantity > 0:
            result['avg_price'] = total_amount / total_quantity
        
        # 根据交易类型计算
        if transaction['transaction_type'].lower() == 'buy':
            # 买入
            result['current_quantity'] = prev_quantity + total_quantity
            result['current_cost'] = prev_cost + total_amount + total_fees
            result['current_avg_cost'] = (result['current_cost'] / result['current_quantity']
                                        if result['current_quantity'] > 0 else Decimal('0'))
        else:
            # 卖出
            # 在添加交易记录时跳过验证，在分单操作时进行验证
            if prev_quantity < total_quantity and not skip_validation and not is_split:
                raise ValueError(f'卖出数量({total_quantity})大于持仓数量({prev_quantity})')
            
            result['current_quantity'] = prev_quantity - total_quantity
            
            # 计算已实现盈亏
            if prev_avg_cost > 0:
                cost_basis = prev_avg_cost * total_quantity
                result['realized_profit'] = total_amount - cost_basis - total_fees
                result['profit_rate'] = (result['realized_profit'] / cost_basis * 100
                                              if cost_basis > 0 else Decimal('0'))
            
            # 更新成本
            result['current_cost'] = (prev_cost * (result['current_quantity'] / prev_quantity)
                                    if prev_quantity > 0 else Decimal('0'))
            result['current_avg_cost'] = (result['current_cost'] / result['current_quantity']
                                        if result['current_quantity'] > 0 else Decimal('0'))
        
        # 格式化数值
        for key in result:
            if isinstance(result[key], Decimal):
                result[key] = result[key].quantize(Decimal('0.00000'), rounding=ROUND_HALF_UP)
        
        return result

    @staticmethod
    def process_transaction(
        db_conn,
        transaction_data: Dict[str, Any],
        operation_type: str,
        holder_id: Optional[int] = None,
        original_transaction_id: Optional[int] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        统一处理交易记录的计算逻辑
        
        Args:
            db_conn: 数据库连接或Database对象
            transaction_data: 交易数据
            operation_type: 操作类型 ('add', 'edit', 'delete', 'split')
            holder_id: 持有人ID（分单时使用）
            original_transaction_id: 原始交易ID（分单和编辑时使用）
            
        Returns:
            Tuple[bool, Dict]: (是否成功, 结果数据)
        """
        try:
            # 记录详细的交易数据和操作类型，用于调试
            logger.info(f"处理交易记录: operation_type={operation_type}, holder_id={holder_id}, data={transaction_data}")
            
            # 确保holder_id不为None
            if holder_id is None:
                logger.error("处理交易记录失败: holder_id不能为空")
                return False, {'message': '处理交易记录失败: holder_id不能为空'}
            
            # 确保transaction_data中包含user_id，如果没有则使用holder_id
            if 'user_id' not in transaction_data or not transaction_data['user_id']:
                transaction_data['user_id'] = holder_id
                logger.info(f"transaction_data中未找到user_id，使用holder_id: {holder_id}")
            
            # 验证交易数据（除删除操作外）
            if operation_type != 'delete':
                logger.info(f"开始验证交易数据: {transaction_data}")
                errors = TransactionCalculator.validate_transaction(transaction_data)
                if errors:
                    logger.error(f"数据验证失败: {errors}")
                    return False, {'message': '数据验证失败', 'errors': errors}
                logger.info(f"交易数据验证通过")

            # 计算持仓变化
            if operation_type == 'add':
                # 获取之前的持仓状态
                prev_state = TransactionCalculator._get_previous_holding_state(
                    db_conn,
                    transaction_data['user_id'],  # 使用user_id而不是holder_id
                    transaction_data['stock_code'],
                    transaction_data['market'],
                    transaction_data['transaction_date']
                )
                
                logger.info(f"获取到之前的持仓状态: {prev_state}")
                
                # 计算持仓变化 - 添加交易记录时跳过验证
                position_change = TransactionCalculator.calculate_position_change(
                    transaction_data, prev_state, skip_validation=True
                )
                
                logger.info(f"计算的持仓变化: {position_change}")
                
                # 添加交易
                success, result = TransactionCalculator._handle_add(db_conn, transaction_data, position_change, holder_id)
            elif operation_type == 'edit':
                # 获取之前的持仓状态
                prev_state = TransactionCalculator._get_previous_holding_state(
                    db_conn,
                    holder_id,
                    transaction_data['stock_code'],
                    transaction_data['market'],
                    transaction_data['transaction_date'],
                    original_transaction_id
                )
                
                # 计算持仓变化 - 编辑交易记录时跳过验证
                position_change = TransactionCalculator.calculate_position_change(
                    transaction_data, prev_state, skip_validation=True
                )
                
                # 编辑交易
                success, result = TransactionCalculator._handle_edit(db_conn, transaction_data, position_change, original_transaction_id)
            elif operation_type == 'delete':
                # 获取之前的持仓状态
                prev_state = TransactionCalculator._get_previous_holding_state(
                    db_conn,
                    holder_id,
                    transaction_data['stock_code'],
                    transaction_data['market'],
                    transaction_data['transaction_date']
                )
                
                # 删除交易
                success, result = TransactionCalculator._handle_delete(db_conn, transaction_data, prev_state, holder_id)
            elif operation_type == 'split':
                # 获取之前的持仓状态
                prev_state = TransactionCalculator._get_previous_holding_state(
                    db_conn,
                    holder_id,
                    transaction_data['stock_code'],
                    transaction_data['market'],
                    transaction_data['transaction_date'],
                    is_split=True
                )
                
                # 计算持仓变化 - 分单操作时不跳过验证
                position_change = TransactionCalculator.calculate_position_change(
                    transaction_data, prev_state, is_split=True, skip_validation=False
                )
                
                # 分单交易
                success, result = TransactionCalculator._handle_split(db_conn, transaction_data, position_change, holder_id, original_transaction_id)
            else:
                logger.error(f"未知的操作类型: {operation_type}")
                return False, {'message': f'未知的操作类型: {operation_type}'}
                
            return success, result
            
        except Exception as e:
            logger.error(f"处理交易记录失败: {str(e)}", exc_info=True)
            return False, {'message': f'处理交易记录失败: {str(e)}'}

    @staticmethod
    def _get_previous_holding_state(
        db_conn,
        user_or_holder_id: int,
        stock_code: str,
        market: str,
        transaction_date: str,
        transaction_id: Optional[int] = None,
        is_split: bool = False
    ) -> Dict[str, Any]:
        """获取之前的持仓状态，使用数据库中已有的字段提高效率"""
        table = "transaction_splits" if is_split else "stock_transactions"
        id_field = "holder_id" if is_split else "user_id"
        
        # 检查表中是否有current_quantity字段
        if is_split:
            sql = f"""
                SELECT current_quantity as quantity,
                       current_cost as cost,
                       current_avg_cost as avg_cost
                FROM {table}
                WHERE {id_field} = %s
                    AND stock_code = %s
                    AND market = %s
                    AND (transaction_date < %s
                         OR (transaction_date = %s AND id < %s))
                ORDER BY transaction_date DESC, id DESC
                LIMIT 1
            """
        else:
            # stock_transactions表中没有这些字段，使用计算值
            sql = f"""
                SELECT 0 as quantity,
                       0 as cost,
                       0 as avg_cost
                FROM {table}
                WHERE {id_field} = %s
                    AND stock_code = %s
                    AND market = %s
                    AND (transaction_date < %s
                         OR (transaction_date = %s AND id < %s))
                ORDER BY transaction_date DESC, id DESC
                LIMIT 1
            """
        
        params = [
            user_or_holder_id, stock_code, market,
            transaction_date, transaction_date,
            transaction_id or 0
        ]
        
        # 使用db_conn.fetch_one获取最近一条记录
        result = db_conn.fetch_one(sql, params)
        
        if result:
            holding_state = {
                'quantity': Decimal(str(result['quantity'])),
                'cost': Decimal(str(result['cost'])),
                'avg_cost': Decimal(str(result['avg_cost']))
            }
            logger.info(f"获取持仓状态: 用户/持有人ID={user_or_holder_id}, 股票={stock_code}, 市场={market}, 日期={transaction_date}, 持仓量={holding_state['quantity']}, 成本={holding_state['cost']}, 平均成本={holding_state['avg_cost']}")
            return holding_state
            
        # 如果没有记录，返回初始状态
        return {
            'quantity': Decimal('0'),
            'cost': Decimal('0'),
            'avg_cost': Decimal('0')
        }

    @staticmethod
    def _handle_add(
        db_conn,
        transaction_data: Dict[str, Any],
        position_change: Dict[str, Any],
        holder_id: Optional[int] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """处理新增交易"""
        try:
            # 获取用户ID
            user_id = transaction_data.get('user_id')
            if not user_id:
                logger.error("缺少用户ID")
                return False, {"message": "缺少用户ID"}
            
            # 获取交易类型
            transaction_type = transaction_data.get('transaction_type', '').lower()
            if not transaction_type or transaction_type not in ['buy', 'sell']:
                logger.error(f"无效的交易类型: {transaction_type}")
                return False, {"message": f"无效的交易类型: {transaction_type}"}
            
            # 获取交易日期
            transaction_date = transaction_data.get('transaction_date')
            if not transaction_date:
                logger.error("缺少交易日期")
                return False, {"message": "缺少交易日期"}
            
            # 获取股票代码和市场
            stock_code = transaction_data.get('stock_code')
            market = transaction_data.get('market')
            if not stock_code or not market:
                logger.error("缺少股票代码或市场")
                return False, {"message": "缺少股票代码或市场"}
            
            # 获取交易数量和金额
            total_quantity = float(transaction_data.get('total_quantity', 0) or 0)
            total_amount = float(transaction_data.get('total_amount', 0) or 0)
            if total_quantity <= 0:
                logger.error(f"无效的交易数量: {total_quantity}")
                return False, {"message": f"无效的交易数量: {total_quantity}"}
            
            # 检查是否已存在相同的交易记录
            check_duplicate_sql = """
                SELECT id FROM stock_transactions
                WHERE transaction_code = %s
                LIMIT 1
            """
            
            check_params = [
                transaction_data.get('transaction_code', '')
            ]
            
            # 只有当交易编号不为空时才检查重复
            if transaction_data.get('transaction_code', ''):
                existing_transaction = db_conn.fetch_one(check_duplicate_sql, check_params)
                if existing_transaction:
                    logger.warning(f"已存在相同的交易编号: ID={existing_transaction['id']}, 交易编号={transaction_data.get('transaction_code', '')}")
                    return False, {"message": f"已存在相同的交易编号，请勿重复添加", "id": existing_transaction['id']}
            
            # 计算交易费用
            broker_fee = float(transaction_data.get('broker_fee', 0) or 0)
            stamp_duty = float(transaction_data.get('stamp_duty', 0) or 0)
            transaction_levy = float(transaction_data.get('transaction_levy', 0) or 0)
            trading_fee = float(transaction_data.get('trading_fee', 0) or 0)
            deposit_fee = float(transaction_data.get('deposit_fee', 0) or 0)
            
            total_fees = broker_fee + stamp_duty + transaction_levy + trading_fee + deposit_fee
            
            # 计算净金额
            if transaction_type == 'buy':
                net_amount = total_amount + total_fees
            else:  # sell
                net_amount = total_amount - total_fees
            
            # 获取当前时间
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 设置running_quantity和running_cost为current_quantity和current_cost
            running_quantity = position_change.get('current_quantity', 0)
            running_cost = position_change.get('current_cost', 0)
            
            # 计算平均价格
            avg_price = 0
            if total_quantity > 0:
                avg_price = abs(total_amount) / total_quantity
            
            # 构建插入SQL
            insert_sql = """
                INSERT INTO stock_transactions (
                    user_id, transaction_date, stock_code, market,
                    transaction_type, transaction_code, total_quantity,
                    total_amount, broker_fee, transaction_levy,
                    stamp_duty, trading_fee, deposit_fee,
                    total_fees, net_amount,
                    created_at, updated_at, has_splits, avg_price
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            # 准备参数
            params = [
                user_id,
                transaction_date,
                stock_code,
                market,
                transaction_type,
                transaction_data.get('transaction_code', ''),
                total_quantity,
                total_amount,
                broker_fee,
                transaction_levy,
                stamp_duty,
                trading_fee,
                deposit_fee,
                float(position_change.get('total_fees', 0)),
                float(position_change.get('net_amount', 0)),
                current_time,
                current_time,
                0,  # has_splits初始为0
                float(position_change.get('avg_price', 0))
            ]
            
            # 执行插入
            transaction_id = db_conn.insert(insert_sql, params)
            
            if not transaction_id:
                logger.error("插入交易记录失败")
                return False, {"message": "插入交易记录失败"}
            
            logger.info(f"插入交易记录成功，ID: {transaction_id}")
            
            # 处理交易明细
            if 'details' in transaction_data and transaction_data['details']:
                for detail in transaction_data['details']:
                    detail_sql = """
                        INSERT INTO stock_transaction_details
                        (transaction_id, quantity, price, created_at)
                        VALUES (%s, %s, %s, %s)
                    """
                    detail_params = [
                        transaction_id,
                        float(detail.get('quantity', 0)),
                        float(detail.get('price', 0)),
                        current_time
                    ]
                    db_conn.execute(detail_sql, detail_params)
                
                logger.info(f"插入交易明细成功，交易ID: {transaction_id}")
            
            # 重新计算后续交易记录
            logger.info(f"开始重新计算后续交易记录: 股票代码={stock_code}, 市场={market}, 日期={transaction_data['transaction_date']}")
            TransactionCalculator.recalculate_subsequent_transactions(
                db_conn,
                stock_code,
                market,
                transaction_data['transaction_date']
            )
            
            # 如果有持有人ID，也重新计算持有人的后续交易记录
            if holder_id:
                logger.info(f"开始重新计算持有人后续交易记录: 持有人ID={holder_id}, 股票代码={stock_code}, 市场={market}, 日期={transaction_data['transaction_date']}")
                TransactionCalculator.recalculate_subsequent_transactions(
                    db_conn,
                    stock_code,
                    market,
                    transaction_data['transaction_date'],
                    holder_id
                )
            
            # 自动创建分单记录
            try:
                # 检查是否有持有人
                if holder_id:
                    # 获取持有人信息
                    holder_query = "SELECT id, name FROM holders WHERE id = %s"
                    holder = db_conn.fetch_one(holder_query, [holder_id])
                    
                    if holder:
                        # 获取股票名称
                        stock_name = ""
                        stock_name_query = "SELECT code_name FROM stocks WHERE code = %s AND market = %s"
                        stock_result = db_conn.fetch_one(stock_name_query, [stock_code, market])
                        
                        if stock_result:
                            stock_name = stock_result['code_name']
                        else:
                            stock_name = stock_code
                        
                        # 获取股票ID
                        stock_id = None
                        try:
                            stock_id_sql = """
                                SELECT id FROM stocks 
                                WHERE code = %s AND market = %s
                                LIMIT 1
                            """
                            stock_id_result = db_conn.fetch_one(stock_id_sql, [stock_code, market])
                            if stock_id_result:
                                stock_id = stock_id_result['id']
                                logger.info(f"获取到股票ID: {stock_id}")
                            else:
                                logger.warning(f"未找到股票ID，股票代码: {stock_code}, 市场: {market}")
                        except Exception as e:
                            logger.error(f"获取股票ID失败: {str(e)}")
                        
                        # 计算running_quantity和running_cost
                        running_quantity = position_change.get('current_quantity', 0)
                        running_cost = position_change.get('current_cost', 0)
                        
                        # 构建分单记录SQL
                        split_sql = """
                            INSERT INTO transaction_splits (
                                original_transaction_id, holder_id, holder_name, split_ratio,
                                transaction_date, stock_id, stock_code, stock_name, market,
                                transaction_code, transaction_type, total_amount, total_quantity,
                                broker_fee, stamp_duty, transaction_levy, trading_fee, deposit_fee,
                                prev_quantity, prev_cost, prev_avg_cost,
                                current_quantity, current_cost, current_avg_cost,
                                total_fees, net_amount, running_quantity, running_cost,
                                realized_profit, profit_rate, exchange_rate, remarks,
                                created_at, updated_at, avg_price
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                            )
                        """
                        
                        # 准备参数
                        split_params = [
                            transaction_id,
                            holder['id'],
                            holder['name'],
                            1.0,  # 100%的分配比例
                            transaction_date,
                            stock_id,
                            stock_code,
                            stock_name,
                            market,
                            transaction_data.get('transaction_code', ''),
                            transaction_type,
                            total_amount,
                            total_quantity,
                            broker_fee,
                            stamp_duty,
                            transaction_levy,
                            trading_fee,
                            deposit_fee,
                            float(position_change.get('prev_quantity', 0)),
                            float(position_change.get('prev_cost', 0)),
                            float(position_change.get('prev_avg_cost', 0)),
                            float(position_change.get('current_quantity', 0)),
                            float(position_change.get('current_cost', 0)),
                            float(position_change.get('current_avg_cost', 0)),
                            total_fees,
                            net_amount,
                            running_quantity,
                            running_cost,
                            float(position_change.get('realized_profit', 0)),
                            float(position_change.get('profit_rate', 0)),
                            transaction_data.get('exchange_rate', 1.0),
                            "系统自动创建的100%分单",
                            current_time,
                            current_time,
                            float(position_change.get('avg_price', 0))
                        ]
                        
                        # 执行插入
                        split_id = db_conn.insert(split_sql, split_params)
                        
                        if split_id:
                            logger.info(f"插入分单记录成功，ID: {split_id}")
                            
                            # 更新交易记录的has_splits字段
                            update_has_splits_sql = """
                            UPDATE stock_transactions 
                            SET has_splits = 1, updated_at = %s
                            WHERE id = %s
                            """
                            db_conn.execute(update_has_splits_sql, [current_time, transaction_id])
                            logger.info(f"更新交易记录has_splits字段成功: ID={transaction_id}")
                        else:
                            logger.error("插入分单记录失败")
                    else:
                        logger.error(f"未找到持有人信息: holder_id={holder_id}")
                        
                        # 尝试获取用户的默认持有人
                        default_holder_query = "SELECT id, name FROM holders WHERE user_id = %s LIMIT 1"
                        default_holder = db_conn.fetch_one(default_holder_query, [user_id])
                        
                        if default_holder:
                            logger.info(f"找到用户的默认持有人: id={default_holder['id']}, name={default_holder['name']}")
                            
                            # 获取股票名称
                            stock_name = ""
                            stock_name_query = "SELECT code_name FROM stocks WHERE code = %s AND market = %s"
                            stock_result = db_conn.fetch_one(stock_name_query, [stock_code, market])
                            
                            if stock_result:
                                stock_name = stock_result['code_name']
                            else:
                                stock_name = stock_code
                            
                            # 获取股票ID
                            stock_id = None
                            try:
                                stock_id_sql = """
                                    SELECT id FROM stocks 
                                    WHERE code = %s AND market = %s
                                    LIMIT 1
                                """
                                stock_id_result = db_conn.fetch_one(stock_id_sql, [stock_code, market])
                                if stock_id_result:
                                    stock_id = stock_id_result['id']
                                    logger.info(f"获取到股票ID: {stock_id}")
                                else:
                                    logger.warning(f"未找到股票ID，股票代码: {stock_code}, 市场: {market}")
                            except Exception as e:
                                logger.error(f"获取股票ID失败: {str(e)}")
                            
                            # 计算running_quantity和running_cost
                            running_quantity = position_change.get('current_quantity', 0)
                            running_cost = position_change.get('current_cost', 0)
                            
                            # 构建分单记录SQL
                            split_sql = """
                                INSERT INTO transaction_splits (
                                    original_transaction_id, holder_id, holder_name, split_ratio,
                                    transaction_date, stock_id, stock_code, stock_name, market,
                                    transaction_code, transaction_type, total_amount, total_quantity,
                                    broker_fee, stamp_duty, transaction_levy, trading_fee, deposit_fee,
                                    prev_quantity, prev_cost, prev_avg_cost,
                                    current_quantity, current_cost, current_avg_cost,
                                    total_fees, net_amount, running_quantity, running_cost,
                                    realized_profit, profit_rate, exchange_rate, remarks,
                                    created_at, updated_at, avg_price
                                ) VALUES (
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                                )
                            """
                            
                            # 准备参数
                            split_params = [
                                transaction_id,
                                default_holder['id'],
                                default_holder['name'],
                                1.0,  # 100%的分配比例
                                transaction_date,
                                stock_id,
                                stock_code,
                                stock_name,
                                market,
                                transaction_data.get('transaction_code', ''),
                                transaction_type,
                                total_amount,
                                total_quantity,
                                broker_fee,
                                stamp_duty,
                                transaction_levy,
                                trading_fee,
                                deposit_fee,
                                float(position_change.get('prev_quantity', 0)),
                                float(position_change.get('prev_cost', 0)),
                                float(position_change.get('prev_avg_cost', 0)),
                                float(position_change.get('current_quantity', 0)),
                                float(position_change.get('current_cost', 0)),
                                float(position_change.get('current_avg_cost', 0)),
                                total_fees,
                                net_amount,
                                running_quantity,
                                running_cost,
                                float(position_change.get('realized_profit', 0)),
                                float(position_change.get('profit_rate', 0)),
                                transaction_data.get('exchange_rate', 1.0),
                                "系统自动创建的100%分单",
                                current_time,
                                current_time,
                                float(position_change.get('avg_price', 0))
                            ]
                            
                            # 执行插入
                            split_id = db_conn.insert(split_sql, split_params)
                            
                            if split_id:
                                logger.info(f"使用默认持有人插入分单记录成功，ID: {split_id}")
                                
                                # 更新交易记录的has_splits字段
                                update_has_splits_sql = """
                                UPDATE stock_transactions 
                                SET has_splits = 1, updated_at = %s
                                WHERE id = %s
                                """
                                db_conn.execute(update_has_splits_sql, [current_time, transaction_id])
                                logger.info(f"更新交易记录has_splits字段成功: ID={transaction_id}")
                            else:
                                logger.error("使用默认持有人插入分单记录失败")
                        else:
                            logger.error(f"未找到用户的默认持有人: user_id={user_id}")
                else:
                    # 如果没有提供holder_id，尝试获取用户的默认持有人
                    default_holder_query = "SELECT id, name FROM holders WHERE user_id = %s LIMIT 1"
                    default_holder = db_conn.fetch_one(default_holder_query, [user_id])
                    
                    if default_holder:
                        logger.info(f"找到用户的默认持有人: id={default_holder['id']}, name={default_holder['name']}")
                        
                        # 获取股票名称
                        stock_name = ""
                        stock_name_query = "SELECT code_name FROM stocks WHERE code = %s AND market = %s"
                        stock_result = db_conn.fetch_one(stock_name_query, [stock_code, market])
                        
                        if stock_result:
                            stock_name = stock_result['code_name']
                        else:
                            stock_name = stock_code
                        
                        # 获取股票ID
                        stock_id = None
                        try:
                            stock_id_sql = """
                                SELECT id FROM stocks 
                                WHERE code = %s AND market = %s
                                LIMIT 1
                            """
                            stock_id_result = db_conn.fetch_one(stock_id_sql, [stock_code, market])
                            if stock_id_result:
                                stock_id = stock_id_result['id']
                                logger.info(f"获取到股票ID: {stock_id}")
                            else:
                                logger.warning(f"未找到股票ID，股票代码: {stock_code}, 市场: {market}")
                        except Exception as e:
                            logger.error(f"获取股票ID失败: {str(e)}")
                        
                        # 计算running_quantity和running_cost
                        running_quantity = position_change.get('current_quantity', 0)
                        running_cost = position_change.get('current_cost', 0)
                        
                        # 构建分单记录SQL
                        split_sql = """
                            INSERT INTO transaction_splits (
                                original_transaction_id, holder_id, holder_name, split_ratio,
                                transaction_date, stock_id, stock_code, stock_name, market,
                                transaction_code, transaction_type, total_amount, total_quantity,
                                broker_fee, stamp_duty, transaction_levy, trading_fee, deposit_fee,
                                prev_quantity, prev_cost, prev_avg_cost,
                                current_quantity, current_cost, current_avg_cost,
                                total_fees, net_amount, running_quantity, running_cost,
                                realized_profit, profit_rate, exchange_rate, remarks,
                                created_at, updated_at, avg_price
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                            )
                        """
                        
                        # 准备参数
                        split_params = [
                            transaction_id,
                            default_holder['id'],
                            default_holder['name'],
                            1.0,  # 100%的分配比例
                            transaction_date,
                            stock_id,
                            stock_code,
                            stock_name,
                            market,
                            transaction_data.get('transaction_code', ''),
                            transaction_type,
                            total_amount,
                            total_quantity,
                            broker_fee,
                            stamp_duty,
                            transaction_levy,
                            trading_fee,
                            deposit_fee,
                            float(position_change.get('prev_quantity', 0)),
                            float(position_change.get('prev_cost', 0)),
                            float(position_change.get('prev_avg_cost', 0)),
                            float(position_change.get('current_quantity', 0)),
                            float(position_change.get('current_cost', 0)),
                            float(position_change.get('current_avg_cost', 0)),
                            total_fees,
                            net_amount,
                            running_quantity,
                            running_cost,
                            float(position_change.get('realized_profit', 0)),
                            float(position_change.get('profit_rate', 0)),
                            transaction_data.get('exchange_rate', 1.0),
                            "系统自动创建的100%分单",
                            current_time,
                            current_time,
                            float(position_change.get('avg_price', 0))
                        ]
                        
                        # 执行插入
                        split_id = db_conn.insert(split_sql, split_params)
                        
                        if split_id:
                            logger.info(f"使用默认持有人插入分单记录成功，ID: {split_id}")
                            
                            # 更新交易记录的has_splits字段
                            update_has_splits_sql = """
                            UPDATE stock_transactions 
                            SET has_splits = 1, updated_at = %s
                            WHERE id = %s
                            """
                            db_conn.execute(update_has_splits_sql, [current_time, transaction_id])
                            logger.info(f"更新交易记录has_splits字段成功: ID={transaction_id}")
                        else:
                            logger.error("使用默认持有人插入分单记录失败")
                    else:
                        logger.error(f"未找到用户的默认持有人: user_id={user_id}")
                        
                    # 尝试获取任意持有人
                    any_holder_query = "SELECT id, name FROM holders LIMIT 1"
                    any_holder = db_conn.fetch_one(any_holder_query)
                    
                    if any_holder:
                        logger.info(f"找到系统中的任意持有人: id={any_holder['id']}, name={any_holder['name']}")
                        
                        # 获取股票名称
                        stock_name = ""
                        stock_name_query = "SELECT code_name FROM stocks WHERE code = %s AND market = %s"
                        stock_result = db_conn.fetch_one(stock_name_query, [stock_code, market])
                        
                        if stock_result:
                            stock_name = stock_result['code_name']
                        else:
                            stock_name = stock_code
                        
                        # 获取股票ID
                        stock_id = None
                        try:
                            stock_id_sql = """
                                SELECT id FROM stocks 
                                WHERE code = %s AND market = %s
                                LIMIT 1
                            """
                            stock_id_result = db_conn.fetch_one(stock_id_sql, [stock_code, market])
                            if stock_id_result:
                                stock_id = stock_id_result['id']
                                logger.info(f"获取到股票ID: {stock_id}")
                            else:
                                logger.warning(f"未找到股票ID，股票代码: {stock_code}, 市场: {market}")
                        except Exception as e:
                            logger.error(f"获取股票ID失败: {str(e)}")
                        
                        # 计算running_quantity和running_cost
                        running_quantity = position_change.get('current_quantity', 0)
                        running_cost = position_change.get('current_cost', 0)
                        
                        # 构建分单记录SQL
                        split_sql = """
                            INSERT INTO transaction_splits (
                                original_transaction_id, holder_id, holder_name, split_ratio,
                                transaction_date, stock_id, stock_code, stock_name, market,
                                transaction_code, transaction_type, total_amount, total_quantity,
                                broker_fee, stamp_duty, transaction_levy, trading_fee, deposit_fee,
                                prev_quantity, prev_cost, prev_avg_cost,
                                current_quantity, current_cost, current_avg_cost,
                                total_fees, net_amount, running_quantity, running_cost,
                                realized_profit, profit_rate, exchange_rate, remarks,
                                created_at, updated_at, avg_price
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                            )
                        """
                        
                        # 准备参数
                        split_params = [
                            transaction_id,
                            any_holder['id'],
                            any_holder['name'],
                            1.0,  # 100%的分配比例
                            transaction_date,
                            stock_id,
                            stock_code,
                            stock_name,
                            market,
                            transaction_data.get('transaction_code', ''),
                            transaction_type,
                            total_amount,
                            total_quantity,
                            broker_fee,
                            stamp_duty,
                            transaction_levy,
                            trading_fee,
                            deposit_fee,
                            float(position_change.get('prev_quantity', 0)),
                            float(position_change.get('prev_cost', 0)),
                            float(position_change.get('prev_avg_cost', 0)),
                            float(position_change.get('current_quantity', 0)),
                            float(position_change.get('current_cost', 0)),
                            float(position_change.get('current_avg_cost', 0)),
                            total_fees,
                            net_amount,
                            running_quantity,
                            running_cost,
                            float(position_change.get('realized_profit', 0)),
                            float(position_change.get('profit_rate', 0)),
                            transaction_data.get('exchange_rate', 1.0),
                            "系统自动创建的100%分单",
                            current_time,
                            current_time,
                            float(position_change.get('avg_price', 0))
                        ]
                        
                        # 执行插入
                        split_id = db_conn.insert(split_sql, split_params)
                        
                        if split_id:
                            logger.info(f"使用系统中的任意持有人插入分单记录成功，ID: {split_id}")
                            
                            # 更新交易记录的has_splits字段
                            update_has_splits_sql = """
                            UPDATE stock_transactions 
                            SET has_splits = 1, updated_at = %s
                            WHERE id = %s
                            """
                            db_conn.execute(update_has_splits_sql, [current_time, transaction_id])
                            logger.info(f"更新交易记录has_splits字段成功: ID={transaction_id}")
                        else:
                            logger.error("使用系统中的任意持有人插入分单记录失败")
                    else:
                        logger.error("系统中没有任何持有人记录，无法创建分单")
            except Exception as e:
                logger.error(f"创建分单记录失败: {str(e)}")
                # 不影响主交易记录的创建，继续执行
            
            return True, {
                "message": "添加交易记录成功",
                "id": transaction_id,
                "changes": position_change
            }
        except Exception as e:
            logger.error(f"添加交易记录失败: {str(e)}")
            return False, {"message": f"添加交易记录失败: {str(e)}"}

    @staticmethod
    def _handle_edit(
        db_conn,
        transaction_data: Dict[str, Any],
        position_change: Dict[str, Any],
        transaction_id: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """处理编辑交易"""
        try:
            update_sql = """
                UPDATE stock_transactions
                SET transaction_date = %s,
                    stock_code = %s,
                    market = %s,
                    transaction_type = %s,
                    total_quantity = %s,
                    total_amount = %s,
                    broker_fee = %s,
                    stamp_duty = %s,
                    transaction_levy = %s,
                    trading_fee = %s,
                    deposit_fee = %s,
                    total_fees = %s,
                    net_amount = %s,
                    avg_price = %s,
                    updated_at = NOW()
                WHERE id = %s
            """
            
            params = [
                transaction_data['transaction_date'],
                transaction_data['stock_code'],
                transaction_data['market'],
                transaction_data['transaction_type'],
                transaction_data['total_quantity'],
                transaction_data['total_amount'],
                transaction_data.get('broker_fee', 0),
                transaction_data.get('stamp_duty', 0),
                transaction_data.get('transaction_levy', 0),
                transaction_data.get('trading_fee', 0),
                transaction_data.get('deposit_fee', 0),
                position_change['total_fees'],
                position_change['net_amount'],
                position_change['avg_price'],
                transaction_id
            ]
            
            success = db_conn.execute(update_sql, params)
            if not success:
                return False, {'message': '更新交易记录失败'}
            
            # 重新计算后续交易记录
            logger.info(f"开始重新计算后续交易记录: 股票代码={transaction_data['stock_code']}, 市场={transaction_data['market']}, 日期={transaction_data['transaction_date']}")
            TransactionCalculator.recalculate_subsequent_transactions(
                db_conn,
                transaction_data['stock_code'],
                transaction_data['market'],
                transaction_data['transaction_date']
            )
            
            # 获取交易记录的持有人信息
            split_query = """
                SELECT holder_id FROM transaction_splits
                WHERE original_transaction_id = %s
                LIMIT 1
            """
            split_result = db_conn.fetch_one(split_query, [transaction_id])
            if split_result and split_result['holder_id']:
                holder_id = split_result['holder_id']
                logger.info(f"开始重新计算持有人后续交易记录: 持有人ID={holder_id}, 股票代码={transaction_data['stock_code']}, 市场={transaction_data['market']}, 日期={transaction_data['transaction_date']}")
                TransactionCalculator.recalculate_subsequent_transactions(
                    db_conn,
                    transaction_data['stock_code'],
                    transaction_data['market'],
                    transaction_data['transaction_date'],
                    holder_id
                )
                
            return True, {'position_change': position_change}
            
        except Exception as e:
            logger.error(f"编辑交易记录失败: {str(e)}")
            return False, {'message': f'编辑交易记录失败: {str(e)}'}

    @staticmethod
    def _handle_delete(
        db_conn,
        transaction_data: Dict[str, Any],
        prev_state: Dict[str, Any],
        holder_id: Optional[int] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """处理删除交易"""
        try:
            logger.info(f"开始删除交易记录: ID={transaction_data['id']}, holder_id={holder_id}")
            
            if holder_id:
                # 删除分单记录 - 更新SQL以确保使用 original_transaction_id 作为删除条件
                delete_sql = """
                    DELETE FROM stock.transaction_splits
                    WHERE original_transaction_id = %s
                """
                params = [transaction_data['id']]
                
                # 使用db_conn.execute而不是cursor
                logger.info(f"执行删除分单记录SQL: {delete_sql}, 参数: {params}")
                result = db_conn.execute(delete_sql, params)
                affected_rows = result.rowcount if hasattr(result, 'rowcount') else 0
                logger.info(f"删除分单记录结果: 影响行数={affected_rows}")
                
                if affected_rows == 0:
                    # 只记录警告，不返回错误
                    logger.warning("未找到匹配的分单记录，可能该交易没有分单或已被删除")
                    # 继续执行，不中断流程
            else:
                # 删除原始交易记录
                
                # 1. 先删除交易分单记录
                split_sql = """
                    DELETE FROM stock.transaction_splits
                    WHERE original_transaction_id = %s
                """
                logger.info(f"执行删除分单记录SQL: {split_sql}, 参数: [{transaction_data['id']}]")
                try:
                    split_result = db_conn.execute(split_sql, [transaction_data['id']])
                    split_rows = split_result.rowcount if hasattr(split_result, 'rowcount') else 0
                    logger.info(f"删除分单记录结果: 影响行数={split_rows}")
                except Exception as e:
                    logger.error(f"删除分单记录时出错: {str(e)}")
                    # 继续执行，不终止流程
                
                # 2. 删除交易明细记录
                detail_sql = """
                    DELETE FROM stock.stock_transaction_details
                    WHERE transaction_id = %s
                """
                logger.info(f"执行删除交易明细SQL: {detail_sql}, 参数: [{transaction_data['id']}]")
                detail_result = db_conn.execute(detail_sql, [transaction_data['id']])
                detail_rows = detail_result.rowcount if hasattr(detail_result, 'rowcount') else 0
                logger.info(f"删除交易明细结果: 影响行数={detail_rows}")
                
                # 3. 删除交易记录
                delete_sql = """
                    DELETE FROM stock.stock_transactions
                    WHERE id = %s
                """
                params = [transaction_data['id']]
                
                # 使用db_conn.execute而不是cursor
                logger.info(f"执行删除交易记录SQL: {delete_sql}, 参数: {params}")
                result = db_conn.execute(delete_sql, params)
                affected_rows = result.rowcount if hasattr(result, 'rowcount') else 0
                logger.info(f"删除交易记录结果: 影响行数={affected_rows}")
                
                if affected_rows == 0:
                    logger.error("删除交易记录失败: 未找到匹配的记录")
                    return False, {'message': '删除交易记录失败: 未找到匹配的记录'}
                
                # 重新计算后续交易记录
                logger.info(f"开始重新计算后续交易记录: 股票代码={transaction_data['stock_code']}, 市场={transaction_data['market']}, 日期={transaction_data['transaction_date']}")
                TransactionCalculator.recalculate_subsequent_transactions(
                    db_conn,
                    transaction_data['stock_code'],
                    transaction_data['market'],
                    transaction_data['transaction_date']
                )
                
                # 如果有持有人ID，也重新计算持有人的后续交易记录
                if holder_id:
                    logger.info(f"开始重新计算持有人后续交易记录: 持有人ID={holder_id}, 股票代码={transaction_data['stock_code']}, 市场={transaction_data['market']}, 日期={transaction_data['transaction_date']}")
                    TransactionCalculator.recalculate_subsequent_transactions(
                        db_conn,
                        transaction_data['stock_code'],
                        transaction_data['market'],
                        transaction_data['transaction_date'],
                        holder_id
                    )
            
            return True, {'prev_state': prev_state, 'message': '删除交易记录成功'}
            
        except Exception as e:
            logger.error(f"删除交易记录失败: {str(e)}")
            return False, {'message': f'删除交易记录失败: {str(e)}'}

    @staticmethod
    def _handle_split(
        db_conn,
        transaction_data: Dict[str, Any],
        position_change: Dict[str, Any],
        holder_id: int,
        original_transaction_id: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """处理交易分单"""
        try:
            logger.info(f"开始处理交易分单: holder_id={holder_id}, original_transaction_id={original_transaction_id}")
            logger.info(f"交易数据: {transaction_data}")
            logger.info(f"持仓变化数据: {position_change}")
            
            # 使用交易数据中的holder_id（如果存在）
            actual_holder_id = transaction_data.get('holder_id', holder_id)
            logger.info(f"使用的持有人ID: {actual_holder_id}（来自交易数据: {transaction_data.get('holder_id')}，传入参数: {holder_id}）")
            
            # 获取持有人名称（如果未提供）
            holder_name = transaction_data.get('holder_name', '')
            logger.info(f"从交易数据中获取的持有人名称: '{holder_name}'")
            
            # 检查持有人是否存在，如果不存在则尝试创建
            holder_exists = False
            if not holder_name:
                # 查询持有人名称
                holder_sql = """
                    SELECT id, name FROM holders
                    WHERE id = %s
                    LIMIT 1
                """
                try:
                    holder_result = db_conn.fetch_one(holder_sql, [actual_holder_id])
                    if holder_result:
                        holder_name = holder_result['name']
                        holder_exists = True
                        logger.info(f"从数据库获取的持有人名称: '{holder_name}'")
                    else:
                        # 尝试获取用户ID
                        user_id = transaction_data.get('user_id')
                        if not user_id:
                            # 从原始交易记录获取用户ID
                            user_sql = """
                                SELECT user_id FROM stock_transactions
                                WHERE id = %s
                                LIMIT 1
                            """
                            user_result = db_conn.fetch_one(user_sql, [original_transaction_id])
                            if user_result:
                                user_id = user_result['user_id']
                                logger.info(f"从原始交易记录获取用户ID: {user_id}")
                        
                        # 如果持有人不存在，尝试创建
                        if user_id:
                            # 检查是否有默认持有人
                            default_holder_sql = """
                                SELECT id, name FROM holders
                                WHERE user_id = %s
                                LIMIT 1
                            """
                            default_holder = db_conn.fetch_one(default_holder_sql, [user_id])
                            
                            if default_holder:
                                # 使用默认持有人
                                actual_holder_id = default_holder['id']
                                holder_name = default_holder['name']
                                holder_exists = True
                                logger.info(f"使用默认持有人: id={actual_holder_id}, name={holder_name}")
                            else:
                                # 创建新持有人
                                create_holder_sql = """
                                    INSERT INTO holders (user_id, name, created_at, updated_at)
                                    VALUES (%s, %s, NOW(), NOW())
                                """
                                new_holder_name = f"默认持有人-{user_id}"
                                db_conn.execute(create_holder_sql, [user_id, new_holder_name])
                                
                                # 获取新创建的持有人ID
                                new_holder_sql = """
                                    SELECT id, name FROM holders
                                    WHERE user_id = %s
                                    ORDER BY id DESC
                                    LIMIT 1
                                """
                                new_holder = db_conn.fetch_one(new_holder_sql, [user_id])
                                if new_holder:
                                    actual_holder_id = new_holder['id']
                                    holder_name = new_holder['name']
                                    holder_exists = True
                                    logger.info(f"创建新持有人: id={actual_holder_id}, name={holder_name}")
                        
                        if not holder_exists:
                            # 如果仍然无法获取持有人，使用默认名称
                            holder_name = f"持有人ID: {actual_holder_id}"
                            logger.warning(f"未找到持有人信息，使用默认名称: '{holder_name}'")
                except Exception as e:
                    logger.error(f"获取持有人名称失败: {str(e)}")
                    holder_name = f"持有人ID: {actual_holder_id}"
            
            # 检查是否已存在分单记录
            check_sql = """
                SELECT id FROM transaction_splits
                WHERE original_transaction_id = %s AND holder_id = %s
                LIMIT 1
            """
            existing_split = db_conn.fetch_one(check_sql, [original_transaction_id, actual_holder_id])
            if existing_split:
                logger.info(f"已存在分单记录: id={existing_split['id']}")
                
                # 更新现有分单记录
                update_sql = """
                    UPDATE transaction_splits
                    SET split_ratio = %s,
                        total_quantity = %s,
                        total_amount = %s,
                        broker_fee = %s,
                        stamp_duty = %s,
                        transaction_levy = %s,
                        trading_fee = %s,
                        deposit_fee = %s,
                        prev_quantity = %s,
                        prev_cost = %s,
                        prev_avg_cost = %s,
                        current_quantity = %s,
                        current_cost = %s,
                        current_avg_cost = %s,
                        total_fees = %s,
                        net_amount = %s,
                        realized_profit = %s,
                        profit_rate = %s,
                        avg_price = %s,
                        stock_id = %s,
                        running_quantity = %s,
                        running_cost = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """
                
                # 计算总费用
                total_fees = sum([
                    float(transaction_data.get('broker_fee', 0) or 0),
                    float(transaction_data.get('stamp_duty', 0) or 0),
                    float(transaction_data.get('transaction_levy', 0) or 0),
                    float(transaction_data.get('trading_fee', 0) or 0),
                    float(transaction_data.get('deposit_fee', 0) or 0)
                ])
                
                # 计算净额 - 修改逻辑，不使用负号
                if transaction_data['transaction_type'].lower() == 'buy':
                    net_amount = float(transaction_data.get('total_amount', 0) or 0) + total_fees
                else:  # sell
                    net_amount = float(transaction_data.get('total_amount', 0) or 0) - total_fees
                
                # 计算平均价格
                avg_price = 0
                if float(transaction_data.get('total_quantity', 0) or 0) > 0:
                    avg_price = abs(float(transaction_data.get('total_amount', 0) or 0)) / float(transaction_data.get('total_quantity', 0) or 1)
                
                # 获取股票ID
                stock_id = None
                try:
                    stock_id_sql = """
                        SELECT id FROM stocks 
                        WHERE code = %s AND market = %s
                        LIMIT 1
                    """
                    stock_id_result = db_conn.fetch_one(stock_id_sql, [transaction_data['stock_code'], transaction_data['market']])
                    if stock_id_result:
                        stock_id = stock_id_result['id']
                        logger.info(f"获取到股票ID: {stock_id}")
                    else:
                        logger.warning(f"未找到股票ID，股票代码: {transaction_data['stock_code']}, 市场: {transaction_data['market']}")
                except Exception as e:
                    logger.error(f"获取股票ID失败: {str(e)}")
                
                # 计算running_quantity和running_cost
                running_quantity = position_change.get('current_quantity', 0)
                running_cost = position_change.get('current_cost', 0)
                
                update_params = [
                    transaction_data.get('split_ratio', 1.0),
                    float(transaction_data.get('total_quantity', 0) or 0),
                    float(transaction_data.get('total_amount', 0) or 0),
                    float(transaction_data.get('broker_fee', 0) or 0),
                    float(transaction_data.get('stamp_duty', 0) or 0),
                    float(transaction_data.get('transaction_levy', 0) or 0),
                    float(transaction_data.get('trading_fee', 0) or 0),
                    float(transaction_data.get('deposit_fee', 0) or 0),
                    position_change.get('prev_quantity', 0),
                    position_change.get('prev_cost', 0),
                    position_change.get('prev_avg_cost', 0),
                    position_change.get('current_quantity', 0),
                    position_change.get('current_cost', 0),
                    position_change.get('current_avg_cost', 0),
                    total_fees,
                    net_amount,
                    position_change.get('realized_profit', 0),
                    position_change.get('profit_rate', 0),
                    avg_price,
                    stock_id,
                    running_quantity,
                    running_cost,
                    existing_split['id']
                ]
                
                try:
                    db_conn.execute(update_sql, update_params)
                    logger.info(f"更新分单记录成功: id={existing_split['id']}")
                    
                    # 重新计算持有人的后续交易记录
                    logger.info(f"开始重新计算持有人后续交易记录: 持有人ID={actual_holder_id}, 股票代码={transaction_data['stock_code']}, 市场={transaction_data['market']}, 日期={transaction_data['transaction_date']}")
                    TransactionCalculator.recalculate_subsequent_transactions(
                        db_conn,
                        transaction_data['stock_code'],
                        transaction_data['market'],
                        transaction_data['transaction_date'],
                        actual_holder_id
                    )
                    
                    return True, {
                        'message': '更新分单记录成功',
                        'id': existing_split['id']
                    }
                except Exception as e:
                    logger.error(f"更新分单记录失败: {str(e)}")
                    return False, {'message': f'更新分单记录失败: {str(e)}'}
            
            # 获取交易编号
            transaction_code_sql = """
                SELECT transaction_code FROM stock_transactions
                WHERE id = %s
                LIMIT 1
            """
            transaction_code = None
            try:
                with db_conn.get_connection() as conn:
                    cursor = conn.cursor(pymysql.cursors.DictCursor)
                    cursor.execute(transaction_code_sql, [original_transaction_id])
                    transaction_code_result = cursor.fetchone()
                    if transaction_code_result:
                        transaction_code = transaction_code_result['transaction_code']
            except Exception as e:
                logger.error(f"获取交易编号失败: {str(e)}")
            
            # 当前时间
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 确保split_ratio为1.0（100%）
            split_ratio = transaction_data.get('split_ratio', 1.0)
            
            # 获取股票名称
            stock_name = transaction_data.get('stock_name', '')
            if not stock_name:
                stock_name_sql = """
                    SELECT code_name FROM stocks 
                    WHERE code = %s AND market = %s
                    LIMIT 1
                """
                try:
                    with db_conn.get_connection() as conn:
                        cursor = conn.cursor(pymysql.cursors.DictCursor)
                        cursor.execute(stock_name_sql, [transaction_data['stock_code'], transaction_data['market']])
                        stock_result = cursor.fetchone()
                        if stock_result:
                            stock_name = stock_result['code_name']
                        else:
                            stock_name = transaction_data['stock_code']
                except Exception as e:
                    logger.error(f"获取股票名称失败: {str(e)}")
                    stock_name = transaction_data['stock_code']
            
            # 获取股票ID
            stock_id = None
            try:
                stock_id_sql = """
                    SELECT id FROM stocks 
                    WHERE code = %s AND market = %s
                    LIMIT 1
                """
                stock_id_result = db_conn.fetch_one(stock_id_sql, [transaction_data['stock_code'], transaction_data['market']])
                if stock_id_result:
                    stock_id = stock_id_result['id']
                    logger.info(f"获取到股票ID: {stock_id}")
                else:
                    logger.warning(f"未找到股票ID，股票代码: {transaction_data['stock_code']}, 市场: {transaction_data['market']}")
            except Exception as e:
                logger.error(f"获取股票ID失败: {str(e)}")
            
            # 计算running_quantity和running_cost
            running_quantity = position_change.get('current_quantity', 0)
            running_cost = position_change.get('current_cost', 0)
            
            # 计算总费用
            total_fees = sum([
                float(transaction_data.get('broker_fee', 0) or 0),
                float(transaction_data.get('stamp_duty', 0) or 0),
                float(transaction_data.get('transaction_levy', 0) or 0),
                float(transaction_data.get('trading_fee', 0) or 0),
                float(transaction_data.get('deposit_fee', 0) or 0)
            ])
            
            # 计算净额 - 修改逻辑，不使用负号
            if transaction_data['transaction_type'].lower() == 'buy':
                net_amount = float(transaction_data.get('total_amount', 0) or 0) + total_fees
            else:  # sell
                net_amount = float(transaction_data.get('total_amount', 0) or 0) - total_fees
            
            # 计算平均价格
            avg_price = 0
            if float(transaction_data.get('total_quantity', 0) or 0) > 0:
                avg_price = abs(float(transaction_data.get('total_amount', 0) or 0)) / float(transaction_data.get('total_quantity', 0) or 1)
            
            # 直接使用SQL插入分单记录
            direct_split_sql = """
                INSERT INTO transaction_splits (
                    original_transaction_id, holder_id, holder_name, split_ratio,
                    transaction_date, stock_id, stock_code, stock_name, market,
                    transaction_type, total_quantity, total_amount,
                    broker_fee, stamp_duty, transaction_levy,
                    trading_fee, deposit_fee, transaction_code, 
                    prev_quantity, prev_cost, prev_avg_cost,
                    current_quantity, current_cost, current_avg_cost,
                    total_fees, net_amount, realized_profit,
                    profit_rate, avg_price, running_quantity, running_cost, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            direct_split_params = [
                original_transaction_id,  # original_transaction_id
                actual_holder_id,  # holder_id
                holder_name,  # holder_name
                split_ratio,  # split_ratio
                transaction_data['transaction_date'],  # transaction_date
                stock_id,  # stock_id
                transaction_data['stock_code'],  # stock_code
                stock_name,  # stock_name
                transaction_data['market'],  # market
                transaction_data['transaction_type'],  # transaction_type
                float(transaction_data['total_quantity']),  # total_quantity
                float(transaction_data['total_amount']),  # total_amount
                float(transaction_data.get('broker_fee', 0) or 0),  # broker_fee
                float(transaction_data.get('stamp_duty', 0) or 0),  # stamp_duty
                float(transaction_data.get('transaction_levy', 0) or 0),  # transaction_levy
                float(transaction_data.get('trading_fee', 0) or 0),  # trading_fee
                float(transaction_data.get('deposit_fee', 0) or 0),  # deposit_fee
                transaction_code,  # transaction_code
                position_change.get('prev_quantity', 0),  # prev_quantity
                position_change.get('prev_cost', 0),  # prev_cost
                position_change.get('prev_avg_cost', 0),  # prev_avg_cost
                position_change.get('current_quantity', 0),  # current_quantity
                position_change.get('current_cost', 0),  # current_cost
                position_change.get('current_avg_cost', 0),  # current_avg_cost
                total_fees,  # total_fees
                net_amount,  # net_amount
                position_change.get('realized_profit', 0),  # realized_profit
                position_change.get('profit_rate', 0),  # profit_rate
                float(position_change.get('avg_price', 0)),  # avg_price
                running_quantity,  # running_quantity
                running_cost,  # running_cost
                current_time  # created_at
            ]
            
            # 执行SQL插入
            try:
                with db_conn.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(direct_split_sql, direct_split_params)
                    conn.commit()
                    logger.info("分单记录插入成功")
                    
                    # 重新计算持有人的后续交易记录
                    logger.info(f"开始重新计算持有人后续交易记录: 持有人ID={actual_holder_id}, 股票代码={transaction_data['stock_code']}, 市场={transaction_data['market']}, 日期={transaction_data['transaction_date']}")
                    TransactionCalculator.recalculate_subsequent_transactions(
                        db_conn,
                        transaction_data['stock_code'],
                        transaction_data['market'],
                        transaction_data['transaction_date'],
                        actual_holder_id
                    )
                    
                    return True, {
                        'message': '分单处理成功',
                        'id': original_transaction_id
                    }
            except Exception as sql_e:
                logger.error(f"分单记录插入失败: {str(sql_e)}")
                return False, {'message': f'分单记录插入失败: {str(sql_e)}'}
            
        except Exception as e:
            logger.error(f"处理交易分单失败: {str(e)}")
            return False, {'message': f'处理交易分单失败: {str(e)}'}

    @staticmethod
    def recalculate_subsequent_transactions(
        db_conn,
        stock_code: str,
        market: str,
        start_date: str,
        holder_id: Optional[int] = None
    ) -> bool:
        """
        重新计算后续交易记录
        
        Args:
            db_conn: 数据库连接
            stock_code: 股票代码
            market: 市场
            start_date: 开始日期
            holder_id: 持有人ID（可选）
            
        Returns:
            bool: 是否成功
        """
        try:
            # 获取需要重新计算的交易记录
            if holder_id:
                sql = """
                    SELECT *
                    FROM transaction_splits
                    WHERE holder_id = %s
                        AND stock_code = %s
                        AND market = %s
                        AND transaction_date >= %s
                    ORDER BY transaction_date, id
                """
                params = [holder_id, stock_code, market, start_date]
            else:
                sql = """
                    SELECT *
                    FROM stock_transactions
                    WHERE stock_code = %s
                        AND market = %s
                        AND transaction_date >= %s
                    ORDER BY transaction_date, id
                """
                params = [stock_code, market, start_date]
            
            # 使用db_conn.fetch_all而不是cursor
            transactions = db_conn.fetch_all(sql, params)
            
            if not transactions:
                return True
            
            # 获取第一条记录之前的状态
            prev_state = TransactionCalculator._get_previous_holding_state(
                db_conn,
                holder_id if holder_id else transactions[0]['user_id'],
                stock_code,
                market,
                start_date,
                is_split=bool(holder_id)
            )
            
            # 逐条重新计算
            for trans in transactions:
                # 构建交易数据
                transaction_data = {
                    'transaction_type': trans['transaction_type'],
                    'total_quantity': trans['total_quantity'],
                    'total_amount': trans['total_amount'],
                    'broker_fee': trans['broker_fee'],
                    'stamp_duty': trans['stamp_duty'],
                    'transaction_levy': trans['transaction_levy'],
                    'trading_fee': trans['trading_fee'],
                    'deposit_fee': trans['deposit_fee']
                }
                
                # 计算持仓变化
                try:
                    position_change = TransactionCalculator.calculate_position_change(
                        transaction_data, prev_state, is_split=True, skip_validation=True
                    )
                except ValueError:
                    return False
                
                # 更新数据库
                if holder_id:
                    update_sql = """
                        UPDATE transaction_splits
                        SET prev_quantity = %s,
                            prev_cost = %s,
                            prev_avg_cost = %s,
                            current_quantity = %s,
                            current_cost = %s,
                            current_avg_cost = %s,
                            total_fees = %s,
                            net_amount = %s,
                            realized_profit = %s,
                            profit_rate = %s,
                            avg_price = %s,
                            updated_at = NOW()
                        WHERE id = %s
                    """
                    
                    params = [
                        position_change['prev_quantity'],
                        position_change['prev_cost'],
                        position_change['prev_avg_cost'],
                        position_change['current_quantity'],
                        position_change['current_cost'],
                        position_change['current_avg_cost'],
                        position_change['total_fees'],
                        position_change['net_amount'],
                        position_change['realized_profit'],
                        position_change['profit_rate'],
                        position_change['avg_price'],
                        trans['id']
                    ]
                else:
                    update_sql = """
                        UPDATE stock_transactions
                        SET total_fees = %s,
                            net_amount = %s,
                            avg_price = %s,
                            updated_at = NOW()
                        WHERE id = %s
                    """
                    
                    params = [
                        position_change['total_fees'],
                        position_change['net_amount'],
                        position_change['avg_price'],
                        trans['id']
                    ]
                
                # 使用db_conn.execute而不是cursor
                db_conn.execute(update_sql, params)
                
                # 更新前值状态用于下一次计算
                prev_state = {
                    'quantity': position_change['current_quantity'],
                    'cost': position_change['current_cost'],
                    'avg_cost': position_change['current_avg_cost']
                }
            
            return True
            
        except Exception as e:
            logger.error(f"重新计算后续交易记录失败: {str(e)}")
            return False

    @staticmethod
    def validate_transaction(transaction):
        """验证交易记录"""
        logger.info(f"开始验证交易数据: {transaction}")
        
        required_fields = [
            'transaction_date',
            'stock_code',
            'market',
            'transaction_type',
            'total_quantity',
            'total_amount'
        ]
        
        errors = []
        
        # 检查必填字段
        for field in required_fields:
            if field not in transaction or transaction.get(field) is None or transaction.get(field) == '':
                errors.append(f'缺少必填字段: {field}')
                logger.error(f"交易数据缺少必填字段: {field}")
        
        # 验证数值字段
        if 'total_quantity' in transaction and transaction['total_quantity'] is not None:
            try:
                quantity = float(transaction['total_quantity'])
                if quantity <= 0:
                    errors.append('交易数量必须大于0')
                    logger.error(f"交易数量必须大于0: {quantity}")
            except Exception as e:
                errors.append('交易数量必须为数字')
                logger.error(f"交易数量必须为数字: {transaction['total_quantity']}, 错误: {str(e)}")
        
        if 'total_amount' in transaction and transaction['total_amount'] is not None:
            try:
                amount = float(transaction['total_amount'])
                if amount <= 0:
                    errors.append('交易金额必须大于0')
                    logger.error(f"交易金额必须大于0: {amount}")
            except Exception as e:
                errors.append('交易金额必须为数字')
                logger.error(f"交易金额必须为数字: {transaction['total_amount']}, 错误: {str(e)}")
        
        # 验证交易类型
        if 'transaction_type' in transaction and transaction['transaction_type'] is not None:
            if transaction['transaction_type'].lower() not in ['buy', 'sell']:
                errors.append('交易类型必须为 buy 或 sell')
                logger.error(f"交易类型必须为 buy 或 sell: {transaction['transaction_type']}")
        
        # 验证日期格式
        if 'transaction_date' in transaction and transaction['transaction_date'] is not None:
            try:
                if isinstance(transaction['transaction_date'], str):
                    datetime.strptime(transaction['transaction_date'], '%Y-%m-%d')
                elif not isinstance(transaction['transaction_date'], datetime):
                    errors.append('交易日期格式错误，应为 YYYY-MM-DD 或 datetime 对象')
                    logger.error(f"交易日期格式错误: {transaction['transaction_date']}")
            except Exception as e:
                errors.append('交易日期格式错误，应为 YYYY-MM-DD')
                logger.error(f"交易日期格式错误: {transaction['transaction_date']}, 错误: {str(e)}")
        
        # 验证股票代码和市场
        if 'stock_code' in transaction and transaction['stock_code'] is not None:
            if not isinstance(transaction['stock_code'], str) or len(transaction['stock_code']) == 0:
                errors.append('股票代码必须为非空字符串')
                logger.error(f"股票代码必须为非空字符串: {transaction['stock_code']}")
        
        if 'market' in transaction and transaction['market'] is not None:
            if transaction['market'] not in ['HK', 'USA', 'CN']:
                errors.append('市场必须为 HK、USA 或 CN')
                logger.error(f"市场必须为 HK、USA 或 CN: {transaction['market']}")
        
        # 验证交易明细
        if 'details' in transaction and transaction['details']:
            for i, detail in enumerate(transaction['details']):
                if 'quantity' not in detail or detail['quantity'] is None:
                    errors.append(f'明细 #{i+1} 缺少数量')
                    logger.error(f"明细 #{i+1} 缺少数量")
                elif not isinstance(detail['quantity'], (int, float, str)) or float(detail['quantity']) <= 0:
                    errors.append(f'明细 #{i+1} 数量必须为大于0的数字')
                    logger.error(f"明细 #{i+1} 数量必须为大于0的数字: {detail['quantity']}")
                
                if 'price' not in detail or detail['price'] is None:
                    errors.append(f'明细 #{i+1} 缺少价格')
                    logger.error(f"明细 #{i+1} 缺少价格")
                elif not isinstance(detail['price'], (int, float, str)) or float(detail['price']) <= 0:
                    errors.append(f'明细 #{i+1} 价格必须为大于0的数字')
                    logger.error(f"明细 #{i+1} 价格必须为大于0的数字: {detail['price']}")
        
        if errors:
            logger.error(f"交易数据验证失败，共有 {len(errors)} 个错误")
        else:
            logger.info("交易数据验证通过")
            
        return errors 