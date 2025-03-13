#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
用户角色权限检查工具
用于连接数据库并检查用户角色的权限问题
"""
import sys
import os
import logging
import pymysql
from pymysql.cursors import DictCursor
import argparse
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'permission_check_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

# 从环境变量或配置文件获取数据库配置
def get_db_config():
    """获取数据库配置"""
    # 优先从环境变量获取
    db_host = os.environ.get('DB_HOST', '192.168.0.109')
    db_port = int(os.environ.get('DB_PORT', 3306))
    db_user = os.environ.get('DB_USER', 'root')
    db_password = os.environ.get('DB_PASSWORD', 'Zxc000123')
    db_name = os.environ.get('DB_NAME', 'stock')
    db_charset = os.environ.get('DB_CHARSET', 'utf8mb4')
    
    return {
        'host': db_host,
        'port': db_port,
        'user': db_user,
        'password': db_password,
        'database': db_name,
        'charset': db_charset,
        'cursorclass': DictCursor,
        'autocommit': True
    }

def connect_to_database():
    """连接到数据库"""
    config = get_db_config()
    try:
        logger.info(f"正在连接到数据库 {config['host']}:{config['port']}/{config['database']}...")
        connection = pymysql.connect(**config)
        logger.info("数据库连接成功")
        return connection
    except pymysql.MySQLError as e:
        error_code = getattr(e, 'args', [None])[0]
        error_msg = f"数据库连接失败: {str(e)}"
        
        # 详细记录错误信息
        if error_code == 1045:
            error_msg += " - 访问被拒绝，用户名或密码错误"
        elif error_code == 1049:
            error_msg += " - 数据库不存在"
        elif error_code == 2003:
            error_msg += " - 无法连接到MySQL服务器，检查服务是否运行或网络问题"
        elif error_code == 2005:
            error_msg += " - 无法解析主机名"
        elif error_code == 2013:
            error_msg += " - 连接过程中服务器关闭了连接"
        
        logger.error(error_msg)
        return None
    except Exception as e:
        logger.error(f"连接数据库时发生未知错误: {str(e)}")
        return None

def get_all_users(connection):
    """获取所有用户"""
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM users ORDER BY id"
            cursor.execute(sql)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        return []

def get_user_roles(connection, user_id):
    """获取用户的角色"""
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT r.* FROM roles r
                JOIN user_roles ur ON r.id = ur.role_id
                WHERE ur.user_id = %s
            """
            cursor.execute(sql, (user_id,))
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"获取用户角色失败: {str(e)}")
        return []

def get_role_permissions(connection, role_id):
    """获取角色的权限"""
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT p.* FROM permissions p
                JOIN role_permissions rp ON p.id = rp.permission_id
                WHERE rp.role_id = %s
                ORDER BY p.sort_order, p.id
            """
            cursor.execute(sql, (role_id,))
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"获取角色权限失败: {str(e)}")
        return []

def get_user_permissions(connection, user_id):
    """获取用户的所有权限"""
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT DISTINCT p.* FROM permissions p
                JOIN role_permissions rp ON p.id = rp.permission_id
                JOIN user_roles ur ON rp.role_id = ur.role_id
                WHERE ur.user_id = %s
                ORDER BY p.sort_order, p.id
            """
            cursor.execute(sql, (user_id,))
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"获取用户权限失败: {str(e)}")
        return []

