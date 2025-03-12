#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, request, current_app, session
import logging
from utils.auth import login_required
from services.transaction_service import TransactionService
from services.transaction_query import TransactionQuery
from config.database import Database

transaction_bp = Blueprint('transaction', __name__)
logger = logging.getLogger(__name__)

# 创建数据库对象
db = Database()
db.init_pool()  # 确保初始化连接池

@transaction_bp.route('/api/transaction/<int:transaction_id>', methods=['GET'])
@login_required
def get_transaction(transaction_id):
    """获取单个交易记录"""
    try:
        user_id = session.get('user_id')
        transaction = TransactionQuery.get_transaction_by_id(transaction_id, user_id)
        
        if not transaction:
            return jsonify({
                'success': False,
                'message': '交易记录不存在或无权限查看'
            }), 404
            
        return jsonify({
            'success': True,
            'data': transaction
        })
        
    except Exception as e:
        logger.error(f'获取交易记录失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'获取交易记录失败: {str(e)}'
        }), 500

@transaction_bp.route('/api/transaction', methods=['POST'])
@login_required
def add_transaction():
    """添加交易记录"""
    try:
        user_id = session.get('user_id')
        transaction_data = request.json
        
        # 确保transaction_data中包含user_id
        transaction_data['user_id'] = user_id
        
        success, result, status_code = TransactionService.process_transaction(
            db=db,  # 使用初始化的数据库连接对象
            user_id=user_id,
            transaction_data=transaction_data
        )
        
        if not success:
            return jsonify({
                'success': False,
                'message': result.get('message', '添加交易记录失败')
            }), status_code
            
        return jsonify({
            'success': True,
            'message': '添加交易记录成功',
            'data': result
        })
        
    except Exception as e:
        logger.error(f'添加交易记录失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'添加交易记录失败: {str(e)}'
        }), 500

@transaction_bp.route('/api/transaction/<int:transaction_id>', methods=['PUT'])
@login_required
def update_transaction(transaction_id):
    """更新交易记录"""
    try:
        user_id = session.get('user_id')
        transaction_data = request.json
        
        # 确保transaction_data中包含user_id
        transaction_data['user_id'] = user_id
        
        success, result, status_code = TransactionService.process_transaction(
            db=db,  # 使用初始化的数据库连接对象
            user_id=user_id,
            transaction_data=transaction_data,
            transaction_id=transaction_id
        )
        
        if not success:
            return jsonify({
                'success': False,
                'message': result.get('message', '更新交易记录失败')
            }), status_code
            
        return jsonify({
            'success': True,
            'message': '更新交易记录成功',
            'data': result
        })
        
    except Exception as e:
        logger.error(f'更新交易记录失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'更新交易记录失败: {str(e)}'
        }), 500

@transaction_bp.route('/api/transaction/<int:transaction_id>', methods=['DELETE'])
@login_required
def delete_transaction(transaction_id):
    """删除交易记录"""
    try:
        user_id = session.get('user_id')
        
        # 获取交易记录
        transaction = TransactionQuery.get_transaction_by_id(transaction_id, user_id)
        
        if not transaction:
            return jsonify({
                'success': False,
                'message': '交易记录不存在或无权限删除'
            }), 404
        
        success, result, status_code = TransactionService.process_transaction(
            db=db,  # 使用初始化的数据库连接对象
            user_id=user_id,
            transaction_data=transaction,
            transaction_id=transaction_id,
            is_delete=True
        )
        
        if not success:
            return jsonify({
                'success': False,
                'message': result.get('message', '删除交易记录失败')
            }), status_code
            
        return jsonify({
            'success': True,
            'message': '删除交易记录成功'
        })
        
    except Exception as e:
        logger.error(f'删除交易记录失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'删除交易记录失败: {str(e)}'
        }), 500 