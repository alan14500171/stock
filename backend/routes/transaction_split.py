#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, request, current_app, session
from datetime import datetime
import logging
import pymysql
import json
from utils.db import get_db_connection
from utils.auth import login_required, has_permission
from services.transaction_calculator import TransactionCalculator
from decimal import Decimal
from config.database import Database

transaction_split_bp = Blueprint('transaction_split', __name__)
logger = logging.getLogger(__name__)

# 创建数据库对象
db = Database()
db.init_pool()  # 确保初始化连接池

@transaction_split_bp.route('/api/transaction/get_by_code', methods=['GET'])
@login_required
def get_transaction_by_code():
    """
    根据交易编号获取交易记录
    允许以下用户查看：
    1. 交易创建者
    2. 分单的持有人关联的用户
    """
    transaction_code = request.args.get('transaction_code', '')
    current_user_id = session.get('user_id')
    
    # 添加详细日志
    logger.info(f"请求交易记录，交易编号: {transaction_code}")
    logger.info(f"当前session: {dict(session)}")
    logger.info(f"当前用户ID: {current_user_id}")
    
    if not transaction_code:
        return jsonify({
            'success': False,
            'message': '请提供交易编号'
        }), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 检查权限：是否是交易创建者或分单持有人
        auth_check_query = """
        SELECT DISTINCT st.id, st.transaction_code
        FROM stock_transactions st
        LEFT JOIN transaction_splits ts ON st.id = ts.original_transaction_id
        LEFT JOIN holders h ON ts.holder_id = h.id
        WHERE st.transaction_code = %s 
        AND (
            st.user_id = %s 
            OR h.user_id = %s 
            OR EXISTS (
                SELECT 1 
                FROM holders h2 
                WHERE h2.user_id = %s 
                AND h2.id IN (
                    SELECT holder_id 
                    FROM transaction_splits 
                    WHERE original_transaction_id = st.id
                )
            )
        )
        """
        
        # 记录查询参数
        logger.info(f"执行权限检查查询，参数: user_id={current_user_id}, transaction_code={transaction_code}")
        
        cursor.execute(auth_check_query, (transaction_code, current_user_id, current_user_id, current_user_id))
        auth_result = cursor.fetchone()
        
        # 记录权限检查结果
        logger.info(f"权限检查结果: {auth_result}")
        
        if not auth_result:
            # 记录更多信息以便调试
            debug_query = """
            SELECT 
                st.id as transaction_id,
                st.transaction_code,
                st.user_id as transaction_user_id,
                ts.id as split_id,
                h.id as holder_id,
                h.name as holder_name,
                h.user_id as holder_user_id
            FROM stock_transactions st
            LEFT JOIN transaction_splits ts ON st.id = ts.original_transaction_id
            LEFT JOIN holders h ON ts.holder_id = h.id
            WHERE st.transaction_code = %s
            """
            cursor.execute(debug_query, (transaction_code,))
            debug_info = cursor.fetchall()
            logger.info(f"调试信息 - 交易记录详情: {debug_info}")
            
            return jsonify({
                'success': False,
                'message': '无权查看该交易记录'
            }), 403
        
        # 查询交易记录
        query = """
        SELECT t.*, s.code_name as stock_name 
        FROM stock_transactions t
        LEFT JOIN stocks s ON t.stock_code = s.code AND t.market = s.market
        WHERE t.transaction_code = %s
        """
        cursor.execute(query, (transaction_code,))
        transaction = cursor.fetchone()
        
        if not transaction:
            return jsonify({
                'success': False,
                'message': '未找到交易记录'
            }), 404
        
        # 获取交易明细
        detail_query = """
        SELECT *
        FROM stock_transaction_details
        WHERE transaction_id = %s
        """
        cursor.execute(detail_query, (transaction['id'],))
        details = cursor.fetchall()
        
        # 获取分单记录
        splits_query = """
        SELECT ts.*, h.name as holder_name, h.user_id as holder_user_id
        FROM transaction_splits ts
        LEFT JOIN holders h ON ts.holder_id = h.id
        WHERE ts.original_transaction_id = %s
        """
        cursor.execute(splits_query, (transaction['id'],))
        splits = cursor.fetchall()
        
        # 转换日期格式
        if transaction.get('transaction_date'):
            transaction['transaction_date'] = transaction['transaction_date'].strftime('%Y-%m-%d')
        
        if transaction.get('created_at'):
            transaction['created_at'] = transaction['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        if transaction.get('updated_at'):
            transaction['updated_at'] = transaction['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        # 添加明细和分单信息到交易记录
        transaction['details'] = details
        transaction['splits'] = splits
        
        return jsonify({
            'success': True,
            'data': transaction
        })
        
    except Exception as e:
        current_app.logger.error(f"获取交易记录失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取交易记录失败: {str(e)}'
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@transaction_split_bp.route('/api/transaction/get_users', methods=['GET'])
@login_required
def get_users():
    """
    获取持有人列表，用于分单选择
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 查询持有人列表
        query = """
        SELECT id, name, name as display_name, type
        FROM holders
        WHERE status = 1
        ORDER BY name
        """
        cursor.execute(query)
        holders = cursor.fetchall()
        
        # 记录持有人信息
        logger.info(f"获取到 {len(holders)} 个持有人")
        for holder in holders:
            logger.info(f"持有人: id={holder['id']}, name={holder['name']}, display_name={holder['display_name']}")
        
        # 处理时间格式
        return jsonify({
            'success': True,
            'data': holders
        })
        
    except Exception as e:
        current_app.logger.error(f"获取持有人列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取持有人列表失败: {str(e)}'
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@transaction_split_bp.route('/api/transaction/split', methods=['POST'])
@login_required
def split_transaction():
    """处理交易分单"""
    try:
        data = request.get_json()
        transaction_id = data.get('transaction_id')
        splits = data.get('splits', [])
        
        logger.info(f"收到分单请求: transaction_id={transaction_id}, splits={splits}")
        
        if not transaction_id or not splits:
            logger.warning(f"分单请求参数不完整: transaction_id={transaction_id}, splits={len(splits) if splits else 0}")
            return jsonify({
                'success': False,
                'message': '参数不完整'
            }), 400
            
        # 检查分割比例总和是否为1
        total_ratio = sum(float(split.get('ratio', 0)) for split in splits)
        if abs(total_ratio - 1.0) > 0.01:  # 允许0.01的误差
            logger.warning(f"分单比例总和不为1: {total_ratio}")
            return jsonify({
                'success': False,
                'message': '分配比例总和必须为1'
            }), 400
            
        # 使用db对象获取连接
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 查询原始交易记录
            query = """
                SELECT * FROM stock_transactions
                WHERE id = %s
                LIMIT 1
            """
            cursor.execute(query, [transaction_id])
            transaction = cursor.fetchone()
            
            if not transaction:
                logger.warning(f"未找到交易记录: transaction_id={transaction_id}")
                return jsonify({
                    'success': False,
                    'message': '未找到交易记录'
                }), 404
                
            logger.info(f"找到原始交易记录: {transaction}")
            
            # 先删除该交易的所有现有分单记录
            delete_query = """
                DELETE FROM transaction_splits
                WHERE original_transaction_id = %s
            """
            cursor.execute(delete_query, [transaction_id])
            deleted_count = cursor.rowcount
            logger.info(f"已删除 {deleted_count} 条旧的分单记录")
            
            # 处理每个分单
            calculator = TransactionCalculator()
            successful_splits = []
            
            # 保存交易日期和股票信息，用于后续重新计算
            transaction_date = transaction['transaction_date'].strftime('%Y-%m-%d')
            stock_code = transaction['stock_code']
            market = transaction['market']
            processed_holder_ids = []
            
            try:
                for split in splits:
                    holder_id = split.get('holder_id')
                    holder_name = split.get('holder_name', '')
                    ratio = float(split.get('ratio', 0))
                    quantity = int(split.get('quantity', 0))
                    amount = float(split.get('amount', 0))
                    fees = float(split.get('fees', 0))
                    
                    # 如果没有提供holder_name，从holders表获取
                    if not holder_name:
                        holder_query = """
                            SELECT name, display_name FROM holders
                            WHERE id = %s
                            LIMIT 1
                        """
                        cursor.execute(holder_query, [holder_id])
                        holder = cursor.fetchone()
                        if holder:
                            # 优先使用display_name，如果没有则使用name
                            holder_name = holder.get('display_name') or holder.get('name', '')
                            logger.info(f"从数据库获取持有人名称: holder_id={holder_id}, holder_name='{holder_name}'")
                        else:
                            holder_name = f"持有人ID: {holder_id}"
                            logger.warning(f"未找到持有人信息: holder_id={holder_id}, 使用默认名称")
                    
                    logger.info(f"处理分单: holder_id={holder_id}, holder_name='{holder_name}', ratio={ratio}")
                    
                    # 准备交易数据
                    transaction_data = {
                        'id': transaction['id'],
                        'transaction_code': transaction['transaction_code'],
                        'transaction_date': transaction_date,
                        'stock_code': stock_code,
                        'market': market,
                        'transaction_type': transaction['transaction_type'],
                        'total_quantity': quantity or int(transaction['total_quantity'] * ratio),
                        'total_amount': amount or float(transaction['total_amount'] * ratio),
                        'broker_fee': float(transaction['broker_fee'] * ratio) if transaction['broker_fee'] else 0,
                        'stamp_duty': float(transaction['stamp_duty'] * ratio) if transaction['stamp_duty'] else 0,
                        'transaction_levy': float(transaction['transaction_levy'] * ratio) if transaction['transaction_levy'] else 0,
                        'trading_fee': float(transaction['trading_fee'] * ratio) if transaction['trading_fee'] else 0,
                        'deposit_fee': float(transaction['deposit_fee'] * ratio) if transaction['deposit_fee'] else 0,
                        'split_ratio': ratio,
                        'holder_name': holder_name,  # 确保传递持有人名称
                        'remarks': transaction.get('remarks', '')  # 添加备注字段
                    }
                    
                    # 计算总费用
                    if fees > 0:
                        # 如果前端提供了费用，则按比例分配到各个费用项
                        total_original_fees = (
                            (transaction['broker_fee'] or 0) +
                            (transaction['stamp_duty'] or 0) +
                            (transaction['transaction_levy'] or 0) +
                            (transaction['trading_fee'] or 0) +
                            (transaction['deposit_fee'] or 0)
                        )
                        
                        if total_original_fees > 0:
                            fee_ratio = fees / total_original_fees
                            transaction_data['broker_fee'] = float(transaction['broker_fee'] * fee_ratio) if transaction['broker_fee'] else 0
                            transaction_data['stamp_duty'] = float(transaction['stamp_duty'] * fee_ratio) if transaction['stamp_duty'] else 0
                            transaction_data['transaction_levy'] = float(transaction['transaction_levy'] * fee_ratio) if transaction['transaction_levy'] else 0
                            transaction_data['trading_fee'] = float(transaction['trading_fee'] * fee_ratio) if transaction['trading_fee'] else 0
                            transaction_data['deposit_fee'] = float(transaction['deposit_fee'] * fee_ratio) if transaction['deposit_fee'] else 0
                    
                    # 处理分单 - 使用db对象而不是conn
                    success, result = calculator.process_transaction(
                        db,
                        transaction_data,
                        'split',
                        holder_id,
                        transaction['id']
                    )
                    
                    if success:
                        logger.info(f"分单处理成功: {result}")
                        successful_splits.append({
                            'holder_id': holder_id,
                            'holder_name': holder_name,
                            'ratio': ratio,
                            'quantity': transaction_data['total_quantity'],
                            'amount': transaction_data['total_amount'],
                            'fees': sum([
                                transaction_data.get('broker_fee', 0),
                                transaction_data.get('stamp_duty', 0),
                                transaction_data.get('transaction_levy', 0),
                                transaction_data.get('trading_fee', 0),
                                transaction_data.get('deposit_fee', 0)
                            ])
                        })
                        processed_holder_ids.append(holder_id)
                    else:
                        logger.error(f"分单处理失败: {result}")
                        return jsonify({
                            'success': False,
                            'message': f"处理分单失败: {result.get('message', '未知错误')}"
                        }), 500
                
                # 重新计算每个持有人的后续交易记录
                logger.info(f"开始重新计算后续交易记录: stock_code={stock_code}, market={market}, date={transaction_date}")
                for holder_id in processed_holder_ids:
                    recalc_success = TransactionCalculator.recalculate_subsequent_transactions(
                        db,
                        stock_code,
                        market,
                        transaction_date,
                        holder_id
                    )
                    if recalc_success:
                        logger.info(f"成功重新计算持有人ID={holder_id}的后续交易记录")
                    else:
                        logger.warning(f"重新计算持有人ID={holder_id}的后续交易记录失败")
            
                # 提交事务
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': '分单处理成功',
                    'data': {
                        'transaction_id': transaction_id,
                        'splits': successful_splits
                    }
                })
                
            except Exception as e:
                logger.exception(f"分单处理异常: {str(e)}")
                if conn:
                    conn.rollback()
                return jsonify({
                    'success': False,
                    'message': f'分单处理异常: {str(e)}'
                }), 500
                
    except Exception as e:
        logger.error(f"处理交易分单时发生错误: {str(e)}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")

@transaction_split_bp.route('/api/transaction/splits', methods=['GET'])
@login_required
def get_transaction_splits():
    """获取交易分单记录"""
    try:
        # 获取查询参数
        transaction_id = request.args.get('transaction_id')
        if not transaction_id:
            return jsonify({
                'success': False,
                'message': '缺少交易ID参数'
            }), 400

        # 使用db对象而不是直接创建连接
        with db.get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # 查询分单记录
            sql = """
                SELECT ts.*, COALESCE(ts.holder_name, h.name) as holder_name, h.user_id as holder_user_id, h.type as holder_type
                FROM transaction_splits ts
                LEFT JOIN holders h ON ts.holder_id = h.id
                WHERE ts.original_transaction_id = %s
                ORDER BY ts.id
            """
            cursor.execute(sql, [transaction_id])
            splits = cursor.fetchall()
            
            # 格式化数据
            formatted_splits = []
            for split in splits:
                formatted_splits.append({
                    'id': split['id'],
                    'holder_id': split['holder_id'],
                    'holder_name': split['holder_name'],
                    'holder_user_id': split['holder_user_id'],
                    'holder_type': split['holder_type'],
                    'split_ratio': float(split['split_ratio']),
                    'total_quantity': float(split['total_quantity']),
                    'total_amount': float(split['total_amount']),
                    'realized_profit': float(split['realized_profit']),
                    'profit_rate': float(split['profit_rate']),
                    'current_quantity': float(split['current_quantity']),
                    'current_cost': float(split['current_cost']),
                    'current_avg_cost': float(split['current_avg_cost']),
                    'total_fees': float(split['total_fees']),
                    'created_at': split['created_at'].strftime('%Y-%m-%d %H:%M:%S') if split.get('created_at') else None
                })
            
            return jsonify({
                'success': True,
                'splits': formatted_splits
            })
            
    except Exception as e:
        logger.error(f"获取交易分单记录时发生错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取交易分单记录失败: {str(e)}'
        }), 500

@transaction_split_bp.route('/api/transaction/split/<transaction_code>', methods=['GET'])
@login_required
def get_transaction_by_code_param(transaction_code):
    """根据交易编号获取分单记录"""
    try:
        # 使用db对象而不是直接创建连接
        with db.get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # 先查询交易记录
            transaction_query = """
                SELECT id FROM stock_transactions
                WHERE transaction_code = %s
                LIMIT 1
            """
            cursor.execute(transaction_query, [transaction_code])
            transaction = cursor.fetchone()
            
            if not transaction:
                return jsonify({
                    'success': False,
                    'message': '未找到交易记录'
                }), 404
                
            # 查询分单记录
            splits_query = """
                SELECT ts.*, 
                       COALESCE(ts.holder_name, h.name) as holder_name,
                       h.user_id as holder_user_id,
                       h.type as holder_type
                FROM transaction_splits ts
                LEFT JOIN holders h ON ts.holder_id = h.id
                WHERE ts.original_transaction_id = %s
                ORDER BY ts.id DESC
            """
            cursor.execute(splits_query, [transaction['id']])
            splits = cursor.fetchall()
            
            # 格式化分单记录
            formatted_splits = []
            for split in splits:
                # 转换日期格式
                transaction_date = split['transaction_date'].strftime('%Y-%m-%d') if split.get('transaction_date') else None
                created_at = split['created_at'].strftime('%Y-%m-%d %H:%M:%S') if split.get('created_at') else None
                
                formatted_split = {
                    'id': split['id'],
                    'original_transaction_id': split['original_transaction_id'],
                    'holder_id': split['holder_id'],
                    'holder_name': split['holder_name'],
                    'holder_display_name': split['holder_name'],  # 使用holder_name作为display_name
                    'holder_user_id': split.get('holder_user_id'),
                    'holder_type': split.get('holder_type'),
                    'split_ratio': _format_split_ratio(split.get('split_ratio')),  # 使用辅助方法处理比例
                    'transaction_date': transaction_date,
                    'stock_code': split['stock_code'],
                    'market': split['market'],
                    'stock_name': split.get('stock_name', ''),
                    'transaction_type': split.get('transaction_type', ''),
                    'total_quantity': split['total_quantity'],
                    'total_amount': float(split['total_amount']) if split.get('total_amount') else 0,
                    'total_fees': float(split['total_fees']) if split.get('total_fees') else 0,
                    'created_at': created_at
                }
                formatted_splits.append(formatted_split)
            
            # 记录返回的数据结构
            logger.info(f"返回的分单记录数量: {len(formatted_splits)}")
            logger.debug(f"返回的分单记录: {formatted_splits}")
            
            return jsonify({
                'success': True,
                'data': formatted_splits  # 修改为'data'字段，与前端期望的结构一致
            })
            
    except Exception as e:
        logger.exception(f"获取交易分单记录异常: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取交易分单记录异常: {str(e)}'
        }), 500

@transaction_split_bp.route('/api/transaction/all_splits', methods=['GET'])
@login_required
def get_all_transaction_splits():
    """获取所有交易分单记录"""
    try:
        # 使用db对象而不是直接创建连接
        with db.get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # 查询分单记录
            query = """
                SELECT ts.*, h.name as holder_name,
                       st.transaction_code, st.stock_code, st.market, st.transaction_type,
                       st.transaction_date
                FROM transaction_splits ts
                LEFT JOIN holders h ON ts.holder_id = h.id
                LEFT JOIN stock_transactions st ON ts.original_transaction_id = st.id
                ORDER BY ts.id DESC
                LIMIT 1000
            """
            cursor.execute(query)
            splits = cursor.fetchall()
            
            # 处理结果
            result = []
            for split in splits:
                # 使用holder_name
                holder_name = split.get('holder_name', '')
                
                # 转换日期格式
                transaction_date = split['transaction_date'].strftime('%Y-%m-%d') if split.get('transaction_date') else None
                created_at = split['created_at'].strftime('%Y-%m-%d %H:%M:%S') if split.get('created_at') else None
                
                result.append({
                    'id': split['id'],
                    'original_transaction_id': split['original_transaction_id'],
                    'transaction_code': split['transaction_code'],
                    'stock_code': split['stock_code'],
                    'market': split['market'],
                    'transaction_type': split['transaction_type'],
                    'transaction_date': transaction_date,
                    'holder_id': split['holder_id'],
                    'holder_name': holder_name,
                    'ratio': float(split['ratio']) if split['ratio'] else 0,
                    'quantity': split['quantity'],
                    'amount': float(split['amount']) if split['amount'] else 0,
                    'fees': float(split['fees']) if split['fees'] else 0,
                    'created_at': created_at
                })
            
            return jsonify({
                'success': True,
                'data': result
            })
            
    except Exception as e:
        logger.exception(f"获取所有分单记录异常: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取所有分单记录异常: {str(e)}'
        }), 500

@transaction_split_bp.route('/api/transaction/get_accessible_holders', methods=['GET'])
@login_required
def get_accessible_holders():
    """
    获取当前用户可以访问的持有人列表，用于盈利统计筛选
    包括：
    1. 用户自己创建的持有人
    2. 用户通过分单关系可以访问的持有人
    """
    try:
        current_user_id = session.get('user_id')
        
        # 记录请求信息
        logger.info(f"获取可访问持有人列表，用户ID: {current_user_id}")
        
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 查询用户可访问的持有人列表
        # 包括用户自己创建的持有人和通过分单关系可以访问的持有人
        query = """
        SELECT DISTINCT h.id, h.name, h.name as display_name, h.type
        FROM holders h
        WHERE h.status = 1 AND (
            h.user_id = %s OR
            h.id IN (
                SELECT DISTINCT ts.holder_id
                FROM transaction_splits ts
                JOIN stock_transactions st ON ts.original_transaction_id = st.id
                WHERE st.user_id = %s
            )
        )
        ORDER BY h.name
        """
        cursor.execute(query, (current_user_id, current_user_id))
        holders = cursor.fetchall()
        
        # 记录持有人信息
        logger.info(f"获取到 {len(holders)} 个可访问的持有人")
        
        return jsonify({
            'success': True,
            'data': holders
        })
        
    except Exception as e:
        logger.error(f"获取可访问持有人列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取可访问持有人列表失败: {str(e)}'
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# 添加辅助方法处理split_ratio格式
def _format_split_ratio(value):
    """
    处理分割比例的格式，确保返回的是百分比格式（0-100）
    """
    if value is None:
        return 0
    
    try:
        float_value = float(value)
        # 记录原始值，方便调试
        logger.debug(f"处理分割比例: 原始值={float_value}")
        
        # 如果值已经是百分比格式（0-100之间）就直接返回
        if 0 <= float_value <= 100:
            return float_value
        # 如果值是小数格式（0-1之间）则转换为百分比
        elif 0 <= float_value < 1:
            return float_value * 100
        # 如果值大于100，可能是错误的，返回100
        elif float_value > 100:
            logger.warning(f"分割比例值过大: {float_value}，将限制为100")
            return 100
        # 如果值为负，返回0
        else:
            logger.warning(f"分割比例值为负: {float_value}，将重置为0")
            return 0
    except (ValueError, TypeError) as e:
        logger.error(f"分割比例格式化错误: {e}, 值={value}")
        return 0

def register_routes(app):
    """
    注册路由
    """
    app.register_blueprint(transaction_split_bp) 