def check_user_permission(connection, user_id, permission_code):
    """检查用户是否有指定权限"""
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT COUNT(*) as count FROM permissions p
                JOIN role_permissions rp ON p.id = rp.permission_id
                JOIN user_roles ur ON rp.role_id = ur.role_id
                WHERE ur.user_id = %s AND p.code = %s
            """
            cursor.execute(sql, (user_id, permission_code))
            result = cursor.fetchone()
            return result and result['count'] > 0
    except Exception as e:
        logger.error(f"检查用户权限失败: {str(e)}")
        return False

def check_all_users_permissions(connection, permission_code=None):
    """检查所有用户的权限"""
    users = get_all_users(connection)
    
    if not users:
        logger.warning("未找到任何用户")
        return
    
    logger.info(f"共找到 {len(users)} 个用户")
    
    for user in users:
        logger.info(f"\n用户: {user['username']} (ID: {user['id']})")
        
        # 获取用户角色
        roles = get_user_roles(connection, user['id'])
        if not roles:
            logger.warning(f"  - 用户 {user['username']} 没有分配任何角色")
            continue
        
        logger.info(f"  - 角色: {', '.join([role['name'] for role in roles])}")
        
        # 获取用户权限
        permissions = get_user_permissions(connection, user['id'])
        if not permissions:
            logger.warning(f"  - 用户 {user['username']} 没有任何权限")
            continue
        
        logger.info(f"  - 权限数量: {len(permissions)}")
        
        # 如果指定了权限代码，检查用户是否有该权限
        if permission_code:
            has_permission = any(p['code'] == permission_code for p in permissions)
            if has_permission:
                logger.info(f"  - ✅ 用户 {user['username']} 有权限 '{permission_code}'")
            else:
                logger.warning(f"  - ❌ 用户 {user['username']} 没有权限 '{permission_code}'")
        else:
            # 显示用户的所有权限
            for perm in permissions:
                logger.info(f"    - {perm['name']} ({perm['code']})")

def check_specific_user_permissions(connection, username=None, user_id=None, permission_code=None):
    """检查特定用户的权限"""
    try:
        with connection.cursor() as cursor:
            if username:
                sql = "SELECT * FROM users WHERE username = %s"
                cursor.execute(sql, (username,))
                user = cursor.fetchone()
            elif user_id:
                sql = "SELECT * FROM users WHERE id = %s"
                cursor.execute(sql, (user_id,))
                user = cursor.fetchone()
            else:
                logger.error("必须提供用户名或用户ID")
                return
            
            if not user:
                logger.error(f"未找到用户: {username or user_id}")
                return
            
            logger.info(f"\n用户: {user['username']} (ID: {user['id']})")
            
            # 获取用户角色
            roles = get_user_roles(connection, user['id'])
            if not roles:
                logger.warning(f"  - 用户 {user['username']} 没有分配任何角色")
                return
            
            logger.info("  - 角色:")
            for role in roles:
                logger.info(f"    - {role['name']} (ID: {role['id']})")
                
                # 获取角色权限
                role_permissions = get_role_permissions(connection, role['id'])
                if not role_permissions:
                    logger.warning(f"      - 角色 {role['name']} 没有任何权限")
                    continue
                
                logger.info(f"      - 权限数量: {len(role_permissions)}")
                
                # 如果指定了权限代码，检查角色是否有该权限
                if permission_code:
                    has_permission = any(p['code'] == permission_code for p in role_permissions)
                    if has_permission:
                        logger.info(f"      - ✅ 角色 {role['name']} 有权限 '{permission_code}'")
                    else:
                        logger.warning(f"      - ❌ 角色 {role['name']} 没有权限 '{permission_code}'")
                else:
                    # 显示角色的所有权限
                    for perm in role_permissions:
                        logger.info(f"      - {perm['name']} ({perm['code']})")
            
            # 获取用户的所有权限
            permissions = get_user_permissions(connection, user['id'])
            if not permissions:
                logger.warning(f"  - 用户 {user['username']} 没有任何权限")
                return
            
            logger.info(f"\n  - 用户权限汇总 (共 {len(permissions)} 个):")
            
            # 如果指定了权限代码，检查用户是否有该权限
            if permission_code:
                has_permission = any(p['code'] == permission_code for p in permissions)
                if has_permission:
                    logger.info(f"    - ✅ 用户 {user['username']} 有权限 '{permission_code}'")
                else:
                    logger.warning(f"    - ❌ 用户 {user['username']} 没有权限 '{permission_code}'")
            else:
                # 显示用户的所有权限
                for perm in permissions:
                    logger.info(f"    - {perm['name']} ({perm['code']})")
    except Exception as e:
        logger.error(f"检查用户权限时发生错误: {str(e)}")

def fix_user_permissions(connection, username=None, user_id=None, role_id=None):
    """修复用户权限问题"""
    try:
        with connection.cursor() as cursor:
            # 获取用户
            if username:
                sql = "SELECT * FROM users WHERE username = %s"
                cursor.execute(sql, (username,))
                user = cursor.fetchone()
            elif user_id:
                sql = "SELECT * FROM users WHERE id = %s"
                cursor.execute(sql, (user_id,))
                user = cursor.fetchone()
            else:
                logger.error("必须提供用户名或用户ID")
                return False
            
            if not user:
                logger.error(f"未找到用户: {username or user_id}")
                return False
            
            # 如果提供了角色ID，为用户分配角色
            if role_id:
                # 检查角色是否存在
                sql = "SELECT * FROM roles WHERE id = %s"
                cursor.execute(sql, (role_id,))
                role = cursor.fetchone()
                
                if not role:
                    logger.error(f"未找到角色: {role_id}")
                    return False
                
                # 检查用户是否已有该角色
                sql = "SELECT * FROM user_roles WHERE user_id = %s AND role_id = %s"
                cursor.execute(sql, (user['id'], role_id))
                existing = cursor.fetchone()
                
                if existing:
                    logger.info(f"用户 {user['username']} 已经有角色 {role['name']}")
                else:
                    # 为用户分配角色
                    sql = "INSERT INTO user_roles (user_id, role_id, created_at, updated_at) VALUES (%s, %s, NOW(), NOW())"
                    cursor.execute(sql, (user['id'], role_id))
                    connection.commit()
                    logger.info(f"已为用户 {user['username']} 分配角色 {role['name']}")
                
                return True
            else:
                logger.error("必须提供角色ID")
                return False
    except Exception as e:
        logger.error(f"修复用户权限时发生错误: {str(e)}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='用户角色权限检查工具')
    parser.add_argument('--user', help='指定用户名')
    parser.add_argument('--user-id', type=int, help='指定用户ID')
    parser.add_argument('--permission', help='指定权限代码')
    parser.add_argument('--all-users', action='store_true', help='检查所有用户')
    parser.add_argument('--fix', action='store_true', help='修复权限问题')
    parser.add_argument('--role-id', type=int, help='指定角色ID（用于修复）')
    
    args = parser.parse_args()
    
    # 连接数据库
    connection = connect_to_database()
    if not connection:
        logger.error("无法连接到数据库，程序退出")
        sys.exit(1)
    
    try:
        if args.fix:
            if not (args.user or args.user_id):
                logger.error("修复权限需要指定用户名或用户ID")
                sys.exit(1)
            if not args.role_id:
                logger.error("修复权限需要指定角色ID")
                sys.exit(1)
            
            success = fix_user_permissions(connection, args.user, args.user_id, args.role_id)
            if success:
                logger.info("权限修复成功")
            else:
                logger.error("权限修复失败")
        elif args.all_users:
            check_all_users_permissions(connection, args.permission)
        elif args.user or args.user_id:
            check_specific_user_permissions(connection, args.user, args.user_id, args.permission)
        else:
            logger.error("请指定要检查的用户或使用 --all-users 检查所有用户")
            sys.exit(1)
    finally:
        connection.close()
        logger.info("数据库连接已关闭")

if __name__ == "__main__":
    main() 