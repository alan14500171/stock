from datetime import datetime
from decimal import Decimal
from .transaction_calculator import TransactionCalculator

class TransactionService:
    """交易服务类，处理交易记录的增加、编辑和删除操作"""
    
    @staticmethod
    def process_transaction(db, user_id, transaction_data, transaction_id=None, is_delete=False):
        """
        处理交易记录的通用函数
        
        Args:
            db: 数据库连接
            user_id: 用户ID
            transaction_data: 交易数据
            transaction_id: 交易ID（编辑或删除时使用）
            is_delete: 是否为删除操作
        
        Returns:
            tuple: (success, result, status_code)
        """
        try:
            # 验证交易数据（仅添加和编辑时需要）
            if not is_delete:
                errors = TransactionCalculator.validate_transaction(transaction_data)
                if errors:
                    return False, {'message': '数据验证失败', 'errors': errors}, 400
            
            # 获取交易前的持仓状态
            prev_state = TransactionCalculator.get_previous_state(
                db, user_id, 
                transaction_data.get('stock_code') if not is_delete else transaction_data['stock_code'],
                transaction_data.get('market') if not is_delete else transaction_data['market'],
                transaction_data.get('transaction_date') if not is_delete else transaction_data['transaction_date'],
                transaction_id
            )
            
            # 计算交易变化（仅添加和编辑时需要）
            changes = None
            if not is_delete:
                try:
                    changes = TransactionCalculator.calculate_position_change(transaction_data, prev_state)
                except ValueError as e:
                    return False, {'message': str(e)}, 400
            
            # 开始事务
            db.execute("START TRANSACTION")
            
            try:
                result = None
                
                # 根据操作类型执行不同的数据库操作
                if is_delete:
                    # 删除操作
                    success, result = TransactionService._handle_delete(
                        db, user_id, transaction_id, transaction_data, prev_state
                    )
                    if not success:
                        db.execute("ROLLBACK")
                        return False, result, 500
                
                elif transaction_id:  # 编辑操作
                    success, result = TransactionService._handle_update(
                        db, user_id, transaction_id, transaction_data, changes
                    )
                    if not success:
                        db.execute("ROLLBACK")
                        return False, result, 500
                    
                else:  # 添加操作
                    success, result = TransactionService._handle_insert(
                        db, user_id, transaction_data, changes
                    )
                    if not success:
                        db.execute("ROLLBACK")
                        return False, result, 500
                
                # 提交事务
                db.execute("COMMIT")
                
                # 更新running_quantity和running_cost字段
                try:
                    from scripts.update_running_fields import update_running_fields
                    
                    # 获取需要更新的参数
                    if is_delete:
                        # 删除操作，更新该股票在删除日期及之后的记录
                        update_running_fields(
                            user_id=user_id,
                            stock_code=transaction_data['stock_code'],
                            market=transaction_data['market'],
                            transaction_date=transaction_data['transaction_date']
                        )
                    else:
                        # 添加或编辑操作，更新该股票在交易日期及之后的记录
                        update_running_fields(
                            user_id=user_id,
                            stock_code=transaction_data['stock_code'],
                            market=transaction_data['market'],
                            transaction_date=transaction_data['transaction_date']
                        )
                except Exception:
                    pass
                
                return True, result, 200
                
            except Exception as e:
                db.execute("ROLLBACK")
                raise e
                
        except Exception as e:
            return False, {'message': f'处理交易记录失败: {str(e)}'}, 500
    
    @staticmethod
    def _handle_delete(db, user_id, transaction_id, transaction_data, prev_state):
        """处理删除交易记录"""
        # 使用事务确保主记录和明细记录的一致性
        with db.get_connection() as connection:
            try:
                # 关闭自动提交，开始事务
                connection.autocommit = False
                
                with connection.cursor() as cursor:
                    # 先删除交易明细记录
                    cursor.execute("DELETE FROM stock.stock_transaction_details WHERE transaction_id = %s", [transaction_id])
                    
                    # 删除交易记录
                    cursor.execute("DELETE FROM stock.stock_transactions WHERE id = %s AND user_id = %s", 
                                  [transaction_id, user_id])
                
                # 提交事务
                connection.commit()
                
                # 更新后续交易记录
                TransactionCalculator.update_subsequent_transactions(
                    db, user_id, transaction_data['stock_code'],
                    transaction_data['market'], transaction_data['transaction_date'],
                    prev_state['id'] if prev_state and prev_state['id'] else 0
                )
                
                return True, {'message': '删除交易记录成功'}
                
            except Exception as e:
                # 回滚事务
                connection.rollback()
                return False, {'message': f'删除交易记录失败: {str(e)}'}
    
    @staticmethod
    def _handle_update(db, user_id, transaction_id, transaction_data, changes):
        """处理更新交易记录"""
        # 更新交易记录
        update_sql = """
            UPDATE stock.stock_transactions 
            SET transaction_date = %s,
                stock_code = %s,
                market = %s,
                transaction_type = %s,
                transaction_code = %s,
                total_amount = %s,
                total_quantity = %s,
                broker_fee = %s,
                transaction_levy = %s,
                stamp_duty = %s,
                trading_fee = %s,
                deposit_fee = %s,
                total_fees = %s,
                net_amount = %s,
                prev_quantity = %s,
                prev_cost = %s,
                prev_avg_cost = %s,
                current_quantity = %s,
                current_cost = %s,
                current_avg_cost = %s,
                realized_profit = %s,
                profit_rate = %s,
                updated_at = NOW()
            WHERE id = %s AND user_id = %s
        """
        
        params = [
            transaction_data['transaction_date'],
            transaction_data['stock_code'],
            transaction_data['market'],
            transaction_data['transaction_type'].lower(),
            transaction_data.get('transaction_code', ''),
            transaction_data['total_amount'],
            transaction_data['total_quantity'],
            transaction_data.get('broker_fee', 0),
            transaction_data.get('transaction_levy', 0),
            transaction_data.get('stamp_duty', 0),
            transaction_data.get('trading_fee', 0),
            transaction_data.get('deposit_fee', 0),
            changes['total_fees'],
            changes['net_amount'],
            changes['prev_quantity'],
            changes['prev_cost'],
            changes['prev_avg_cost'],
            changes['current_quantity'],
            changes['current_cost'],
            changes['current_avg_cost'],
            changes['realized_profit'],
            changes['profit_rate'],
            transaction_id,
            user_id
        ]
        
        # 使用事务确保主记录和明细记录的一致性
        with db.get_connection() as connection:
            try:
                # 关闭自动提交，开始事务
                connection.autocommit = False
                
                # 更新主交易记录
                with connection.cursor() as cursor:
                    cursor.execute(update_sql, params)
                    
                    # 先删除原有明细
                    cursor.execute("DELETE FROM stock.stock_transaction_details WHERE transaction_id = %s", [transaction_id])
                    
                    # 插入新的明细
                    if 'details' in transaction_data and transaction_data['details']:
                        for detail in transaction_data['details']:
                            detail_sql = """
                                INSERT INTO stock.stock_transaction_details
                                (transaction_id, quantity, price, created_at)
                                VALUES (%s, %s, %s, NOW())
                            """
                            detail_params = [transaction_id, detail['quantity'], detail['price']]
                            cursor.execute(detail_sql, detail_params)
                
                # 提交事务
                connection.commit()
                
                # 更新后续交易记录
                TransactionCalculator.update_subsequent_transactions(
                    db, user_id, transaction_data['stock_code'],
                    transaction_data['market'], transaction_data['transaction_date'],
                    transaction_id
                )
                
                return True, {'message': '更新交易记录成功', 'changes': changes}
                
            except Exception as e:
                # 回滚事务
                connection.rollback()
                return False, {'message': f'更新交易记录失败: {str(e)}'}
    
    @staticmethod
    def _handle_insert(db, user_id, transaction_data, changes):
        """处理插入交易记录"""
        # 插入交易记录
        insert_sql = """
            INSERT INTO stock.stock_transactions (
                user_id, transaction_date, stock_code, market,
                transaction_type, transaction_code, total_quantity,
                total_amount, broker_fee, transaction_levy,
                stamp_duty, trading_fee, deposit_fee, total_fees,
                net_amount, prev_quantity, prev_cost, prev_avg_cost,
                current_quantity, current_cost, current_avg_cost,
                realized_profit, profit_rate,
                created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, NOW(), NOW()
            )
        """
        
        params = [
            user_id,
            transaction_data['transaction_date'],
            transaction_data['stock_code'],
            transaction_data['market'],
            transaction_data['transaction_type'].lower(),
            transaction_data.get('transaction_code', ''),
            transaction_data['total_quantity'],
            transaction_data['total_amount'],
            transaction_data.get('broker_fee', 0),
            transaction_data.get('transaction_levy', 0),
            transaction_data.get('stamp_duty', 0),
            transaction_data.get('trading_fee', 0),
            transaction_data.get('deposit_fee', 0),
            changes['total_fees'],
            changes['net_amount'],
            changes['prev_quantity'],
            changes['prev_cost'],
            changes['prev_avg_cost'],
            changes['current_quantity'],
            changes['current_cost'],
            changes['current_avg_cost'],
            changes['realized_profit'],
            changes['profit_rate']
        ]
        
        # 使用事务确保主记录和明细记录的一致性
        with db.get_connection() as connection:
            try:
                # 关闭自动提交，开始事务
                connection.autocommit = False
                
                # 插入主交易记录
                with connection.cursor() as cursor:
                    cursor.execute(insert_sql, params)
                    new_id = cursor.lastrowid
                    
                    if not new_id:
                        connection.rollback()
                        return False, {'message': '添加交易记录失败'}
                    
                    # 处理交易明细
                    if 'details' in transaction_data and transaction_data['details']:
                        for detail in transaction_data['details']:
                            detail_sql = """
                                INSERT INTO stock.stock_transaction_details
                                (transaction_id, quantity, price, created_at)
                                VALUES (%s, %s, %s, NOW())
                            """
                            detail_params = [new_id, detail['quantity'], detail['price']]
                            cursor.execute(detail_sql, detail_params)
                
                # 提交事务
                connection.commit()
                
                # 更新后续交易记录
                TransactionCalculator.update_subsequent_transactions(
                    db, user_id, transaction_data['stock_code'],
                    transaction_data['market'], transaction_data['transaction_date'],
                    new_id
                )
                
                return True, {'message': '添加交易记录成功', 'id': new_id, 'changes': changes}
                
            except Exception as e:
                # 回滚事务
                connection.rollback()
                return False, {'message': f'添加交易记录失败: {str(e)}'}
    
    @staticmethod
    def _handle_transaction_details(db, transaction_id, transaction_data):
        """处理交易明细记录"""
        try:
            # 先删除原有明细
            db.execute("DELETE FROM stock.stock_transaction_details WHERE transaction_id = %s", [transaction_id])
            
            # 插入新的明细
            if 'details' in transaction_data and transaction_data['details']:
                with db.get_connection() as connection:
                    try:
                        # 关闭自动提交，开始事务
                        connection.autocommit = False
                        
                        with connection.cursor() as cursor:
                            for detail in transaction_data['details']:
                                detail_sql = """
                                    INSERT INTO stock.stock_transaction_details
                                    (transaction_id, quantity, price, created_at)
                                    VALUES (%s, %s, %s, NOW())
                                """
                                detail_params = [transaction_id, detail['quantity'], detail['price']]
                                cursor.execute(detail_sql, detail_params)
                        
                        # 提交事务
                        connection.commit()
                        return True
                    except Exception as e:
                        # 回滚事务
                        connection.rollback()
                        return False
                    finally:
                        # 恢复自动提交
                        connection.autocommit = True
            
            return True
        except Exception as e:
            return False
    
    @staticmethod
    def check_delete_validity(db, user_id, transaction_id):
        """
        检查删除交易记录的合法性
        
        Args:
            db: 数据库连接
            user_id: 用户ID
            transaction_id: 交易ID
            
        Returns:
            tuple: (is_valid, message, transaction)
        """
        # 获取要删除的交易记录
        transaction_sql = """
            SELECT * FROM stock.stock_transactions 
            WHERE id = %s AND user_id = %s
        """
        transaction = db.fetch_one(transaction_sql, [transaction_id, user_id])
        
        if not transaction:
            return False, '交易记录不存在', None
        
        # 如果是买入交易，检查删除后是否会导致后续卖出交易持仓不足
        if transaction['transaction_type'].lower() == 'buy':
            # 获取该交易之前的持仓状态
            prev_state = TransactionCalculator.get_previous_state(
                db, user_id, transaction['stock_code'],
                transaction['market'], transaction['transaction_date'], transaction_id
            )
            
            # 获取后续第一条卖出交易记录
            next_sell_sql = """
                SELECT * FROM stock.stock_transactions 
                WHERE user_id = %s 
                    AND stock_code = %s 
                    AND market = %s
                    AND transaction_type = 'sell'
                    AND (transaction_date > %s 
                         OR (transaction_date = %s AND id > %s))
                ORDER BY transaction_date ASC, id ASC
                LIMIT 1
            """
            next_sell = db.fetch_one(next_sell_sql, [
                user_id,
                transaction['stock_code'],
                transaction['market'],
                transaction['transaction_date'],
                transaction['transaction_date'],
                transaction_id
            ])
            
            # 如果有后续卖出交易，检查删除后的持仓是否足够
            if next_sell:
                # 计算删除后的持仓数量
                prev_quantity = float(prev_state.get('quantity', 0))
                
                # 获取要删除的交易到下一条卖出交易之间的所有买入交易
                interim_buys_sql = """
                    SELECT COALESCE(SUM(total_quantity), 0) as total_buys
                    FROM stock.stock_transactions 
                    WHERE user_id = %s 
                        AND stock_code = %s 
                        AND market = %s
                        AND transaction_type = 'buy'
                        AND id != %s
                        AND (
                            (transaction_date > %s AND transaction_date < %s)
                            OR (transaction_date = %s AND id > %s AND id < %s)
                            OR (transaction_date = %s AND id < %s)
                        )
                """
                interim_buys = db.fetch_one(interim_buys_sql, [
                    user_id,
                    transaction['stock_code'],
                    transaction['market'],
                    transaction_id,
                    transaction['transaction_date'],
                    next_sell['transaction_date'],
                    transaction['transaction_date'],
                    transaction_id,
                    next_sell['id'],
                    next_sell['transaction_date'],
                    next_sell['id']
                ])
                
                # 计算删除后的实际持仓
                current_quantity = prev_quantity - float(transaction['total_quantity']) + float(interim_buys['total_buys'])
                
                # 检查持仓是否足够支持下一次卖出
                if current_quantity < float(next_sell['total_quantity']):
                    return False, f'删除此买入记录后，持仓数量（{current_quantity}）将不足以支持后续的卖出交易（{next_sell["total_quantity"]}）', None
        
        return True, '', transaction
    
    @staticmethod
    def check_edit_validity(db, user_id, transaction_id, new_data):
        """
        检查编辑交易记录的合法性
        
        Args:
            db: 数据库连接
            user_id: 用户ID
            transaction_id: 交易ID
            new_data: 新的交易数据
            
        Returns:
            tuple: (is_valid, message, transaction)
        """
        # 获取原始交易记录
        original_sql = """
            SELECT * FROM stock.stock_transactions 
            WHERE id = %s AND user_id = %s
        """
        transaction = db.fetch_one(original_sql, [transaction_id, user_id])
        
        if not transaction:
            return False, '交易记录不存在', None
        
        # 检查交易日期是否变更
        date_changed = transaction['transaction_date'].strftime('%Y-%m-%d') != new_data['transaction_date']
        
        # 如果日期变更，需要验证新日期的合法性
        if date_changed:
            # 检查新日期是否会导致卖出时持仓不足
            prev_state = TransactionCalculator.get_previous_state(
                db, user_id, new_data['stock_code'],
                new_data['market'], new_data['transaction_date']
            )
            
            if new_data['transaction_type'].lower() == 'sell':
                total_quantity = float(new_data['total_quantity'])
                prev_quantity = float(prev_state.get('quantity', 0))
                
                if prev_quantity < total_quantity:
                    return False, f'交易日期变更后，该日期的持仓数量（{prev_quantity}）不足以支持卖出数量（{total_quantity}）', None
        
        return True, '', transaction 