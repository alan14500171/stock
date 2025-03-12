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
    def calculate_position_change(transaction, prev_state):
        """计算持仓变化"""
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
            if prev_quantity < total_quantity:
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
                    holder_id,
                    transaction_data['stock_code'],
                    transaction_data['market'],
                    transaction_data['transaction_date']
                )
                
                # 计算持仓变化
                position_change = TransactionCalculator.calculate_position_change(transaction_data, prev_state)
                
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
                
                # 计算持仓变化
                position_change = TransactionCalculator.calculate_position_change(transaction_data, prev_state)
                
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
                
                # 计算持仓变化
                position_change = TransactionCalculator.calculate_position_change(transaction_data, prev_state)
                
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
        """获取之前的持仓状态"""
        table = "transaction_splits" if is_split else "stock_transactions"
        id_field = "holder_id" if is_split else "user_id"
        
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
        
        params = [
            user_or_holder_id, stock_code, market,
            transaction_date, transaction_date,
            transaction_id or 0
        ]
        
        # 使用db_conn.fetch_one而不是cursor
        result = db_conn.fetch_one(sql, params)
        
        if result:
            return {
                'quantity': Decimal(str(result['quantity'])),
                'cost': Decimal(str(result['cost'])),
                'avg_cost': Decimal(str(result['avg_cost']))
            }
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
            # 确保holder_id不为None
            if holder_id is None:
                logger.error("添加交易记录失败: user_id不能为空")
                return False, {'message': '添加交易记录失败: user_id不能为空'}
            
            # 记录详细的交易数据和持有人ID，用于调试
            logger.info(f"开始添加交易记录: holder_id={holder_id}, data={transaction_data}")
                
            # 查询表结构，确保SQL语句与表结构匹配
            try:
                table_info = db_conn.fetch_all("DESCRIBE stock_transactions")
                columns = [col['Field'] for col in table_info] if table_info else []
                logger.info(f"stock_transactions表的列: {columns}")
            except Exception as e:
                logger.error(f"获取表结构失败: {str(e)}")
                columns = []
            
            # 构建SQL语句，根据实际表结构调整
            has_transaction_code = 'transaction_code' in columns
            has_created_at = 'created_at' in columns
            
            # 构建字段列表和值占位符
            fields = [
                "user_id", "transaction_date", "stock_code", "market",
                "transaction_type", "total_quantity", "total_amount",
                "broker_fee", "stamp_duty", "transaction_levy",
                "trading_fee", "deposit_fee", "prev_quantity",
                "prev_cost", "prev_avg_cost", "current_quantity",
                "current_cost", "current_avg_cost", "total_fees",
                "net_amount", "realized_profit", "profit_rate",
                "avg_price"
            ]
            
            # 添加可选字段
            if has_transaction_code:
                fields.append("transaction_code")
            
            # 始终添加created_at字段，即使表结构检查没有发现它
            # 这是为了确保即使表结构检查失败，也能尝试设置created_at
            fields.append("created_at")
                
            # 构建参数列表
            params = [
                holder_id,  # 使用传入的holder_id作为user_id
                transaction_data['transaction_date'],
                transaction_data['stock_code'],
                transaction_data['market'],
                transaction_data['transaction_type'],
                float(transaction_data['total_quantity']),
                float(transaction_data['total_amount']),
                float(transaction_data.get('broker_fee', 0)),
                float(transaction_data.get('stamp_duty', 0)),
                float(transaction_data.get('transaction_levy', 0)),
                float(transaction_data.get('trading_fee', 0)),
                float(transaction_data.get('deposit_fee', 0)),
                float(position_change['prev_quantity']),
                float(position_change['prev_cost']),
                float(position_change['prev_avg_cost']),
                float(position_change['current_quantity']),
                float(position_change['current_cost']),
                float(position_change['current_avg_cost']),
                float(position_change['total_fees']),
                float(position_change['net_amount']),
                float(position_change['realized_profit']),
                float(position_change['profit_rate']),
                float(position_change['avg_price'])
            ]
            
            # 添加可选参数
            if has_transaction_code:
                params.append(transaction_data.get('transaction_code', ''))
            
            # 始终添加created_at参数
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            params.append(current_time)
            
            # 构建SQL语句
            placeholders = ", ".join(["%s"] * len(fields))
            fields_str = ", ".join(fields)
            insert_sql = f"""
                INSERT INTO stock_transactions (
                    {fields_str}
                ) VALUES (
                    {placeholders}
                )
            """
            
            # 记录SQL和参数，用于调试
            logger.info(f"执行SQL: {insert_sql}")
            logger.info(f"参数: {params}")
            
            # 使用execute而不是insert，并手动获取最后插入的ID
            try:
                # 执行插入操作
                db_conn.execute(insert_sql, params)
                
                # 获取最后插入的ID
                result = db_conn.fetch_one("SELECT LAST_INSERT_ID() as id")
                if not result or 'id' not in result:
                    logger.error("插入交易记录失败: 无法获取最后插入的ID")
                    return False, {'message': '插入交易记录失败: 无法获取最后插入的ID'}
                    
                transaction_id = result['id']
                logger.info(f"交易记录插入成功: ID={transaction_id}")
                
                # 确保transaction_id不为0
                if transaction_id == 0:
                    # 尝试通过transaction_code查询获取真实ID
                    if 'transaction_code' in transaction_data and transaction_data['transaction_code']:
                        query = "SELECT id FROM stock_transactions WHERE transaction_code = %s ORDER BY id DESC LIMIT 1"
                        id_result = db_conn.fetch_one(query, [transaction_data['transaction_code']])
                        if id_result and 'id' in id_result:
                            transaction_id = id_result['id']
                            logger.info(f"通过transaction_code获取到真实ID: {transaction_id}")
                        else:
                            logger.error(f"无法通过transaction_code获取真实ID: {transaction_data['transaction_code']}")
                            return False, {'message': '插入交易记录失败: 无法获取有效的交易ID'}
                    else:
                        logger.error("插入交易记录失败: 获取到的ID为0且无法通过transaction_code查询")
                        return False, {'message': '插入交易记录失败: 获取到的ID为0'}
                
                # 插入交易明细
                if 'details' in transaction_data and transaction_data['details']:
                    # 查询交易明细表结构
                    try:
                        detail_table_info = db_conn.fetch_all("DESCRIBE stock_transaction_details")
                        detail_columns = [col['Field'] for col in detail_table_info] if detail_table_info else []
                        logger.info(f"stock_transaction_details表的列: {detail_columns}")
                    except Exception as e:
                        logger.error(f"获取交易明细表结构失败: {str(e)}")
                        detail_columns = []
                    
                    # 检查是否有amount字段和created_at字段
                    has_amount = 'amount' in detail_columns
                    has_detail_created_at = 'created_at' in detail_columns
                    
                    # 构建交易明细SQL
                    detail_fields = ["transaction_id", "quantity", "price"]
                    if has_amount:
                        detail_fields.append("amount")
                    
                    # 始终添加created_at字段
                    detail_fields.append("created_at")
                    
                    detail_placeholders = ", ".join(["%s"] * len(detail_fields))
                    detail_fields_str = ", ".join(detail_fields)
                    
                    detail_sql = f"""
                        INSERT INTO stock_transaction_details (
                            {detail_fields_str}
                        ) VALUES (
                            {detail_placeholders}
                        )
                    """
                    
                    detail_success = True
                    for detail in transaction_data['details']:
                        quantity = float(detail['quantity'])
                        price = float(detail['price'])
                        
                        detail_params = [transaction_id, quantity, price]
                        if has_amount:
                            amount = quantity * price
                            detail_params.append(amount)
                        
                        # 始终添加created_at参数
                        detail_params.append(current_time)
                        
                        logger.info(f"插入交易明细: {detail_params}")
                        
                        try:
                            db_conn.execute(detail_sql, detail_params)
                        except Exception as e:
                            logger.error(f"插入交易明细失败: {str(e)}")
                            detail_success = False
                            break
                    
                    if not detail_success:
                        logger.error("交易明细插入失败")
                        return False, {'message': '插入交易明细失败'}
                    
                    logger.info(f"交易明细插入成功: 共{len(transaction_data['details'])}条")
                
                # 自动创建分单记录
                split_created = False
                try:
                    # 确保transaction_data中包含必要的字段
                    if 'split_ratio' not in transaction_data:
                        transaction_data['split_ratio'] = 1.0  # 设置默认值为100%
                    
                    # 检查是否已存在分单记录
                    check_split_sql = "SELECT COUNT(*) as count FROM transaction_splits WHERE original_transaction_id = %s"
                    split_count_result = db_conn.fetch_one(check_split_sql, [transaction_id])
                    
                    if split_count_result and split_count_result['count'] > 0:
                        logger.info(f"已存在分单记录，无需创建: count={split_count_result['count']}")
                        split_created = True
                    else:
                        logger.info("开始创建分单记录")
                        
                        # 获取股票名称
                        stock_name_sql = """
                            SELECT code_name FROM stocks 
                            WHERE code = %s AND market = %s
                            LIMIT 1
                        """
                        stock_params = [
                            transaction_data['stock_code'],
                            transaction_data['market']
                        ]
                        stock_result = db_conn.fetch_one(stock_name_sql, stock_params)
                        stock_name = stock_result['code_name'] if stock_result else transaction_data['stock_code']
                        
                        # 获取用户的默认持有人ID
                        user_id = transaction_data.get('user_id', holder_id)
                        default_holder_sql = """
                            SELECT id, name FROM holders
                            WHERE user_id = %s
                            LIMIT 1
                        """
                        default_holder_result = db_conn.fetch_one(default_holder_sql, [user_id])
                        
                        if default_holder_result:
                            # 使用用户的默认持有人
                            actual_holder_id = default_holder_result['id']
                            holder_name = default_holder_result['name']
                            logger.info(f"使用用户的默认持有人: ID={actual_holder_id}, 名称='{holder_name}'")
                        else:
                            # 检查holders表中是否存在该用户ID作为持有人
                            check_holder_sql = """
                                SELECT id, name FROM holders
                                WHERE id = %s
                                LIMIT 1
                            """
                            holder_result = db_conn.fetch_one(check_holder_sql, [holder_id])
                            
                            if holder_result:
                                actual_holder_id = holder_id
                                holder_name = holder_result['name']
                                logger.info(f"使用传入的持有人ID: ID={actual_holder_id}, 名称='{holder_name}'")
                            else:
                                # 获取所有持有人，选择第一个
                                all_holders_sql = """
                                    SELECT id, name FROM holders
                                    LIMIT 1
                                """
                                all_holders_result = db_conn.fetch_one(all_holders_sql)
                                
                                if all_holders_result:
                                    actual_holder_id = all_holders_result['id']
                                    holder_name = all_holders_result['name']
                                    logger.info(f"使用系统中的第一个持有人: ID={actual_holder_id}, 名称='{holder_name}'")
                                else:
                                    logger.error("系统中没有任何持有人记录，无法创建分单")
                                    return True, {
                                        'message': '添加交易记录成功，但无法创建分单（系统中没有持有人记录）',
                                        'id': transaction_id,
                                        'position_change': position_change,
                                        'split_created': False
                                    }
                        
                        # 确保holder_name不为空
                        if not holder_name:
                            holder_name = f"持有人ID: {actual_holder_id}"
                            logger.warning(f"持有人名称为空，使用默认名称: '{holder_name}'")
                        
                        logger.info(f"最终使用的持有人ID: {actual_holder_id}, 名称: '{holder_name}'")
                        
                        # 检查transaction_splits表是否有holder_name字段
                        check_column_sql = """
                            SELECT COUNT(*) as count
                            FROM information_schema.COLUMNS 
                            WHERE TABLE_SCHEMA = DATABASE()
                            AND TABLE_NAME = 'transaction_splits' 
                            AND COLUMN_NAME = 'holder_name'
                        """
                        result = db_conn.fetch_one(check_column_sql)
                        has_holder_name = result['count'] > 0
                        
                        logger.info(f"transaction_splits表是否有holder_name字段: {has_holder_name}")
                        
                        # 检查transaction_splits表是否有created_at字段
                        check_created_at_sql = """
                            SELECT COUNT(*) as count
                            FROM information_schema.COLUMNS 
                            WHERE TABLE_SCHEMA = DATABASE()
                            AND TABLE_NAME = 'transaction_splits' 
                            AND COLUMN_NAME = 'created_at'
                        """
                        created_at_result = db_conn.fetch_one(check_created_at_sql)
                        has_created_at = created_at_result['count'] > 0
                        
                        logger.info(f"transaction_splits表是否有created_at字段: {has_created_at}")
                        
                        # 直接使用SQL插入分单记录
                        try:
                            # 构建字段和占位符
                            fields = [
                                "original_transaction_id", "holder_id", "split_ratio",
                                "transaction_date", "stock_code", "market", "stock_name",
                                "transaction_type", "total_quantity", "total_amount",
                                "broker_fee", "stamp_duty", "transaction_levy",
                                "trading_fee", "deposit_fee", "prev_quantity",
                                "prev_cost", "prev_avg_cost", "current_quantity",
                                "current_cost", "current_avg_cost", "total_fees",
                                "net_amount", "realized_profit", "profit_rate",
                                "avg_price", "transaction_code", "remarks"
                            ]
                            
                            # 添加可选字段
                            if has_holder_name:
                                fields.append("holder_name")
                            if has_created_at:
                                fields.append("created_at")
                            
                            # 构建占位符
                            placeholders = ["%s"] * len(fields)
                            
                            # 构建SQL
                            fields_str = ", ".join(fields)
                            placeholders_str = ", ".join(placeholders)
                            
                            simple_split_sql = f"""
                                INSERT INTO transaction_splits (
                                    {fields_str}
                                ) VALUES (
                                    {placeholders_str}
                                )
                            """
                            
                            # 准备基本参数
                            split_params = [
                                transaction_id,  # original_transaction_id
                                actual_holder_id,  # holder_id
                                1.0,  # split_ratio (100%)
                                transaction_data['transaction_date'],  # transaction_date
                                transaction_data['stock_code'],  # stock_code
                                transaction_data['market'],  # market
                                stock_name,  # stock_name
                                transaction_data['transaction_type'],  # transaction_type
                                float(transaction_data['total_quantity']),  # total_quantity
                                float(transaction_data['total_amount']),  # total_amount
                                float(transaction_data.get('broker_fee', 0)),  # broker_fee
                                float(transaction_data.get('stamp_duty', 0)),  # stamp_duty
                                float(transaction_data.get('transaction_levy', 0)),  # transaction_levy
                                float(transaction_data.get('trading_fee', 0)),  # trading_fee
                                float(transaction_data.get('deposit_fee', 0)),  # deposit_fee
                                float(position_change['prev_quantity']),  # prev_quantity
                                float(position_change['prev_cost']),  # prev_cost
                                float(position_change['prev_avg_cost']),  # prev_avg_cost
                                float(position_change['current_quantity']),  # current_quantity
                                float(position_change['current_cost']),  # current_cost
                                float(position_change['current_avg_cost']),  # current_avg_cost
                                float(position_change['total_fees']),  # total_fees
                                float(position_change['net_amount']),  # net_amount
                                float(position_change['realized_profit']),  # realized_profit
                                float(position_change['profit_rate']),  # profit_rate
                                float(position_change['avg_price']),  # avg_price
                                transaction_data.get('transaction_code', ''),  # transaction_code
                                transaction_data.get('remarks', '系统自动创建的100%分单') or '系统自动创建的100%分单'  # remarks
                            ]
                            
                            # 添加可选参数
                            if has_holder_name:
                                split_params.append(holder_name)  # holder_name
                            if has_created_at:
                                split_params.append(current_time)  # created_at
                            
                            # 记录SQL语句和参数数量，用于调试
                            logger.info(f"分单SQL语句中的占位符数量: {simple_split_sql.count('%s')}")
                            logger.info(f"分单参数列表中的参数数量: {len(split_params)}")
                            
                            # 执行SQL插入
                            db_conn.execute(simple_split_sql, split_params)
                            logger.info("分单记录插入成功")
                            split_created = True
                            
                            # 更新交易记录的has_splits字段
                            update_has_splits_sql = "UPDATE stock_transactions SET has_splits = 1 WHERE id = %s"
                            db_conn.execute(update_has_splits_sql, [transaction_id])
                            logger.info(f"更新交易记录has_splits字段成功: ID={transaction_id}")
                        except Exception as split_e:
                            logger.error(f"直接插入分单记录失败: {str(split_e)}")
                            logger.error(f"错误详情: {traceback.format_exc()}")
                            
                            # 尝试使用更简单的SQL语句
                            try:
                                # 构建最小字段集
                                min_fields = [
                                    "original_transaction_id", "holder_id", "split_ratio",
                                    "transaction_date", "stock_code", "market",
                                    "transaction_type", "total_quantity", "total_amount"
                                ]
                                
                                # 添加可选字段
                                if has_holder_name:
                                    min_fields.append("holder_name")
                                
                                # 构建占位符
                                min_placeholders = ["%s"] * len(min_fields)
                                
                                # 构建SQL
                                min_fields_str = ", ".join(min_fields)
                                min_placeholders_str = ", ".join(min_placeholders)
                                
                                very_simple_split_sql = f"""
                                    INSERT INTO transaction_splits (
                                        {min_fields_str}
                                    ) VALUES (
                                        {min_placeholders_str}
                                    )
                                """
                                
                                # 准备最小参数集
                                very_simple_params = [
                                    transaction_id,
                                    actual_holder_id,
                                    1.0,
                                    transaction_data['transaction_date'],
                                    transaction_data['stock_code'],
                                    transaction_data['market'],
                                    transaction_data['transaction_type'],
                                    float(transaction_data['total_quantity']),
                                    float(transaction_data['total_amount'])
                                ]
                                
                                # 添加可选参数
                                if has_holder_name:
                                    very_simple_params.append(holder_name)
                                
                                db_conn.execute(very_simple_split_sql, very_simple_params)
                                logger.info("简化版分单记录插入成功")
                                split_created = True
                                
                                # 更新交易记录的has_splits字段
                                db_conn.execute(update_has_splits_sql, [transaction_id])
                            except Exception as very_simple_e:
                                logger.error(f"简化版分单记录插入失败: {str(very_simple_e)}")
                except Exception as e:
                    logger.error(f"创建分单记录失败: {str(e)}")
                    logger.error(f"错误详情: {traceback.format_exc()}")
                
                # 返回成功结果
                return True, {
                    'message': '添加交易记录成功',
                    'id': transaction_id,
                    'position_change': position_change,
                    'split_created': split_created
                }
                
            except Exception as e:
                logger.error(f"插入交易记录失败: {str(e)}")
                return False, {'message': f'插入交易记录失败: {str(e)}'}
                
        except Exception as e:
            logger.error(f"处理新增交易失败: {str(e)}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            return False, {'message': f'处理新增交易失败: {str(e)}'}

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
                    remarks = %s,
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
                transaction_data.get('remarks', ''),
                transaction_id
            ]
            
            success = db_conn.execute(update_sql, params)
            if not success:
                return False, {'message': '更新交易记录失败'}
                
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
            
            if not holder_name:
                # 查询持有人名称
                holder_sql = """
                    SELECT name FROM holders
                    WHERE id = %s
                    LIMIT 1
                """
                try:
                    holder_result = db_conn.fetch_one(holder_sql, [actual_holder_id])
                    if holder_result:
                        holder_name = holder_result['name']
                        logger.info(f"从数据库获取的持有人名称: '{holder_name}'")
                    else:
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
                
                # 计算净额
                net_amount = float(transaction_data.get('total_amount', 0) or 0) + total_fees
                
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
            
            # 计算净额
            net_amount = float(transaction_data.get('total_amount', 0) or 0) + total_fees
            
            # 计算平均价格
            avg_price = 0
            if float(transaction_data.get('total_quantity', 0) or 0) > 0:
                avg_price = abs(float(transaction_data.get('total_amount', 0) or 0)) / float(transaction_data.get('total_quantity', 0) or 1)
            
            # 直接使用SQL插入分单记录
            direct_split_sql = """
                INSERT INTO transaction_splits (
                    original_transaction_id, holder_id, holder_name, split_ratio,
                    transaction_date, stock_code, market, stock_name,
                    transaction_type, total_quantity, total_amount,
                    broker_fee, stamp_duty, transaction_levy,
                    trading_fee, deposit_fee, transaction_code, 
                    prev_quantity, prev_cost, prev_avg_cost,
                    current_quantity, current_cost, current_avg_cost,
                    total_fees, net_amount, realized_profit,
                    profit_rate, avg_price, stock_id,
                    running_quantity, running_cost, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s
                )
            """
            
            direct_split_params = [
                original_transaction_id,  # original_transaction_id
                actual_holder_id,  # holder_id
                holder_name,  # holder_name
                split_ratio,  # split_ratio
                transaction_data['transaction_date'],  # transaction_date
                transaction_data['stock_code'],  # stock_code
                transaction_data['market'],  # market
                stock_name,  # stock_name
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
                avg_price,  # avg_price
                stock_id,  # stock_id
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
                        transaction_data, prev_state
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
                else:
                    update_sql = """
                        UPDATE stock_transactions
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