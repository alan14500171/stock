from flask import Blueprint, request, session, jsonify
from functools import wraps
from models.user import User
from models import Permission, Role
from utils.auth import login_required, get_current_user
import logging

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'message': '请先登录'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

# 注册API已禁用
"""
@auth_bp.route('/register', methods=['POST'])
def register():
    # 用户注册API
    try:
        logger.info('开始处理注册请求')
        logger.info('请求内容类型: %s', request.content_type)
        logger.info('请求数据: %s', request.get_data())
        
        data = request.get_json() if request.is_json else request.form
        logger.info('解析后的数据: %s', data)
        
        username = data.get('username')
        password = data.get('password')
        
        logger.info('用户名: %s', username)
        
        if not username or not password:
            logger.warning('用户名或密码为空')
            return jsonify({
                'success': False,
                'message': '用户名和密码不能为空'
            }), 400
        
        if User.find_by_username(username):
            logger.warning('用户名已存在: %s', username)
            return jsonify({
                'success': False,
                'message': '用户名已存在'
            }), 400
        
        new_user = User()
        new_user.username = username
        new_user.set_password(password)
        
        if new_user.save():
            logger.info('用户注册成功: %s', username)
            return jsonify({
                'success': True,
                'message': '注册成功'
            })
        else:
            logger.error('用户保存失败: %s', username)
            return jsonify({
                'success': False,
                'message': '注册失败'
            }), 500
            
    except Exception as e:
        logger.error('注册过程发生错误: %s', str(e), exc_info=True)
        return jsonify({
            'success': False,
            'message': f'注册失败: {str(e)}'
        }), 500
"""

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录API"""
    try:
        logger.info('开始处理登录请求')
        logger.info('请求内容类型: %s', request.content_type)
        logger.info('请求数据: %s', request.get_data())
        
        data = request.get_json() if request.is_json else request.form
        logger.info('解析后的数据: %s', data)
        
        username = data.get('username')
        password = data.get('password')
        
        logger.info('用户名: %s', username)
        
        if not username or not password:
            logger.warning('用户名或密码为空')
            return jsonify({
                'success': False,
                'message': '用户名和密码不能为空'
            }), 400
        
        user = User.find_by_username(username)
        logger.info('查找用户结果: %s', bool(user))
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            user.update_last_login()
            logger.info('用户登录成功: %s', username)
            return jsonify({
                'success': True,
                'message': '登录成功',
                'user': user.to_dict()
            })
        
        logger.warning('用户名或密码错误: %s', username)
        return jsonify({
            'success': False,
            'message': '用户名或密码错误'
        }), 401
            
    except Exception as e:
        logger.error('登录过程发生错误: %s', str(e), exc_info=True)
        return jsonify({
            'success': False,
            'message': f'登录失败: {str(e)}'
        }), 500

@auth_bp.route('/logout')
@login_required
def logout():
    """退出登录API"""
    try:
        session.clear()
        return jsonify({
            'success': True,
            'message': '退出登录成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@auth_bp.route('/check_login')
def check_login():
    """检查登录状态API"""
    is_authenticated = 'user_id' in session
    user = None
    if is_authenticated:
        user = User.get_by_id(session.get('user_id'))
        if not user:
            is_authenticated = False
            session.clear()
    
    return jsonify({
        'success': True,
        'is_authenticated': is_authenticated,
        'user': user.to_dict() if user else None
    })

@auth_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    """修改密码API"""
    try:
        logger.info('开始处理修改密码请求')
        
        data = request.get_json() if request.is_json else request.form
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            logger.warning('当前密码或新密码为空')
            return jsonify({
                'success': False,
                'message': '当前密码和新密码不能为空'
            }), 400
            
        # 获取当前用户
        user = User.get_by_id(session.get('user_id'))
        if not user:
            logger.warning('用户不存在')
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
            
        # 验证当前密码
        if not user.check_password(current_password):
            logger.warning('当前密码错误')
            return jsonify({
                'success': False,
                'message': '当前密码错误'
            }), 400
            
        # 设置新密码
        user.set_password(new_password)
        if user.save():
            logger.info('密码修改成功')
            return jsonify({
                'success': True,
                'message': '密码修改成功'
            })
        else:
            logger.error('密码保存失败')
            return jsonify({
                'success': False,
                'message': '密码修改失败'
            }), 500
            
    except Exception as e:
        logger.error('修改密码过程发生错误: %s', str(e), exc_info=True)
        return jsonify({
            'success': False,
            'message': f'修改密码失败: {str(e)}'
        }), 500

@auth_bp.route('/user/permissions', methods=['GET'])
@login_required
def get_user_permissions():
    """获取当前用户的权限信息"""
    try:
        user = get_current_user()
        logger.info(f"获取用户权限信息: {user.username if user else 'None'}")
        
        if not user:
            return jsonify({
                'success': False,
                'message': '获取用户权限失败'
            }), 401
            
        # 获取用户角色
        roles = Role.get_user_roles(user.id)
        logger.info(f"用户角色: {[role.name for role in roles]}")
        
        # 获取用户权限
        permissions = Permission.get_user_permissions(user.id)
        logger.info(f"用户权限数量: {len(permissions)}")
        
        # 只返回权限代码列表
        permission_codes = [permission.code for permission in permissions]
        logger.info(f"用户权限代码: {permission_codes}")
        
        return jsonify({
            'success': True,
            'data': {
                'permissions': permission_codes,
                'roles': [role.to_dict() for role in roles]
            }
        })
    except Exception as e:
        logger.error(f"获取用户权限失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"获取用户权限失败: {str(e)}"
        }), 500 