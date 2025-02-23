from flask import Blueprint, jsonify, request, session
from routes.auth import login_required
from config.database import db
from datetime import datetime
from models import Stock, StockTransaction
from utils.exchange_rate import get_exchange_rate
from services.currency_checker import CurrencyChecker
import json
import logging

profit_bp = Blueprint('profit', __name__)
checker = CurrencyChecker()
logger = logging.getLogger(__name__)

@profit_bp.route('/')
@login_required
def get_profit_stats():
    """获取盈利统计数据"""
    try:
        # 1. 获取查询参数
        user_id = session.get('user_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        market = request.args.get('market')
        stock_codes = request.args.getlist('stock_codes[]')

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
        if stock_codes:
            placeholders = ','.join(['%s'] * len(stock_codes))
            conditions.append(f't.stock_code IN ({placeholders})')
            params.extend(stock_codes)

        where_clause = ' AND '.join(conditions)

        # 3. 获取交易明细数据
        details_sql = f"""
            WITH base_transactions AS (
                SELECT 
                    t.*,
                    s.name as stock_name,
                    (t.broker_fee + t.transaction_levy + t.stamp_duty + t.trading_fee + t.deposit_fee) as total_fees_hkd
                FROM stock.stock_transactions t
                LEFT JOIN stock.stocks s ON t.stock_code = s.code AND t.market = s.market
                WHERE {where_clause}
                ORDER BY t.market, t.stock_code, t.transaction_date, t.id
            ),
            running_totals AS (
                SELECT 
                    t1.*,
                    @prev_qty := IF(
                        @current_stock = CONCAT(t1.market, t1.stock_code),
                        @qty,
                        0
                    ) as calc_prev_qty,
                    @prev_cost := IF(
                        @current_stock = CONCAT(t1.market, t1.stock_code),
                        @cost,
                        0
                    ) as calc_prev_cost,
                    @prev_avg_cost := IF(
                        @current_stock = CONCAT(t1.market, t1.stock_code) AND @qty > 0,
                        @cost / @qty,
                            0
                    ) as calc_prev_avg_cost,
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
                            @cost + t1.total_amount + t1.total_fees_hkd,
                            IF(@qty > t1.total_quantity, 
                               @cost * (@qty - t1.total_quantity) / @qty,
                               0)
                        ),
                        IF(
                            t1.transaction_type = 'buy',
                            t1.total_amount + t1.total_fees_hkd,
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
                t.current_avg_cost as current_average_cost,
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
                t.qty_running, t.cost_running, t.calc_prev_qty, t.calc_prev_cost, t.calc_prev_avg_cost
            ORDER BY t.market, t.stock_code, t.transaction_date DESC, t.id DESC
        """

        # 4. 获取市场统计数据
        market_sql = f"""
            SELECT 
                t.market,
                COUNT(DISTINCT t.id) as transaction_count,
                SUM(CASE WHEN t.transaction_type = 'buy' THEN t.total_amount ELSE 0 END) as total_buy,
                SUM(CASE WHEN t.transaction_type = 'sell' THEN t.total_amount ELSE 0 END) as total_sell,
                SUM(t.broker_fee + t.transaction_levy + t.stamp_duty + t.trading_fee + t.deposit_fee) as total_fees
            FROM stock.stock_transactions t
            WHERE {where_clause}
            GROUP BY t.market
        """

        # 5. 获取股票统计数据
        stock_sql = f"""
            SELECT 
                t.market,
                t.stock_code,
                s.name as stock_name,
                COUNT(DISTINCT t.id) as transaction_count,
                SUM(CASE WHEN t.transaction_type = 'buy' THEN t.total_quantity ELSE -t.total_quantity END) as quantity,
                SUM(CASE WHEN t.transaction_type = 'buy' THEN t.total_amount ELSE 0 END) as total_buy,
                SUM(CASE WHEN t.transaction_type = 'sell' THEN t.total_amount ELSE 0 END) as total_sell,
                SUM(t.broker_fee + t.transaction_levy + t.stamp_duty + t.trading_fee + t.deposit_fee) as total_fees
            FROM stock.stock_transactions t
            LEFT JOIN stock.stocks s ON t.stock_code = s.code AND t.market = s.market
            WHERE {where_clause}
            GROUP BY t.market, t.stock_code, s.name
        """

        # 6. 执行查询
        transaction_details = db.fetch_all(details_sql, params)
        market_stats = db.fetch_all(market_sql, params)
        stock_stats = db.fetch_all(stock_sql, params)

        # 7. 处理交易明细数据
        transaction_details_dict = {}
        for detail in transaction_details:
            key = f"{detail['market']}-{detail['stock_code']}"
            if key not in transaction_details_dict:
                transaction_details_dict[key] = []
            # 转换日期格式
            if isinstance(detail['transaction_date'], datetime):
                detail['transaction_date'] = detail['transaction_date'].strftime('%Y-%m-%d')
            # 转换数值类型
            for field in ['total_amount', 'total_quantity', 'exchange_rate', 'broker_fee', 
                         'stamp_duty', 'transaction_levy', 'trading_fee', 'deposit_fee', 
                         'total_fees_hkd', 'current_quantity', 'current_average_cost']:
                if detail[field] is not None:
                    detail[field] = float(detail[field])
            # 转换交易类型为大写
            detail['transaction_type'] = detail['transaction_type'].upper()
            transaction_details_dict[key].append(detail)

        # 8. 处理市场统计数据
        market_stats_dict = {}
        for market in market_stats:
            market_code = market['market']
            
            # 获取该市场所有股票的已实现盈亏总和
            market_realized_profit_sql = """
                SELECT 
                    SUM(
                        CASE 
                            WHEN t.transaction_type = 'SELL' THEN 
                                t.total_amount - (t.total_quantity * t.prev_avg_cost) - 
                                (t.broker_fee + t.transaction_levy + t.stamp_duty + t.trading_fee + t.deposit_fee)
                            ELSE 0 
                        END
                    ) as total_realized_profit
                FROM stock_transactions t
                WHERE t.user_id = %s 
                  AND t.market = %s
            """
            market_realized_profit_record = db.fetch_one(market_realized_profit_sql, [session.get('user_id'), market_code])
            market_realized_profit = float(market_realized_profit_record['total_realized_profit'] or 0) if market_realized_profit_record else 0
            
            market_stats_dict[market_code] = {
                'transaction_count': market['transaction_count'],
                'total_buy': float(market['total_buy'] or 0),
                'total_sell': float(market['total_sell'] or 0),
                'total_fees': float(market['total_fees'] or 0),
                'realized_profit': market_realized_profit,
                'market_value': 0,
                'holding_profit': 0,
                'total_profit': 0,
                'profit_rate': 0,
                'holding_stats': {
                    'count': 0,
                    'total_buy': 0,
                    'total_sell': 0,
                    'total_fees': 0,
                    'realized_profit': 0,
                    'market_value': 0,
                    'holding_profit': 0,
                    'total_profit': 0,
                    'profit_rate': 0
                },
                'closed_stats': {
                    'count': 0,
                    'total_buy': 0,
                    'total_sell': 0,
                    'total_fees': 0,
                    'realized_profit': 0,
                    'profit_rate': 0
                }
            }

        # 9. 处理股票统计数据
        stock_stats_dict = {}
        for stock in stock_stats:
            market = stock['market']
            stock_code = stock['stock_code']
            key = f"{market}-{stock_code}"
            
            total_buy = float(stock['total_buy'] or 0)
            total_sell = float(stock['total_sell'] or 0)
            total_fees = float(stock['total_fees'] or 0)
            quantity = float(stock['quantity'] or 0)
            
            # 获取该股票所有交易的已实现盈亏总和
            realized_profit_sql = """
                SELECT 
                    SUM(
                        CASE 
                            WHEN t.transaction_type = 'SELL' THEN 
                                t.total_amount - (t.total_quantity * t.prev_avg_cost) - 
                                (t.broker_fee + t.transaction_levy + t.stamp_duty + t.trading_fee + t.deposit_fee)
                            ELSE 0 
                        END
                    ) as total_realized_profit
                FROM stock_transactions t
                WHERE t.user_id = %s 
                  AND t.stock_code = %s 
                  AND t.market = %s
            """
            realized_profit_record = db.fetch_one(realized_profit_sql, [session.get('user_id'), stock_code, market])
            realized_profit = float(realized_profit_record['total_realized_profit'] or 0) if realized_profit_record else 0
            
            # 计算盈亏（使用原始货币）
            market_value = 0
            holding_profit = 0
            current_price = 0  # 初始化current_price变量
            
            if quantity > 0:
                try:
                    query = stock['full_name'] if stock.get('full_name') else f"{stock_code}:NASDAQ"
                    logger.info(f"查询股价: {query}")
                    price_result = checker.get_stock_price(query)
                    if price_result is not None:
                        current_price = float(price_result)
                        # 获取最后一次买入时的移动加权平均价
                        avg_cost_sql = """
                            SELECT current_avg_cost
                            FROM stock_transactions
                            WHERE user_id = %s 
                              AND stock_code = %s 
                              AND market = %s
                              AND transaction_type = 'BUY'
                            ORDER BY transaction_date DESC, id DESC
                            LIMIT 1
                        """
                        latest_record = db.fetch_one(avg_cost_sql, [session.get('user_id'), stock_code, market])
                        avg_cost = float(latest_record['current_avg_cost']) if latest_record else 0
                        
                        # 计算市值
                        market_value = quantity * current_price
                        
                        # 计算持仓成本
                        holding_cost = quantity * avg_cost
                        
                        # 计算持仓盈亏 = 市值 - 持仓成本
                        holding_profit = market_value - holding_cost
                except Exception as e:
                    logger.error(f"获取股价失败 {stock['market']}:{stock['stock_code']}: {str(e)}")
                    market_value = 0
                    holding_profit = 0
                    current_price = 0
            
            # 总盈亏 = 已实现盈亏 + 持仓盈亏
            total_profit = realized_profit + holding_profit
            
            # 计算盈亏率
            profit_rate = (total_profit / total_buy * 100) if total_buy > 0 else 0
            
            stock_stats_dict[key] = {
                'market': market,
                'code': stock_code,
                'name': stock['stock_name'],
                'quantity': quantity,
                'transaction_count': stock['transaction_count'],
                'total_buy': total_buy,
                'total_sell': total_sell,
                'total_fees': total_fees,
                'realized_profit': realized_profit,
                'current_price': current_price if quantity > 0 else 0,
                'market_value': market_value,
                'holding_profit': holding_profit,
                'total_profit': total_profit,
                'profit_rate': profit_rate
            }
            
            # 更新市场统计
            if quantity > 0:
                market_stats_dict[market]['holding_stats']['count'] += 1
                market_stats_dict[market]['holding_stats']['total_buy'] += total_buy
                market_stats_dict[market]['holding_stats']['total_sell'] += total_sell
                market_stats_dict[market]['holding_stats']['total_fees'] += total_fees
                market_stats_dict[market]['holding_stats']['realized_profit'] += realized_profit
                market_stats_dict[market]['holding_stats']['market_value'] += market_value
                market_stats_dict[market]['holding_stats']['holding_profit'] += holding_profit
                market_stats_dict[market]['holding_stats']['total_profit'] = (
                    market_stats_dict[market]['holding_stats']['holding_profit'] +  # 持仓盈亏
                    market_stats_dict[market]['holding_stats']['realized_profit']   # 持仓股票的已实现盈亏
                )
                
                # 更新持仓盈亏率
                if market_stats_dict[market]['holding_stats']['total_buy'] > 0:
                    market_stats_dict[market]['holding_stats']['profit_rate'] = (
                        market_stats_dict[market]['holding_stats']['total_profit'] / 
                        market_stats_dict[market]['holding_stats']['total_buy'] * 100
                    )
            else:
                market_stats_dict[market]['closed_stats']['count'] += 1
                market_stats_dict[market]['closed_stats']['total_buy'] += total_buy
                market_stats_dict[market]['closed_stats']['total_sell'] += total_sell
                market_stats_dict[market]['closed_stats']['total_fees'] += total_fees
                market_stats_dict[market]['closed_stats']['realized_profit'] += realized_profit
                
                # 更新已平仓盈亏率
                if market_stats_dict[market]['closed_stats']['total_buy'] > 0:
                    market_stats_dict[market]['closed_stats']['profit_rate'] = (
                        market_stats_dict[market]['closed_stats']['realized_profit'] / 
                        market_stats_dict[market]['closed_stats']['total_buy'] * 100
                    )
            
            # 更新市场总计
            market_stats_dict[market]['market_value'] = market_stats_dict[market]['holding_stats']['market_value']
            market_stats_dict[market]['holding_profit'] = market_stats_dict[market]['holding_stats']['holding_profit']
            market_stats_dict[market]['total_profit'] = (
                market_stats_dict[market]['holding_stats']['holding_profit'] +  # 持仓盈亏
                market_stats_dict[market]['holding_stats']['realized_profit'] +  # 持仓股票的已实现盈亏
                market_stats_dict[market]['closed_stats']['realized_profit']     # 已平仓股票的已实现盈亏
            )
            
            # 更新市场总盈亏率
            total_buy = (
                market_stats_dict[market]['holding_stats']['total_buy'] + 
                market_stats_dict[market]['closed_stats']['total_buy']
            )
            if total_buy > 0:
                market_stats_dict[market]['profit_rate'] = (
                    market_stats_dict[market]['total_profit'] / total_buy * 100
                )

        return jsonify({
            'success': True,
            'data': {
                'market_stats': market_stats_dict,
                'stock_stats': stock_stats_dict,
                'transaction_details': transaction_details_dict
            }
        })

    except Exception as e:
        logger.error(f"获取盈利统计数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '获取盈利统计数据失败'
        }), 500 

