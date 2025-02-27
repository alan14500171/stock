#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库连接测试脚本
用于测试MySQL数据库连接
"""

import pymysql
import sys

# 数据库配置
DB_CONFIG = {
    'host': '172.16.0.109',
    'port': 3306,
    'user': 'root',
    'password': '000123',
    'db': 'stock',
    'charset': 'utf8mb4'
}

def test_connection():
    """测试数据库连接"""
    print("\n" + "="*50)
    print("测试数据库连接...")
    print(f"  主机: {DB_CONFIG['host']}")
    print(f"  端口: {DB_CONFIG['port']}")
    print(f"  用户: {DB_CONFIG['user']}")
    print(f"  数据库: {DB_CONFIG['db']}")
    print("="*50)
    
    # 尝试不同的连接方式
    connection_methods = [
        {
            "description": "方式1: 使用标准连接",
            "params": {
                "host": DB_CONFIG['host'],
                "port": DB_CONFIG['port'],
                "user": DB_CONFIG['user'],
                "password": DB_CONFIG['password'],
                "charset": 'utf8mb4'
            }
        },
        {
            "description": "方式2: 不指定端口",
            "params": {
                "host": DB_CONFIG['host'],
                "user": DB_CONFIG['user'],
                "password": DB_CONFIG['password'],
                "charset": 'utf8mb4'
            }
        },
        {
            "description": "方式3: 使用connect_timeout参数",
            "params": {
                "host": DB_CONFIG['host'],
                "port": DB_CONFIG['port'],
                "user": DB_CONFIG['user'],
                "password": DB_CONFIG['password'],
                "charset": 'utf8mb4',
                "connect_timeout": 10
            }
        }
    ]
    
    for method in connection_methods:
        print(f"\n尝试 {method['description']}...")
        try:
            # 尝试连接
            connection = pymysql.connect(**method['params'])
            
            # 如果连接成功，获取服务器信息
            with connection.cursor() as cursor:
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()
                print(f"连接成功！MySQL版本: {version[0]}")
                
                # 检查数据库是否存在
                cursor.execute("SHOW DATABASES")
                databases = cursor.fetchall()
                db_exists = False
                print("\n可用数据库:")
                for db in databases:
                    db_name = list(db.values())[0]
                    print(f"  - {db_name}")
                    if db_name.lower() == DB_CONFIG['db'].lower():
                        db_exists = True
                
                if db_exists:
                    print(f"\n数据库 '{DB_CONFIG['db']}' 存在")
                else:
                    print(f"\n警告: 数据库 '{DB_CONFIG['db']}' 不存在")
            
            connection.close()
            return True
        except Exception as e:
            print(f"连接失败: {e}")
    
    print("\n所有连接方式均失败")
    print("\n可能的原因:")
    print("  1. 服务器地址或端口错误")
    print("  2. 用户名或密码错误")
    print("  3. MySQL服务器未运行")
    print("  4. 防火墙阻止了连接")
    print("  5. 用户没有远程连接权限")
    print("\n请检查以下内容:")
    print("  - 确认服务器地址和端口是否正确")
    print("  - 确认用户名和密码是否正确")
    print("  - 确认MySQL服务器是否允许远程连接")
    print("  - 确认用户是否有权限从当前IP地址连接")
    return False

def main():
    """主函数"""
    print("开始测试数据库连接")
    test_connection()

if __name__ == "__main__":
    main() 