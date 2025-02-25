from flask import Blueprint, request, session, jsonify, make_response
from routes.auth import login_required
from config.database import db
from datetime import datetime
from services.currency_checker import CurrencyChecker
from models import Stock, StockTransaction
from models.exchange import ExchangeRate
import logging
import json
from sqlalchemy import text
from services.transaction_calculator import TransactionCalculator

stock_bp = Blueprint('stock', __name__)
checker = CurrencyChecker()
logger = logging.getLogger(__name__)

@stock_bp.route('/transactions/')
@login_required
def get_transactions():
    """获取交易记录列表"""
    try:
        # 获取查询参数
        user_id = session.get('user_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        market = request.args.get('market')
        stock_codes = request.args.getlist('stock_codes[]')
        transaction_code = request.args.get('transaction_code')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # 构建查询条件
        conditions = ["t.user_id = %s"]
        params = [user_id]
        
        if start_date:
            conditions.append("t.transaction_date >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("t.transaction_date <= %s")
            params.append(end_date)
        if market:
            conditions.append("t.market = %s")
            params.append(market)
        if stock_codes:
            placeholders = ','.join(['%s'] * len(stock_codes))
            conditions.append(f"t.stock_code IN ({placeholders})")
            params.extend(stock_codes)
        if transaction_code:
            conditions.append("t.transaction_code LIKE %s")
            params.append(f"%{transaction_code}%")
            
        where_clause = " AND ".join(conditions)
        
        # 计算总记录数
        count_sql = f"""
            SELECT COUNT(*) as total
            FROM stock.stock_transactions t
            WHERE {where_clause}
        """
        total = db.fetch_one(count_sql, params)
        total_count = total['total']
        total_pages = (total_count + per_page - 1) // per_page
        
        # 获取分页数据
        offset = (page - 1) * per_page
        
        # 主查询SQL
        main_sql = f"""
            SELECT 
                t.id,
                t.transaction_date,
                t.market,
                t.stock_code,
                s.code_name as stock_name,
                t.transaction_code,
                t.transaction_type,
                t.total_quantity,
                t.total_amount,
                t.broker_fee,
                t.transaction_levy,
                t.stamp_duty,
                t.trading_fee,
                t.deposit_fee,
                (t.broker_fee + t.transaction_levy + t.stamp_duty + t.trading_fee + t.deposit_fee) as total_fees,
                CASE 
                    WHEN t.transaction_type = 'buy' THEN 
                        t.total_amount + (t.broker_fee + t.transaction_levy + t.stamp_duty + t.trading_fee + t.deposit_fee)
                    ELSE 
                        t.total_amount - (t.broker_fee + t.transaction_levy + t.stamp_duty + t.trading_fee + t.deposit_fee)
                END as net_amount
            FROM stock.stock_transactions t
            LEFT JOIN stock.stocks s ON t.stock_code = s.code AND t.market = s.market
            WHERE {where_clause}
            ORDER BY t.transaction_date DESC, t.id DESC
            LIMIT %s OFFSET %s
        """
        params.extend([per_page, offset])
        transactions = db.fetch_all(main_sql, params)
        
        # 获取交易明细
        transaction_ids = [t['id'] for t in transactions]
        if transaction_ids:
            details_sql = """
                SELECT 
                    transaction_id,
                    quantity,
                    price
                FROM stock.stock_transaction_details
                WHERE transaction_id IN ({})
                ORDER BY id ASC
            """.format(','.join(['%s'] * len(transaction_ids)))
            
            details = db.fetch_all(details_sql, transaction_ids)
            
            # 将明细数据关联到主记录
            details_map = {}
            for detail in details:
                transaction_id = detail['transaction_id']
                if transaction_id not in details_map:
                    details_map[transaction_id] = []
                details_map[transaction_id].append({
                    'quantity': float(detail['quantity']),
                    'price': float(detail['price'])
                })
            
            # 添加明细到主记录
            for transaction in transactions:
                transaction['details'] = details_map.get(transaction['id'], [])
                # 转换数值类型
                transaction['total_quantity'] = float(transaction['total_quantity'])
                transaction['total_amount'] = float(transaction['total_amount'])
                transaction['broker_fee'] = float(transaction['broker_fee'])
                transaction['transaction_levy'] = float(transaction['transaction_levy'])
                transaction['stamp_duty'] = float(transaction['stamp_duty'])
                transaction['trading_fee'] = float(transaction['trading_fee'])
                transaction['deposit_fee'] = float(transaction['deposit_fee'])
                transaction['total_fees'] = float(transaction['total_fees'])
                transaction['net_amount'] = float(transaction['net_amount'])
                # 转换交易类型为大写
                transaction['transaction_type'] = transaction['transaction_type'].upper()
                # 格式化日期
                if isinstance(transaction['transaction_date'], datetime):
                    transaction['transaction_date'] = transaction['transaction_date'].strftime('%Y-%m-%d')
        
        return jsonify({
            'success': True,
            'data': {
                'items': transactions,
                'total': total_count,
                'page': page,
                'per_page': per_page,
                'pages': total_pages
            }
        })
        
    except Exception as e:
        logger.error(f"获取交易记录失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"获取交易记录失败: {str(e)}"
        }), 500

@stock_bp.route('/transactions', methods=['POST'])
@login_required
def add_transaction():
    """添加交易记录"""
    try:
        data = request.get_json()
        
        # 验证交易数据
        errors = TransactionCalculator.validate_transaction(data)
        if errors:
            return jsonify({
                'success': False,
                'message': '数据验证失败',
                'errors': errors
            }), 400
        
        # 获取交易前的持仓状态
        prev_state = TransactionCalculator.get_previous_state(
            db, session['user_id'], data['stock_code'],
            data['market'], data['transaction_date']
        )
        
        # 计算交易变化
        try:
            changes = TransactionCalculator.calculate_position_change(data, prev_state)
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
        
        # 开始事务
        db.execute("START TRANSACTION")
        
        try:
            # 插入交易记录
            insert_sql = """
                INSERT INTO stock.stock_transactions (
                    user_id, transaction_date, stock_code, market,
                    transaction_type, transaction_code, total_quantity,
                    total_amount, broker_fee, transaction_levy,
                    stamp_duty, trading_fee, deposit_fee, total_fees,
                    net_amount, prev_quantity, prev_cost, prev_avg_cost,
                    current_quantity, current_cost, current_avg_cost,
                    realized_pnl, realized_pnl_ratio, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, NOW(), NOW()
                )
            """
            
            params = [
                session['user_id'],
                data['transaction_date'],
                data['stock_code'],
                data['market'],
                data['transaction_type'].upper(),
                data.get('transaction_code', ''),
                data['total_quantity'],
                data['total_amount'],
                data.get('broker_fee', 0),
                data.get('transaction_levy', 0),
                data.get('stamp_duty', 0),
                data.get('trading_fee', 0),
                data.get('deposit_fee', 0),
                changes['total_fees'],
                changes['net_amount'],
                changes['prev_quantity'],
                changes['prev_cost'],
                changes['prev_avg_cost'],
                changes['current_quantity'],
                changes['current_cost'],
                changes['current_avg_cost'],
                changes['realized_pnl'],
                changes['realized_pnl_ratio']
            ]
            
            result = db.execute(insert_sql, params)
            if not result:
                db.execute("ROLLBACK")
                return jsonify({
                    'success': False,
                    'message': '添加交易记录失败'
                }), 500
            
            # 获取新插入记录的ID
            new_id = db.fetch_one("SELECT LAST_INSERT_ID() as id")['id']
            
            # 更新后续交易记录
            if not TransactionCalculator.update_subsequent_transactions(
                db, session['user_id'], data['stock_code'],
                data['market'], data['transaction_date'], new_id
            ):
                db.execute("ROLLBACK")
                return jsonify({
                    'success': False,
                    'message': '更新后续交易记录失败'
                }), 500
            
            # 提交事务
            db.execute("COMMIT")
            
            return jsonify({
                'success': True,
                'message': '添加交易记录成功',
                'data': {
                    'id': new_id,
                    'changes': changes
                }
            })
            
        except Exception as e:
            db.execute("ROLLBACK")
            raise e
            
    except Exception as e:
        logger.error(f'添加交易记录失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@stock_bp.route('/transactions/<int:id>', methods=['PUT'])
@login_required
def update_transaction(id):
    """更新交易记录"""
    try:
        data = request.get_json()
        
        # 验证交易数据
        errors = TransactionCalculator.validate_transaction(data)
        if errors:
            return jsonify({
                'success': False,
                'message': '数据验证失败',
                'errors': errors
            }), 400
        
        # 获取原始交易记录
        original_sql = """
            SELECT * FROM stock.stock_transactions 
            WHERE id = %s AND user_id = %s
        """
        transaction = db.fetch_one(original_sql, [id, session['user_id']])
        
        if not transaction:
            return jsonify({
                'success': False,
                'message': '交易记录不存在'
            }), 404
        
        # 获取交易前的持仓状态
        prev_state = TransactionCalculator.get_previous_state(
            db, session['user_id'], data['stock_code'],
            data['market'], data['transaction_date'], id
        )
        
        # 计算交易变化
        try:
            changes = TransactionCalculator.calculate_position_change(data, prev_state)
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
        
        # 开始事务
        db.execute("START TRANSACTION")
        
        try:
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
                    realized_pnl = %s,
                    realized_pnl_ratio = %s,
                    updated_at = NOW()
                WHERE id = %s AND user_id = %s
            """
            
            params = [
                data['transaction_date'],
                data['stock_code'],
                data['market'],
                data['transaction_type'].upper(),
                data.get('transaction_code', ''),
                data['total_amount'],
                data['total_quantity'],
                data.get('broker_fee', 0),
                data.get('transaction_levy', 0),
                data.get('stamp_duty', 0),
                data.get('trading_fee', 0),
                data.get('deposit_fee', 0),
                changes['total_fees'],
                changes['net_amount'],
                changes['prev_quantity'],
                changes['prev_cost'],
                changes['prev_avg_cost'],
                changes['current_quantity'],
                changes['current_cost'],
                changes['current_avg_cost'],
                changes['realized_pnl'],
                changes['realized_pnl_ratio'],
                id,
                session['user_id']
            ]
            
            result = db.execute(update_sql, params)
            if not result:
                db.execute("ROLLBACK")
                return jsonify({
                    'success': False,
                    'message': '更新交易记录失败'
                }), 500
            
            # 更新后续交易记录
            if not TransactionCalculator.update_subsequent_transactions(
                db, session['user_id'], data['stock_code'],
                data['market'], data['transaction_date'], id
            ):
                db.execute("ROLLBACK")
                return jsonify({
                    'success': False,
                    'message': '更新后续交易记录失败'
                }), 500
            
            # 提交事务
            db.execute("COMMIT")
            
            return jsonify({
                'success': True,
                'message': '更新交易记录成功',
                'data': {
                    'changes': changes
                }
            })
            
        except Exception as e:
            db.execute("ROLLBACK")
            raise e
            
    except Exception as e:
        logger.error(f'更新交易记录失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@stock_bp.route('/transactions/<int:id>', methods=['DELETE'])
@login_required
def delete_transaction(id):
    """删除交易记录"""
    try:
        # 获取要删除的交易记录
        transaction_sql = """
            SELECT * FROM stock.stock_transactions 
            WHERE id = %s AND user_id = %s
        """
        transaction = db.fetch_one(transaction_sql, [id, session['user_id']])
        
        if not transaction:
            return jsonify({
                'success': False,
                'message': '交易记录不存在'
            }), 404
        
        # 获取该交易之前的持仓状态
        prev_state = TransactionCalculator.get_previous_state(
            db, session['user_id'], transaction['stock_code'],
            transaction['market'], transaction['transaction_date'], id
        )
        
        # 开始事务
        db.execute("START TRANSACTION")
        
        try:
            # 删除交易记录
            delete_sql = """
                DELETE FROM stock.stock_transactions 
                WHERE id = %s AND user_id = %s
            """
            result = db.execute(delete_sql, [id, session['user_id']])
            
            if not result:
                db.execute("ROLLBACK")
                return jsonify({
                    'success': False,
                    'message': '删除交易记录失败'
                }), 500
            
            # 更新后续交易记录
            if not TransactionCalculator.update_subsequent_transactions(
                db, session['user_id'], transaction['stock_code'],
                transaction['market'], transaction['transaction_date'], id
            ):
                db.execute("ROLLBACK")
                return jsonify({
                    'success': False,
                    'message': '更新后续交易记录失败'
                }), 500
            
            # 提交事务
            db.execute("COMMIT")
            
            return jsonify({
                'success': True,
                'message': '删除交易记录成功'
            })
            
        except Exception as e:
            db.execute("ROLLBACK")
            raise e
            
    except Exception as e:
        logger.error(f'删除交易记录失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@stock_bp.route('/transactions/logs', methods=['GET'])
@login_required
def get_transaction_logs():
    """获取交易日志"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        market = request.args.get('market')
        stock_code = request.args.get('stock_code')
        transaction_type = request.args.get('transaction_type')
        
        # 构建SQL查询
        sql = """
            WITH base_transactions AS (
                SELECT 
                    t.*,
                    s.code_name as stock_name,
                    (t.broker_fee + t.transaction_levy + t.stamp_duty + t.trading_fee + t.deposit_fee) as total_fees_hkd
                FROM stock.stock_transactions t
                LEFT JOIN stock.stocks s ON t.stock_code = s.code AND t.market = s.market
                WHERE t.user_id = %s
                ORDER BY t.market, t.stock_code, t.transaction_date, t.id
            ),
            running_totals AS (
                SELECT 
                    t1.*,
                    @prev_qty := IF(
                        @current_stock = CONCAT(t1.market, t1.stock_code),
                        @qty,
                        0
                    ) as prev_qty,
                    @prev_cost := IF(
                        @current_stock = CONCAT(t1.market, t1.stock_code),
                        @cost,
                        0
                    ) as prev_cost,
                    @prev_avg_cost := IF(
                        @current_stock = CONCAT(t1.market, t1.stock_code) AND @qty > 0,
                        @cost / @qty,
                        IF(
                            @current_stock = CONCAT(t1.market, t1.stock_code),
                            @prev_avg_cost,
                            0
                        )
                    ) as prev_avg_cost,
                    @qty := IF(
                        @current_stock = CONCAT(t1.market, t1.stock_code),
                        IF(
                            t1.transaction_type = 'buy',
                            @qty + t1.total_quantity,
                            @qty - t1.total_quantity
                        ),
                        IF(
                            t1.transaction_type = 'buy',
                            t1.total_quantity,
                            -t1.total_quantity
                        )
                    ) as qty_running,
                    @cost := IF(
                        @current_stock = CONCAT(t1.market, t1.stock_code),
                        IF(
                            t1.transaction_type = 'buy',
                            @cost + t1.total_amount + t1.broker_fee + t1.transaction_levy + t1.stamp_duty + t1.trading_fee + t1.deposit_fee,
                            IF(@qty - t1.total_quantity > 0, @cost * ((@qty - t1.total_quantity) / @qty), 0)
                        ),
                        IF(
                            t1.transaction_type = 'buy',
                            t1.total_amount + t1.broker_fee + t1.transaction_levy + t1.stamp_duty + t1.trading_fee + t1.deposit_fee,
                            0
                        )
                    ) as cost_running,
                    @current_stock := CONCAT(t1.market, t1.stock_code) as _group_key
                FROM (
                    SELECT @qty := 0, @cost := 0, @current_stock := '', @prev_qty := 0, @prev_cost := 0, @prev_avg_cost := 0
                ) vars, base_transactions t1
            )
            SELECT 
                t.id,
                t.market,
                t.stock_code,
                t.stock_name,
                t.transaction_type,
                t.transaction_date,
                t.transaction_code,
                t.total_amount,
                t.total_quantity,
                t.exchange_rate,
                t.broker_fee,
                t.stamp_duty,
                t.transaction_levy,
                t.trading_fee,
                t.deposit_fee,
                t.total_fees_hkd,
                GROUP_CONCAT(
                    CONCAT(
                        COALESCE(td.quantity, ''),
                        '@',
                        COALESCE(td.price, ''),
                        '@',
                        COALESCE(td.quantity * td.price, '')
                    ) ORDER BY td.id ASC
                ) as detail_info,
                t.qty_running as current_quantity,
                CASE 
                    WHEN t.qty_running > 0 THEN t.cost_running / t.qty_running
                    ELSE 0
                END as current_average_cost,
                CASE 
                    WHEN t.transaction_type = 'sell' THEN t.prev_avg_cost
                    ELSE NULL
                END as sold_average_cost
            FROM running_totals t
            LEFT JOIN stock.stock_transaction_details td ON t.id = td.transaction_id
            GROUP BY 
                t.id, t.market, t.stock_code, t.stock_name, t.transaction_type,
                t.transaction_date, t.transaction_code, t.total_amount, t.total_quantity,
                t.exchange_rate, t.broker_fee, t.stamp_duty, t.transaction_levy,
                t.trading_fee, t.deposit_fee, t.total_fees_hkd,
                t.qty_running, t.cost_running, t.prev_qty, t.prev_cost, t.prev_avg_cost
            ORDER BY t.transaction_date DESC, t.id DESC
        """
        params = [session['user_id']]
        
        if start_date:
            sql += " AND t.transaction_date >= %s"
            params.append(start_date)
        if end_date:
            sql += " AND t.transaction_date <= %s"
            params.append(end_date)
        if market:
            sql += " AND t.market = %s"
            params.append(market)
        if stock_code:
            sql += " AND t.stock_code = %s"
            params.append(stock_code)
        if transaction_type:
            sql += " AND t.transaction_type = %s"
            params.append(transaction_type)
            
        # 获取总记录数
        count_sql = f"SELECT COUNT(*) as total FROM ({sql}) as temp"
        total_result = db.fetch_one(count_sql, params)
        total = total_result['total'] if total_result else 0
        
        # 添加排序和分页
        sql += " ORDER BY t.transaction_date DESC LIMIT %s OFFSET %s"
        params.extend([per_page, (page - 1) * per_page])
        
        # 执行查询
        logs = db.fetch_all(sql, params)
        
        # 获取当前页面涉及的股票的累计持仓情况
        if logs:
            stock_codes = list(set(log['stock_code'] for log in logs))
            placeholders = ','.join(['%s'] * len(stock_codes))
            
            position_sql = f"""
                SELECT 
                    stock_code,
                    SUM(CASE WHEN transaction_type = 'buy' THEN quantity ELSE -quantity END) as total_quantity,
                    SUM(CASE WHEN transaction_type = 'buy' THEN quantity * price ELSE -quantity * price END) as total_amount
                FROM stock_transactions
                WHERE user_id = %s AND stock_code IN ({placeholders})
                GROUP BY stock_code
            """
            position_params = [session['user_id']] + stock_codes
            positions = db.fetch_all(position_sql, position_params)
            position_map = {p['stock_code']: p for p in positions}
            
            # 添加累计持仓信息到日志中
            for log in logs:
                position = position_map.get(log['stock_code'], {})
                log['cumulative_quantity'] = position.get('total_quantity', 0)
                log['cumulative_amount'] = position.get('total_amount', 0)
        
        return jsonify({
            'success': True,
            'data': {
                'items': logs,
                'total': total,
                'pages': (total + per_page - 1) // per_page,
                'current_page': page
            }
        })
        
    except Exception as e:
        logger.error(f"获取交易日志失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取交易日志失败: {str(e)}'
        }), 500

@stock_bp.route('/stocks')
@login_required
def get_stocks():
    """获取股票列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 15, type=int)
        market = request.args.get('market')
        search = request.args.get('search')
        
        # 构建SQL查询
        sql = "SELECT * FROM stocks WHERE 1=1"
        params = []
        
        if market:
            sql += " AND market = %s"
            params.append(market)
            
        if search:
            sql += " AND (code LIKE %s OR code_name LIKE %s)"
            search_pattern = f'%{search}%'
            params.extend([search_pattern, search_pattern])
            
        # 计算总记录数
        count_sql = sql.replace("SELECT *", "SELECT COUNT(*)")
        total_result = db.fetch_one(count_sql, params)
        total = total_result['COUNT(*)'] if total_result else 0
        
        # 添加排序和分页
        sql += " ORDER BY market, code LIMIT %s OFFSET %s"
        params.extend([per_page, (page - 1) * per_page])
        
        # 执行查询
        stocks = db.fetch_all(sql, params)
            
        return jsonify({
            'success': True,
            'data': {
                'items': [Stock(item).to_dict() for item in stocks],
                'total': total,
                'pages': (total + per_page - 1) // per_page,
                'current_page': page
            }
        })
        
    except Exception as e:
        logger.error(f"获取股票列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取股票列表失败: {str(e)}'
        }), 500

@stock_bp.route('/stocks', methods=['POST'])
@login_required
def add_stock():
    """添加股票"""
    try:
        data = request.get_json()
        logger.info(f"接收到添加股票请求，数据：{data}")
        
        # 验证必填字段
        required_fields = ['code', 'market', 'code_name']
        for field in required_fields:
            if not data.get(field):
                logger.error(f"添加股票失败：缺少必填字段 {field}")
                return jsonify({
                    'success': False,
                    'message': f'缺少必填字段：{field}'
                }), 400
        
        # 检查是否已存在相同代码的股票
        check_sql = "SELECT id FROM stock.stocks WHERE code = %s AND market = %s"
        existing = db.fetch_one(check_sql, [data['code'], data['market']])
        if existing:
            logger.error(f"添加股票失败：股票代码 {data['code']} 在市场 {data['market']} 已存在")
            return jsonify({
                'success': False,
                'message': f"股票代码 {data['code']} 在市场 {data['market']} 已存在"
            }), 400
        
        # 创建股票对象
        stock = Stock({
            'code': data['code'].strip(),
            'market': data['market'].strip(),
            'code_name': data['code_name'].strip(),
            'google_name': data.get('google_name', '').strip()
        })
        
        # 保存到数据库
        logger.info(f"开始保存股票：{stock.to_dict()}")
        if stock.save():
            logger.info("股票添加成功")
            return jsonify({
                'success': True,
                'message': '股票添加成功',
                'data': stock.to_dict()
            })
        else:
            logger.error("股票添加失败：数据库保存失败")
            return jsonify({
                'success': False,
                'message': '添加失败：数据库保存失败'
            }), 500
            
    except Exception as e:
        logger.error(f"添加股票失败：{str(e)}")
        return jsonify({
            'success': False,
            'message': f'添加失败：{str(e)}'
        }), 500

@stock_bp.route('/stocks/<int:id>', methods=['PUT'])
@login_required
def edit_stock(id):
    """编辑股票"""
    try:
        data = request.get_json()
        
        # 查找股票记录
        sql = "SELECT * FROM stocks WHERE id = %s"
        stock_data = db.fetch_one(sql, (id,))
        if not stock_data:
            return jsonify({
                'success': False,
                'message': '股票不存在'
            }), 404
            
        stock = Stock(stock_data)
        stock.code = data['code']
        stock.market = data['market']
        stock.code_name = data['code_name']
        stock.google_name = data.get('google_name')
        stock.industry = data.get('industry')
        stock.currency = data.get('currency')
        
        if stock.save():
            return jsonify({
                'success': True,
                'message': '股票更新成功',
                'data': stock.to_dict()
            })
        else:
            return jsonify({
                'success': False,
                'message': '更新失败'
            }), 500
            
    except Exception as e:
        logger.error(f'更新股票失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'更新失败：{str(e)}'
        }), 500

@stock_bp.route('/stocks/<int:id>', methods=['DELETE'])
@login_required
def delete_stock(id):
    """删除股票"""
    try:
        # 先检查股票是否存在
        sql = "SELECT * FROM stocks WHERE id = %s"
        stock = db.fetch_one(sql, (id,))
        if not stock:
            return jsonify({
                'success': False,
                'message': '股票不存在'
            }), 404
            
        # 删除股票
        sql = "DELETE FROM stocks WHERE id = %s"
        if db.execute(sql, (id,)):
            return jsonify({
                'success': True,
                'message': '股票删除成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '删除失败'
            }), 500
            
    except Exception as e:
        logger.error(f'删除股票失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'删除失败：{str(e)}'
        }), 500

@stock_bp.route('/stocks/update-prices', methods=['POST'])
@login_required
def update_stock_prices():
    """更新股票价格"""
    try:
        # 获取所有股票
        sql = "SELECT code, market FROM stocks"
        stocks = db.fetch_all(sql)
        
        updated_count = 0
        failed_count = 0
        
        for stock in stocks:
            try:
                market_code = 'HKG' if stock['market'] == 'HK' else stock['market']
                query = f"{stock['code']}:{market_code}"
                price_result = checker.get_exchange_rate(query)
                stock['current_price'] = float(price_result) if price_result is not None else 0
            except Exception as e:
                logger.error(f"获取股票 {query} 价格失败: {str(e)}")
                stock['current_price'] = 0
                
            try:
                # 更新股票价格
                update_sql = """
                    UPDATE stocks 
                    SET current_price = %s, 
                        price_updated_at = NOW() 
                    WHERE code = %s AND market = %s
                """
                if db.execute(update_sql, (stock['current_price'], stock['code'], stock['market'])):
                    updated_count += 1
            except Exception as e:
                failed_count += 1
                logger.error(f"更新股票 {stock['code']} 价格失败: {str(e)}")
        
        return jsonify({
            'success': True,
            'data': {
                'updated': updated_count,
                'failed': failed_count
            }
        })
        
    except Exception as e:
        logger.error(f"更新股票价格失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'更新股票价格失败: {str(e)}'
        }), 500

@stock_bp.route('/check_price')
@login_required
def check_stock_price():
    """检查股票价格"""
    try:
        code = request.args.get('code')
        
        if not code:
            return jsonify({
                'success': False,
                'message': '请提供股票代码'
            }), 400

        # 如果是纯数字,先尝试港股市场
        if code.isdigit():
            # 如果是5位数,去除首位
            if len(code) == 5:
                code = code[1:]
            # 补齐到4位
            padded_code = code.zfill(4)
            query = f"{padded_code}:HKG"
            result = checker.get_exchange_rate(query)
            if result and result.get('price') is not None:
                return jsonify({
                    'success': True,
                    'data': {
                        'price': result['price'],
                        'name': result['name'],
                        'market': 'HK',
                        'google_code': query
                    }
                })

        # 尝试美股市场
        us_markets = ['NASDAQ', 'NYSE', 'NYSEAMERICAN']
        for market in us_markets:
            query = f"{code}:{market}"
            result = checker.get_exchange_rate(query)
            if result and result.get('price') is not None:
                return jsonify({
                    'success': True,
                    'data': {
                        'price': result['price'],
                        'name': result['name'],
                        'market': 'USA',
                        'google_code': query
                    }
                })

        return jsonify({
            'success': False,
            'message': '未找到股票信息'
        }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'message': '检查股票价格失败'
        }), 500

@stock_bp.route('/exchange_rates')
@login_required
def get_exchange_rates():
    """获取汇率列表"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 15))
        currency = request.args.get('currency')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 构建SQL查询
        sql = """
            SELECT * FROM exchange_rates 
            WHERE 1=1
        """
        params = []
        
        if currency:
            sql += " AND currency = %s"
            params.append(currency)
        if start_date:
            sql += " AND rate_date >= %s"
            params.append(start_date)
        if end_date:
            sql += " AND rate_date <= %s"
            params.append(end_date)
            
        # 计算总记录数
        count_sql = sql.replace("*", "COUNT(*)")
        total = db.fetch_one(count_sql, params)
        total_count = total['COUNT(*)'] if total else 0
        
        # 添加排序和分页
        sql += " ORDER BY rate_date DESC, currency"
        sql += " LIMIT %s OFFSET %s"
        offset = (page - 1) * per_page
        params.extend([per_page, offset])
        
        # 获取数据
        rates = db.fetch_all(sql, params)
        
        return jsonify({
            'success': True,
            'data': {
                'items': [ExchangeRate(rate).to_dict() for rate in rates],
                'total': total_count,
                'page': page,
                'per_page': per_page,
                'pages': (total_count + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        logger.error(f"获取汇率列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取汇率列表失败: {str(e)}'
        }), 500

@stock_bp.route('/exchange_rates', methods=['POST'])
@login_required
def add_exchange_rate():
    """添加汇率记录"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['currency', 'rate', 'rate_date']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'缺少必填字段: {field}'
                }), 400
        
        # 检查是否已存在相同日期的汇率记录
        existing = ExchangeRate.find_by_date(data['currency'], data['rate_date'])
        if existing:
            return jsonify({
                'success': False,
                'message': '该日期的汇率记录已存在'
            }), 400
        
        # 创建新记录
        rate = ExchangeRate(data)
        if rate.save():
            return jsonify({
                'success': True,
                'message': '添加汇率记录成功',
                'data': rate.to_dict()
            })
        else:
            return jsonify({
                'success': False,
                'message': '添加汇率记录失败'
            }), 500
        
    except Exception as e:
        logger.error(f"添加汇率记录失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'添加汇率记录失败: {str(e)}'
        }), 500

@stock_bp.route('/exchange_rates/<int:id>', methods=['PUT'])
@login_required
def update_exchange_rate(id):
    """更新汇率记录"""
    try:
        data = request.get_json()
        
        # 查找记录
        sql = "SELECT * FROM exchange_rates WHERE id = %s"
        rate_data = db.fetch_one(sql, (id,))
        if not rate_data:
            return jsonify({
                'success': False,
                'message': '汇率记录不存在'
            }), 404
        
        rate = ExchangeRate(rate_data)
        
        # 更新字段
        if 'rate' in data:
            rate.rate = data['rate']
        if 'source' in data:
            rate.source = data['source']
        
        if rate.save():
            return jsonify({
                'success': True,
                'message': '更新汇率记录成功',
                'data': rate.to_dict()
            })
        else:
            return jsonify({
                'success': False,
                'message': '更新汇率记录失败'
            }), 500
        
    except Exception as e:
        logger.error(f"更新汇率记录失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'更新汇率记录失败: {str(e)}'
        }), 500

@stock_bp.route('/exchange_rates/<int:id>', methods=['DELETE'])
@login_required
def delete_exchange_rate(id):
    """删除汇率记录"""
    try:
        # 查找记录
        sql = "SELECT * FROM exchange_rates WHERE id = %s"
        rate = db.fetch_one(sql, (id,))
        if not rate:
            return jsonify({
                'success': False,
                'message': '汇率记录不存在'
            }), 404
        
        # 删除记录
        delete_sql = "DELETE FROM exchange_rates WHERE id = %s"
        if db.execute(delete_sql, (id,)):
            return jsonify({
                'success': True,
                'message': '删除汇率记录成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '删除汇率记录失败'
            }), 500
            
    except Exception as e:
        logger.error(f"删除汇率记录失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'删除汇率记录失败: {str(e)}'
        }), 500

@stock_bp.route('/transactions/<int:id>', methods=['GET'])
@login_required
def get_transaction(id):
    """获取单个交易记录"""
    try:
        # 主查询SQL
        sql = """
            SELECT 
                t.id,
                t.transaction_date,
                t.market,
                t.stock_code,
                s.code_name as stock_name,
                t.transaction_code,
                t.transaction_type,
                t.total_quantity,
                t.total_amount,
                t.broker_fee,
                t.transaction_levy,
                t.stamp_duty,
                t.trading_fee,
                t.deposit_fee,
                (t.broker_fee + t.transaction_levy + t.stamp_duty + t.trading_fee + t.deposit_fee) as total_fees,
                CASE 
                    WHEN t.transaction_type = 'buy' THEN 
                        t.total_amount + (t.broker_fee + t.transaction_levy + t.stamp_duty + t.trading_fee + t.deposit_fee)
                    ELSE 
                        t.total_amount - (t.broker_fee + t.transaction_levy + t.stamp_duty + t.trading_fee + t.deposit_fee)
                END as net_amount
            FROM stock.stock_transactions t
            LEFT JOIN stock.stocks s ON t.stock_code = s.code AND t.market = s.market
            WHERE t.id = %s AND t.user_id = %s
        """
        transaction = db.fetch_one(sql, [id, session['user_id']])
        
        if not transaction:
            return jsonify({
                'success': False,
                'message': '交易记录不存在或无权限查看'
            }), 404
            
        # 获取交易明细
        details_sql = """
            SELECT quantity, price
            FROM stock.stock_transaction_details
            WHERE transaction_id = %s
            ORDER BY id ASC
        """
        details = db.fetch_all(details_sql, [id])
        
        # 转换数据类型
        transaction['total_quantity'] = float(transaction['total_quantity'])
        transaction['total_amount'] = float(transaction['total_amount'])
        transaction['broker_fee'] = float(transaction['broker_fee'])
        transaction['transaction_levy'] = float(transaction['transaction_levy'])
        transaction['stamp_duty'] = float(transaction['stamp_duty'])
        transaction['trading_fee'] = float(transaction['trading_fee'])
        transaction['deposit_fee'] = float(transaction['deposit_fee'])
        transaction['total_fees'] = float(transaction['total_fees'])
        transaction['net_amount'] = float(transaction['net_amount'])
        
        # 转换交易类型为大写
        transaction['transaction_type'] = transaction['transaction_type'].upper()
        
        # 格式化日期
        if isinstance(transaction['transaction_date'], datetime):
            transaction['transaction_date'] = transaction['transaction_date'].strftime('%Y-%m-%d')
            
        # 添加明细数据
        transaction['details'] = [{
            'quantity': float(detail['quantity']),
            'price': float(detail['price'])
        } for detail in details]
        
        return jsonify({
            'success': True,
            'data': transaction
        })
        
    except Exception as e:
        logger.error(f"获取交易记录失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取交易记录失败: {str(e)}'
        }), 500

@stock_bp.route('/profit/')
@login_required
def get_profit_stats():
    """获取盈利统计数据"""
    try:
        # 1. 获取查询参数
        user_id = session.get('user_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        market = request.args.get('market')

        # 2. 构建查询条件
        conditions = ['t.user_id = %s']
        params = [user_id]

        if start_date:
            conditions.append('t.transaction_date >= %s')
            params.append(start_date)
        if end_date:
            conditions.append('t.transaction_date <= %s')
            params.append(end_date)
        if market:
            conditions.append('t.market = %s')
            params.append(market)

        where_clause = ' AND '.join(conditions)

        # 3. 获取交易数据
        sql = f"""
            WITH transaction_summary AS (
                SELECT 
                    t.market,
                    t.stock_code,
                    s.code_name as stock_name,
                    t.transaction_type,
                    SUM(t.total_quantity) as total_quantity,
                    SUM(t.total_amount) as total_amount,
                    SUM(t.broker_fee + t.transaction_levy + t.stamp_duty + t.trading_fee + t.deposit_fee) as total_fees,
                    COUNT(*) as transaction_count
                FROM stock.stock_transactions t
                LEFT JOIN stock.stocks s ON t.stock_code = s.code AND t.market = s.market
                WHERE {where_clause}
                GROUP BY t.market, t.stock_code, s.code_name, t.transaction_type
            )
            SELECT * FROM transaction_summary
            ORDER BY market, stock_code, transaction_type
        """

        transactions = db.fetch_all(sql, params)

        # 4. 处理数据
        market_stats = {}  # 市场级别统计
        stock_stats = {}   # 股票级别统计
        
        # 5. 计算统计数据
        for trans in transactions:
            market = trans['market']
            stock_code = trans['stock_code']
            key = f"{market}-{stock_code}"
            
            # 初始化股票统计
            if key not in stock_stats:
                stock_stats[key] = {
                    'market': market,
                    'code': stock_code,
                    'name': trans['stock_name'],
                    'buy_count': 0,
                    'sell_count': 0,
                    'buy_quantity': 0,
                    'sell_quantity': 0,
                    'buy_amount': 0,
                    'sell_amount': 0,
                    'total_fees': 0,
                    'realized_profit': 0,
                    'current_price': 0,
                    'market_value': 0,
                    'unrealized_profit': 0,
                    'total_profit': 0,
                    'profit_rate': 0
                }

            # 初始化市场统计
            if market not in market_stats:
                market_stats[market] = {
                    'buy_count': 0,
                    'sell_count': 0,
                    'buy_amount': 0,
                    'sell_amount': 0,
                    'total_fees': 0,
                    'realized_profit': 0,
                    'market_value': 0,
                    'unrealized_profit': 0,
                    'total_profit': 0,
                    'profit_rate': 0
                }

            # 更新统计数据
            if trans['transaction_type'] == 'BUY':
                stock_stats[key]['buy_count'] += trans['transaction_count']
                stock_stats[key]['buy_quantity'] += trans['total_quantity']
                stock_stats[key]['buy_amount'] += trans['total_amount']
                market_stats[market]['buy_count'] += trans['transaction_count']
                market_stats[market]['buy_amount'] += trans['total_amount']
            else:  # SELL
                stock_stats[key]['sell_count'] += trans['transaction_count']
                stock_stats[key]['sell_quantity'] += trans['total_quantity']
                stock_stats[key]['sell_amount'] += trans['total_amount']
                market_stats[market]['sell_count'] += trans['transaction_count']
                market_stats[market]['sell_amount'] += trans['total_amount']

            stock_stats[key]['total_fees'] += trans['total_fees']
            market_stats[market]['total_fees'] += trans['total_fees']

        # 6. 计算持仓数量和盈亏数据
        holding_stocks = {}
        closed_stocks = {}

        for key, stock in stock_stats.items():
            # 计算持仓数量
            quantity = stock['buy_quantity'] - stock['sell_quantity']
            stock['quantity'] = quantity

            # 计算平均成本
            if quantity > 0:
                stock['average_cost'] = stock['buy_amount'] / stock['buy_quantity']
            else:
                stock['average_cost'] = 0

            # 获取当前股价
            try:
                market_code = 'HKG' if stock['market'] == 'HK' else stock['market']
                query = f"{stock['code']}:{market_code}"
                price_result = checker.get_exchange_rate(query)
                stock['current_price'] = float(price_result) if price_result is not None else 0
            except Exception as e:
                logger.error(f"获取股票 {query} 价格失败: {str(e)}")
                stock['current_price'] = 0

            # 计算已实现盈亏
            if stock['sell_quantity'] > 0:
                avg_cost = stock['buy_amount'] / stock['buy_quantity'] if stock['buy_quantity'] > 0 else 0
                stock['realized_profit'] = stock['sell_amount'] - (stock['sell_quantity'] * avg_cost) - stock['total_fees']
            else:
                stock['realized_profit'] = -stock['total_fees']

            # 计算未实现盈亏
            stock['market_value'] = quantity * stock['current_price']
            stock['unrealized_profit'] = stock['market_value'] - (quantity * stock['average_cost']) if quantity > 0 else 0

            # 计算总盈亏和收益率
            stock['total_profit'] = stock['realized_profit'] + stock['unrealized_profit']
            stock['profit_rate'] = (stock['total_profit'] / stock['buy_amount'] * 100) if stock['buy_amount'] > 0 else 0

            # 更新市场统计数据
            market = stock['market']
            market_stats[market]['realized_profit'] += stock['realized_profit']
            market_stats[market]['market_value'] += stock['market_value']
            market_stats[market]['unrealized_profit'] += stock['unrealized_profit']
            market_stats[market]['total_profit'] += stock['total_profit']

            # 分类到持仓或已清仓
            if quantity > 0:
                holding_stocks[key] = stock
            else:
                closed_stocks[key] = stock

        # 7. 计算市场收益率
        for market, stats in market_stats.items():
            stats['profit_rate'] = (stats['total_profit'] / stats['buy_amount'] * 100) if stats['buy_amount'] > 0 else 0

        return jsonify({
            'success': True,
            'data': {
                'market_stats': market_stats,
                'holding_stocks': holding_stocks,
                'closed_stocks': closed_stocks
            }
        })

    except Exception as e:
        logger.error(f"获取盈利统计数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '获取盈利统计数据失败'
        })

@stock_bp.route('/stocks/search')
@login_required
def search_stocks():
    """搜索股票"""
    try:
        query = request.args.get('query', '').strip()
        if not query:
            return jsonify({
                'success': True,
                'data': []
            })

        # 构建SQL查询
        sql = """
            SELECT code, code_name as name, market
            FROM stock.stocks
            WHERE code LIKE %s OR code_name LIKE %s
            ORDER BY 
                CASE 
                    WHEN code = %s THEN 1
                    WHEN code LIKE %s THEN 2
                    WHEN code_name LIKE %s THEN 3
                    ELSE 4
                END,
                market,
                code
            LIMIT 10
        """
        
        # 准备查询参数
        exact_match = query
        prefix_match = f"{query}%"
        contains_match = f"%{query}%"
        
        params = [
            contains_match,  # code LIKE
            contains_match,  # name LIKE
            exact_match,    # code =
            prefix_match,   # code LIKE (prefix)
            prefix_match    # name LIKE (prefix)
        ]
        
        # 执行查询
        results = db.fetch_all(sql, params)
        
        return jsonify({
            'success': True,
            'data': results
        })
        
    except Exception as e:
        logger.error(f"搜索股票失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'搜索股票失败: {str(e)}'
        }), 500

@stock_bp.route('/transactions/check-code')
@login_required
def check_transaction_code():
    """检查交易编号是否已存在"""
    try:
        code = request.args.get('code')
        if not code:
            return jsonify({
                'success': False,
                'message': '请提供交易编号'
            }), 400

        # 查询数据库中是否存在相同的交易编号
        sql = """
            SELECT COUNT(*) as count 
            FROM stock_transactions 
            WHERE user_id = %s AND transaction_code = %s
        """
        result = db.fetch_one(sql, [session['user_id'], code])
        
        return jsonify({
            'success': True,
            'exists': result['count'] > 0
        })
        
    except Exception as e:
        logger.error(f"检查交易编号失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'检查交易编号失败: {str(e)}'
        }), 500

@stock_bp.route('/search_stock')
@login_required
def search_stock():
    """搜索股票代码"""
    try:
        code = request.args.get('code')
        if not code:
            return jsonify({
                'success': False,
                'message': '请提供股票代码'
            }), 400

        # 添加时间戳和缓存控制
        response = make_response(jsonify({
            'success': True,
            'data': checker.search_stock(code)
        }))
        
        # 设置响应头以防止缓存
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response

    except Exception as e:
        logger.error(f"搜索股票失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'搜索股票失败: {str(e)}'
        }), 500 