def get_holding_stocks(user_id):
    """获取用户的持仓股票列表"""
    sql = """
        WITH stock_summary AS (
            SELECT 
                s.market,
                s.code,
                s.name as stock_name,
                s.full_name,
                SUM(CASE 
                    WHEN t.transaction_type = 'buy' THEN t.total_quantity 
                    WHEN t.transaction_type = 'sell' THEN -t.total_quantity 
                    ELSE 0 
                END) as quantity,
                SUM(CASE WHEN t.transaction_type = 'buy' THEN t.total_amount ELSE 0 END) as total_buy,
                SUM(CASE WHEN t.transaction_type = 'buy' THEN 
                    t.total_amount * COALESCE(
                        (SELECT rate FROM stock.exchange_rates 
                         WHERE currency = t.market 
                         AND rate_date <= t.transaction_date 
                         ORDER BY rate_date DESC LIMIT 1), 
                        1
                    ) 
                ELSE 0 END) as total_buy_hkd,
                SUM(CASE WHEN t.transaction_type = 'sell' THEN t.total_amount ELSE 0 END) as total_sell,
                SUM(CASE WHEN t.transaction_type = 'sell' THEN 
                    t.total_amount * COALESCE(
                        (SELECT rate FROM stock.exchange_rates 
                         WHERE currency = t.market 
                         AND rate_date <= t.transaction_date 
                         ORDER BY rate_date DESC LIMIT 1), 
                        1
                    ) 
                ELSE 0 END) as total_sell_hkd,
                SUM(t.broker_fee + t.transaction_levy + t.stamp_duty + t.trading_fee + t.deposit_fee) as total_fees,
                SUM((t.broker_fee + t.transaction_levy + t.stamp_duty + t.trading_fee + t.deposit_fee) * 
                    COALESCE(
                        (SELECT rate FROM stock.exchange_rates 
                         WHERE currency = t.market 
                         AND rate_date <= t.transaction_date 
                         ORDER BY rate_date DESC LIMIT 1), 
                        1
                    )
                ) as total_fees_hkd
            FROM stock.stock_transactions t
            JOIN stock.stocks s ON t.stock_code = s.code AND t.market = s.market
            WHERE t.user_id = %s
            GROUP BY s.market, s.code, s.name, s.full_name
            HAVING SUM(CASE 
                WHEN t.transaction_type = 'buy' THEN t.total_quantity 
                WHEN t.transaction_type = 'sell' THEN -t.total_quantity 
                ELSE 0 
            END) > 0
        )
        SELECT 
            market,
            code,
            stock_name,
            full_name,
            quantity,
            total_buy,
            total_buy_hkd,
            total_sell,
            total_sell_hkd,
            total_fees,
            total_fees_hkd,
            total_sell_hkd - total_buy_hkd - total_fees_hkd as realized_profit_hkd
        FROM stock_summary
        ORDER BY market, code
    """
    return db.fetch_all(sql, [user_id])

@profit_bp.route('/refresh_prices', methods=['POST'])
@login_required
def refresh_stock_prices():
    """刷新股票现价"""
    try:
        # 获取持仓股票列表
        sql = """
            SELECT 
                s.market,
                s.code,
                s.name as stock_name,
                s.full_name,
                SUM(CASE 
                    WHEN t.transaction_type = 'buy' THEN t.total_quantity 
                    WHEN t.transaction_type = 'sell' THEN -t.total_quantity 
                    ELSE 0 
                END) as quantity,
                SUM(CASE WHEN t.transaction_type = 'buy' THEN t.total_amount ELSE 0 END) as total_buy,
                SUM(CASE WHEN t.transaction_type = 'sell' THEN t.total_amount ELSE 0 END) as total_sell,
                SUM(t.broker_fee + t.transaction_levy + t.stamp_duty + t.trading_fee + t.deposit_fee) as total_fees
            FROM stock.stock_transactions t
            JOIN stock.stocks s ON t.stock_code = s.code AND t.market = s.market
            WHERE t.user_id = %s
            GROUP BY s.market, s.code, s.name, s.full_name
            HAVING SUM(CASE 
                WHEN t.transaction_type = 'buy' THEN t.total_quantity 
                WHEN t.transaction_type = 'sell' THEN -t.total_quantity 
                ELSE 0 
            END) > 0
        """
        
        stocks = db.fetch_all(sql, [session.get('user_id')])
        results = []
        success_count = 0
        failed_count = 0
        
        for stock in stocks:
            quantity = float(stock['quantity'])
            total_buy = float(stock['total_buy'])
            total_sell = float(stock['total_sell'])
            total_fees = float(stock['total_fees'])
            
            try:
                # 获取当前股价
                query = stock['full_name'] if stock.get('full_name') else f"{stock['code']}:NASDAQ"
                logger.info(f"查询股价: {query}")
                price_result = checker.get_stock_price(query)
                
                if price_result is not None:
                    current_price = float(price_result)
                    # 计算市值
                    market_value = current_price * quantity
                    
                    # 获取最后一次买入时的移动加权平均价
                    avg_cost_sql = """
                        SELECT current_avg_cost
                        FROM stock_transactions
                        WHERE user_id = %s 
                          AND stock_code = %s 
                          AND market = %s
                          AND transaction_type = 'BUY'
                        ORDER BY transaction_date DESC, id DESC
                        LIMIT 1
                    """
                    latest_record = db.fetch_one(avg_cost_sql, [session.get('user_id'), stock['code'], stock['market']])
                    avg_cost = float(latest_record['current_avg_cost']) if latest_record else 0
                    
                    # 计算持仓成本
                    holding_cost = quantity * avg_cost
                    
                    # 计算持仓盈亏 = 市值 - 持仓成本
                    holding_profit = market_value - holding_cost
                    
                    # 获取已实现盈亏
                    realized_profit_sql = """
                        SELECT 
                            SUM(
                                CASE 
                                    WHEN t.transaction_type = 'SELL' THEN 
                                        t.total_amount - (t.total_quantity * t.prev_avg_cost) - 
                                        (t.broker_fee + t.transaction_levy + t.stamp_duty + t.trading_fee + t.deposit_fee)
                                    ELSE 0 
                                END
                            ) as total_realized_profit
                        FROM stock_transactions t
                        WHERE t.user_id = %s 
                          AND t.stock_code = %s 
                          AND t.market = %s
                    """
                    realized_profit_record = db.fetch_one(realized_profit_sql, [session.get('user_id'), stock['code'], stock['market']])
                    realized_profit = float(realized_profit_record['total_realized_profit'] or 0) if realized_profit_record else 0
                    
                    # 总盈亏 = 已实现盈亏 + 持仓盈亏
                    total_profit = realized_profit + holding_profit
                    
                    # 计算盈亏率
                    profit_rate = (total_profit / total_buy * 100) if total_buy > 0 else 0
                    
                    results.append({
                        'market': stock['market'],
                        'code': stock['code'],
                        'name': stock['stock_name'],
                        'current_price': current_price,
                        'quantity': quantity,
                        'market_value': market_value,
                        'avg_cost': avg_cost,
                        'holding_profit': holding_profit,
                        'realized_profit': realized_profit,
                        'total_profit': total_profit,
                        'profit_rate': profit_rate
                    })
                    success_count += 1
                else:
                    failed_count += 1
                    logger.error(f"获取股价失败 {stock['market']}:{stock['code']}: 未获取到价格")
            except Exception as e:
                failed_count += 1
                logger.error(f"获取股价失败 {stock['market']}:{stock['code']}: {str(e)}")
        
        return jsonify({
            'success': True,
            'data': {
                'items': results,
                'success_count': success_count,
                'failed_count': failed_count
            }
        })
    except Exception as e:
        logger.error(f"刷新股价失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '刷新股价失败'
        }), 500 