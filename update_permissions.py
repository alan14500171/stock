#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
权限数据更新脚本
根据截图中的权限列表更新数据库中的权限数据
"""

import os
import sys
import pymysql
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('permission_update.log')
    ]
)
logger = logging.getLogger(__name__)

# 数据库配置
DB_CONFIG = {
    'host': '172.16.0.109',
    'port': 3306,
    'user': 'root',
    'password': 'Zxc000123',  # 本地数据库密码
    'db': 'stock',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# 权限数据
PERMISSIONS = [
    # 1. 股票管理模块
    {
        'id': 1,
        'name': '股票管理',
        'code': 'stock',
        'description': '股票管理相关功能',
        'type': 1,
        'parent_id': None,
        'path': '1',
        'level': 0,
        'sort_order': 1,
        'is_menu': 1,
        'icon': 'bi-graph-up',
        'component': None,
        'route_path': None
    },
    # 股票列表
    {
        'id': 2,
        'name': '股票列表',
        'code': 'stock:list',
        'description': '股票列表管理',
        'type': 2,
        'parent_id': 1,
        'path': '1/2',
        'level': 1,
        'sort_order': 1,
        'is_menu': 1,
        'icon': 'bi-list-ul',
        'component': 'views/stock/StockList.vue',
        'route_path': '/stock/list'
    },
    {
        'id': 3,
        'name': '查看股票',
        'code': 'stock:list:view',
        'description': '查看股票列表',
        'type': 3,
        'parent_id': 2,
        'path': '1/2/3',
        'level': 2,
        'sort_order': 1,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    {
        'id': 4,
        'name': '添加股票',
        'code': 'stock:list:add',
        'description': '添加新股票',
        'type': 3,
        'parent_id': 2,
        'path': '1/2/4',
        'level': 2,
        'sort_order': 2,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    {
        'id': 5,
        'name': '编辑股票',
        'code': 'stock:list:edit',
        'description': '编辑股票信息',
        'type': 3,
        'parent_id': 2,
        'path': '1/2/5',
        'level': 2,
        'sort_order': 3,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    {
        'id': 6,
        'name': '删除股票',
        'code': 'stock:list:delete',
        'description': '删除股票',
        'type': 3,
        'parent_id': 2,
        'path': '1/2/6',
        'level': 2,
        'sort_order': 4,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    # 持仓管理
    {
        'id': 7,
        'name': '持仓管理',
        'code': 'stock:holdings',
        'description': '股票持仓管理',
        'type': 2,
        'parent_id': 1,
        'path': '1/7',
        'level': 1,
        'sort_order': 2,
        'is_menu': 1,
        'icon': 'bi-briefcase',
        'component': 'views/stock/Holdings.vue',
        'route_path': '/stock/holdings'
    },
    {
        'id': 8,
        'name': '查看持仓',
        'code': 'stock:holdings:view',
        'description': '查看持仓列表',
        'type': 3,
        'parent_id': 7,
        'path': '1/7/8',
        'level': 2,
        'sort_order': 1,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    {
        'id': 9,
        'name': '导出持仓',
        'code': 'stock:holdings:export',
        'description': '导出持仓数据',
        'type': 3,
        'parent_id': 7,
        'path': '1/7/9',
        'level': 2,
        'sort_order': 2,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    
    # 2. 交易管理模块
    {
        'id': 10,
        'name': '交易管理',
        'code': 'transaction',
        'description': '交易管理相关功能',
        'type': 1,
        'parent_id': None,
        'path': '10',
        'level': 0,
        'sort_order': 2,
        'is_menu': 1,
        'icon': 'bi-currency-exchange',
        'component': None,
        'route_path': None
    },
    # 交易记录
    {
        'id': 11,
        'name': '交易记录',
        'code': 'transaction:records',
        'description': '交易记录管理',
        'type': 2,
        'parent_id': 10,
        'path': '10/11',
        'level': 1,
        'sort_order': 1,
        'is_menu': 1,
        'icon': 'bi-journal-text',
        'component': 'views/transaction/Records.vue',
        'route_path': '/transaction/records'
    },
    {
        'id': 12,
        'name': '查看交易',
        'code': 'transaction:records:view',
        'description': '查看交易记录',
        'type': 3,
        'parent_id': 11,
        'path': '10/11/12',
        'level': 2,
        'sort_order': 1,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    {
        'id': 13,
        'name': '添加交易',
        'code': 'transaction:records:add',
        'description': '添加新交易记录',
        'type': 3,
        'parent_id': 11,
        'path': '10/11/13',
        'level': 2,
        'sort_order': 2,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    {
        'id': 14,
        'name': '编辑交易',
        'code': 'transaction:records:edit',
        'description': '编辑交易记录',
        'type': 3,
        'parent_id': 11,
        'path': '10/11/14',
        'level': 2,
        'sort_order': 3,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    {
        'id': 15,
        'name': '删除交易',
        'code': 'transaction:records:delete',
        'description': '删除交易记录',
        'type': 3,
        'parent_id': 11,
        'path': '10/11/15',
        'level': 2,
        'sort_order': 4,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    {
        'id': 16,
        'name': '导出交易',
        'code': 'transaction:records:export',
        'description': '导出交易记录',
        'type': 3,
        'parent_id': 11,
        'path': '10/11/16',
        'level': 2,
        'sort_order': 5,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    # 交易统计
    {
        'id': 17,
        'name': '交易统计',
        'code': 'transaction:stats',
        'description': '交易统计分析',
        'type': 2,
        'parent_id': 10,
        'path': '10/17',
        'level': 1,
        'sort_order': 2,
        'is_menu': 1,
        'icon': 'bi-bar-chart',
        'component': 'views/transaction/Stats.vue',
        'route_path': '/transaction/stats'
    },
    {
        'id': 18,
        'name': '查看统计',
        'code': 'transaction:stats:view',
        'description': '查看交易统计数据',
        'type': 3,
        'parent_id': 17,
        'path': '10/17/18',
        'level': 2,
        'sort_order': 1,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    {
        'id': 19,
        'name': '导出统计',
        'code': 'transaction:stats:export',
        'description': '导出交易统计数据',
        'type': 3,
        'parent_id': 17,
        'path': '10/17/19',
        'level': 2,
        'sort_order': 2,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    
    # 3. 收益统计模块
    {
        'id': 20,
        'name': '收益统计',
        'code': 'profit',
        'description': '收益统计相关功能',
        'type': 1,
        'parent_id': None,
        'path': '20',
        'level': 0,
        'sort_order': 3,
        'is_menu': 1,
        'icon': 'bi-graph-up-arrow',
        'component': None,
        'route_path': None
    },
    # 收益总览
    {
        'id': 21,
        'name': '收益总览',
        'code': 'profit:overview',
        'description': '收益总览分析',
        'type': 2,
        'parent_id': 20,
        'path': '20/21',
        'level': 1,
        'sort_order': 1,
        'is_menu': 1,
        'icon': 'bi-clipboard-data',
        'component': 'views/profit/Overview.vue',
        'route_path': '/profit/overview'
    },
    {
        'id': 22,
        'name': '查看总览',
        'code': 'profit:overview:view',
        'description': '查看收益总览数据',
        'type': 3,
        'parent_id': 21,
        'path': '20/21/22',
        'level': 2,
        'sort_order': 1,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    {
        'id': 23,
        'name': '导出总览',
        'code': 'profit:overview:export',
        'description': '导出收益总览数据',
        'type': 3,
        'parent_id': 21,
        'path': '20/21/23',
        'level': 2,
        'sort_order': 2,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    # 收益详情
    {
        'id': 24,
        'name': '收益详情',
        'code': 'profit:details',
        'description': '收益详细分析',
        'type': 2,
        'parent_id': 20,
        'path': '20/24',
        'level': 1,
        'sort_order': 2,
        'is_menu': 1,
        'icon': 'bi-pie-chart',
        'component': 'views/profit/Details.vue',
        'route_path': '/profit/details'
    },
    {
        'id': 25,
        'name': '查看详情',
        'code': 'profit:details:view',
        'description': '查看收益详细数据',
        'type': 3,
        'parent_id': 24,
        'path': '20/24/25',
        'level': 2,
        'sort_order': 1,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    {
        'id': 26,
        'name': '导出详情',
        'code': 'profit:details:export',
        'description': '导出收益详细数据',
        'type': 3,
        'parent_id': 24,
        'path': '20/24/26',
        'level': 2,
        'sort_order': 2,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    
    # 4. 汇率管理模块
    {
        'id': 27,
        'name': '汇率管理',
        'code': 'exchange',
        'description': '汇率管理相关功能',
        'type': 1,
        'parent_id': None,
        'path': '27',
        'level': 0,
        'sort_order': 4,
        'is_menu': 1,
        'icon': 'bi-cash-coin',
        'component': None,
        'route_path': None
    },
    # 汇率列表
    {
        'id': 28,
        'name': '汇率列表',
        'code': 'exchange:rates',
        'description': '汇率列表管理',
        'type': 2,
        'parent_id': 27,
        'path': '27/28',
        'level': 1,
        'sort_order': 1,
        'is_menu': 1,
        'icon': 'bi-list-columns',
        'component': 'views/exchange/Rates.vue',
        'route_path': '/exchange/rates'
    },
    {
        'id': 29,
        'name': '查看汇率',
        'code': 'exchange:rates:view',
        'description': '查看汇率列表',
        'type': 3,
        'parent_id': 28,
        'path': '27/28/29',
        'level': 2,
        'sort_order': 1,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    {
        'id': 30,
        'name': '添加汇率',
        'code': 'exchange:rates:add',
        'description': '添加新汇率记录',
        'type': 3,
        'parent_id': 28,
        'path': '27/28/30',
        'level': 2,
        'sort_order': 2,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    {
        'id': 31,
        'name': '编辑汇率',
        'code': 'exchange:rates:edit',
        'description': '编辑汇率记录',
        'type': 3,
        'parent_id': 28,
        'path': '27/28/31',
        'level': 2,
        'sort_order': 3,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    {
        'id': 32,
        'name': '删除汇率',
        'code': 'exchange:rates:delete',
        'description': '删除汇率记录',
        'type': 3,
        'parent_id': 28,
        'path': '27/28/32',
        'level': 2,
        'sort_order': 4,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    # 汇率转换
    {
        'id': 33,
        'name': '汇率转换',
        'code': 'exchange:converter',
        'description': '汇率转换工具',
        'type': 2,
        'parent_id': 27,
        'path': '27/33',
        'level': 1,
        'sort_order': 2,
        'is_menu': 1,
        'icon': 'bi-arrow-left-right',
        'component': 'views/exchange/Converter.vue',
        'route_path': '/exchange/converter'
    },
    {
        'id': 34,
        'name': '使用转换器',
        'code': 'exchange:converter:use',
        'description': '使用汇率转换功能',
        'type': 3,
        'parent_id': 33,
        'path': '27/33/34',
        'level': 2,
        'sort_order': 1,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    
    # 5. 系统管理模块
    {
        'id': 35,
        'name': '系统管理',
        'code': 'system',
        'description': '系统管理相关功能',
        'type': 1,
        'parent_id': None,
        'path': '35',
        'level': 0,
        'sort_order': 5,
        'is_menu': 1,
        'icon': 'bi-gear',
        'component': None,
        'route_path': None
    },
    # 用户管理
    {
        'id': 36,
        'name': '用户管理',
        'code': 'system:user',
        'description': '用户管理相关功能',
        'type': 2,
        'parent_id': 35,
        'path': '35/36',
        'level': 1,
        'sort_order': 1,
        'is_menu': 1,
        'icon': 'bi-people',
        'component': 'views/system/User.vue',
        'route_path': '/system/user'
    },
    {
        'id': 37,
        'name': '查看用户',
        'code': 'system:user:view',
        'description': '查看用户列表',
        'type': 3,
        'parent_id': 36,
        'path': '35/36/37',
        'level': 2,
        'sort_order': 1,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    {
        'id': 38,
        'name': '添加用户',
        'code': 'system:user:add',
        'description': '添加新用户',
        'type': 3,
        'parent_id': 36,
        'path': '35/36/38',
        'level': 2,
        'sort_order': 2,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    {
        'id': 39,
        'name': '编辑用户',
        'code': 'system:user:edit',
        'description': '编辑用户信息',
        'type': 3,
        'parent_id': 36,
        'path': '35/36/39',
        'level': 2,
        'sort_order': 3,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    {
        'id': 40,
        'name': '删除用户',
        'code': 'system:user:delete',
        'description': '删除用户',
        'type': 3,
        'parent_id': 36,
        'path': '35/36/40',
        'level': 2,
        'sort_order': 4,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    {
        'id': 41,
        'name': '分配角色',
        'code': 'system:user:assign',
        'description': '为用户分配角色',
        'type': 3,
        'parent_id': 36,
        'path': '35/36/41',
        'level': 2,
        'sort_order': 5,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    # 角色管理
    {
        'id': 42,
        'name': '角色管理',
        'code': 'system:role',
        'description': '角色管理相关功能',
        'type': 2,
        'parent_id': 35,
        'path': '35/42',
        'level': 1,
        'sort_order': 2,
        'is_menu': 1,
        'icon': 'bi-person-badge',
        'component': 'views/system/Role.vue',
        'route_path': '/system/role'
    },
    {
        'id': 43,
        'name': '查看角色',
        'code': 'system:role:view',
        'description': '查看角色列表',
        'type': 3,
        'parent_id': 42,
        'path': '35/42/43',
        'level': 2,
        'sort_order': 1,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    {
        'id': 44,
        'name': '添加角色',
        'code': 'system:role:add',
        'description': '添加新角色',
        'type': 3,
        'parent_id': 42,
        'path': '35/42/44',
        'level': 2,
        'sort_order': 2,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    {
        'id': 45,
        'name': '编辑角色',
        'code': 'system:role:edit',
        'description': '编辑角色信息',
        'type': 3,
        'parent_id': 42,
        'path': '35/42/45',
        'level': 2,
        'sort_order': 3,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    {
        'id': 46,
        'name': '删除角色',
        'code': 'system:role:delete',
        'description': '删除角色',
        'type': 3,
        'parent_id': 42,
        'path': '35/42/46',
        'level': 2,
        'sort_order': 4,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    {
        'id': 47,
        'name': '分配权限',
        'code': 'system:role:assign',
        'description': '为角色分配权限',
        'type': 3,
        'parent_id': 42,
        'path': '35/42/47',
        'level': 2,
        'sort_order': 5,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    # 权限管理
    {
        'id': 48,
        'name': '权限管理',
        'code': 'system:permission',
        'description': '权限管理相关功能',
        'type': 2,
        'parent_id': 35,
        'path': '35/48',
        'level': 1,
        'sort_order': 3,
        'is_menu': 1,
        'icon': 'bi-shield-lock',
        'component': 'views/system/Permission.vue',
        'route_path': '/system/permission'
    },
    {
        'id': 49,
        'name': '查看权限',
        'code': 'system:permission:view',
        'description': '查看权限列表',
        'type': 3,
        'parent_id': 48,
        'path': '35/48/49',
        'level': 2,
        'sort_order': 1,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    {
        'id': 50,
        'name': '添加权限',
        'code': 'system:permission:add',
        'description': '添加新权限',
        'type': 3,
        'parent_id': 48,
        'path': '35/48/50',
        'level': 2,
        'sort_order': 2,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    {
        'id': 51,
        'name': '编辑权限',
        'code': 'system:permission:edit',
        'description': '编辑权限信息',
        'type': 3,
        'parent_id': 48,
        'path': '35/48/51',
        'level': 2,
        'sort_order': 3,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    {
        'id': 52,
        'name': '删除权限',
        'code': 'system:permission:delete',
        'description': '删除权限',
        'type': 3,
        'parent_id': 48,
        'path': '35/48/52',
        'level': 2,
        'sort_order': 4,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    # 系统设置
    {
        'id': 53,
        'name': '系统设置',
        'code': 'system:settings',
        'description': '系统设置功能',
        'type': 2,
        'parent_id': 35,
        'path': '35/53',
        'level': 1,
        'sort_order': 4,
        'is_menu': 1,
        'icon': 'bi-sliders',
        'component': 'views/system/Settings.vue',
        'route_path': '/system/settings'
    },
    {
        'id': 54,
        'name': '查看设置',
        'code': 'system:settings:view',
        'description': '查看系统设置',
        'type': 3,
        'parent_id': 53,
        'path': '35/53/54',
        'level': 2,
        'sort_order': 1,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    },
    {
        'id': 55,
        'name': '修改设置',
        'code': 'system:settings:edit',
        'description': '修改系统设置',
        'type': 3,
        'parent_id': 53,
        'path': '35/53/55',
        'level': 2,
        'sort_order': 2,
        'is_menu': 0,
        'icon': None,
        'component': None,
        'route_path': None
    }
]

def connect_db():
    """连接到数据库"""
    try:
        # 尝试连接到本地数据库
        connection = pymysql.connect(**DB_CONFIG)
        print("数据库连接成功！")
        return connection
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None

def update_permissions(connection):
    """更新权限数据"""
    try:
        with connection.cursor() as cursor:
            # 备份现有权限数据
            logger.info("备份现有权限数据")
            cursor.execute("DROP TABLE IF EXISTS permissions_backup")
            cursor.execute("CREATE TABLE IF NOT EXISTS permissions_backup LIKE permissions")
            cursor.execute("INSERT INTO permissions_backup SELECT * FROM permissions")
            connection.commit()
            
            # 清空现有权限关联
            logger.info("清空现有权限关联")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            cursor.execute("TRUNCATE TABLE role_permissions")
            cursor.execute("TRUNCATE TABLE permissions")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            connection.commit()
            
            # 插入权限数据
            logger.info("插入权限数据")
            for perm in PERMISSIONS:
                sql = """
                INSERT INTO permissions (
                    id, name, code, description, parent_id, path, 
                    level, sort_order, is_menu, icon, component, route_path
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """
                cursor.execute(sql, (
                    perm['id'], perm['name'], perm['code'], perm['description'],
                    perm['parent_id'], perm['path'], perm['level'],
                    perm['sort_order'], perm['is_menu'], perm['icon'], 
                    perm['component'], perm['route_path']
                ))
            connection.commit()
            
            # 重置自增ID
            logger.info("重置自增ID")
            cursor.execute("ALTER TABLE permissions AUTO_INCREMENT = 56")
            connection.commit()
            
            # 为超级管理员角色分配所有权限
            logger.info("为超级管理员角色分配所有权限")
            cursor.execute("SELECT id FROM roles WHERE name = 'admin'")
            admin_role = cursor.fetchone()
            if admin_role:
                admin_role_id = admin_role['id']
                cursor.execute("SELECT id FROM permissions")
                permissions = cursor.fetchall()
                for perm in permissions:
                    cursor.execute(
                        "INSERT INTO role_permissions (role_id, permission_id) VALUES (%s, %s)",
                        (admin_role_id, perm['id'])
                    )
                connection.commit()
            else:
                logger.warning("未找到超级管理员角色")
            
            # 为普通用户角色分配基本权限
            logger.info("为普通用户角色分配基本权限")
            cursor.execute("SELECT id FROM roles WHERE name = 'user'")
            user_role = cursor.fetchone()
            if user_role:
                user_role_id = user_role['id']
                basic_permissions = ['system:user:view', 'system:role:view', 'system:permission:view']
                for code in basic_permissions:
                    cursor.execute("SELECT id FROM permissions WHERE code = %s", (code,))
                    perm = cursor.fetchone()
                    if perm:
                        cursor.execute(
                            "INSERT INTO role_permissions (role_id, permission_id) VALUES (%s, %s)",
                            (user_role_id, perm['id'])
                        )
                connection.commit()
            else:
                logger.warning("未找到普通用户角色")
            
            # 统计结果
            cursor.execute("SELECT COUNT(*) as count FROM permissions")
            total_permissions = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM role_permissions WHERE role_id = %s", 
                          (admin_role_id if admin_role else 0,))
            admin_permissions = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM role_permissions WHERE role_id = %s", 
                          (user_role_id if user_role else 0,))
            user_permissions = cursor.fetchone()['count']
            
            logger.info(f"权限数据更新成功！总权限数: {total_permissions}, "
                       f"超级管理员权限数: {admin_permissions}, "
                       f"普通用户权限数: {user_permissions}")
            
            return {
                'total_permissions': total_permissions,
                'admin_permissions': admin_permissions,
                'user_permissions': user_permissions
            }
    except Exception as e:
        logger.error(f"更新权限数据失败: {str(e)}")
        connection.rollback()
        sys.exit(1)

def main():
    """主函数"""
    logger.info("开始更新权限数据")
    
    # 提示用户检查数据库配置
    print("\n" + "="*50)
    print("使用以下数据库连接信息:")
    print(f"  主机: {DB_CONFIG['host']}")
    print(f"  端口: {DB_CONFIG['port']}")
    print(f"  用户: {DB_CONFIG['user']}")
    print(f"  数据库: {DB_CONFIG['db']}")
    print("="*50 + "\n")
    
    # 连接数据库
    connection = connect_db()
    if not connection:
        logger.error("无法连接到数据库，请检查连接信息")
        return
    
    try:
        # 更新权限数据
        stats = update_permissions(connection)
        
        # 输出结果
        print("\n" + "="*50)
        print("权限数据更新成功！")
        print(f"总权限数: {stats['total_permissions']}")
        print(f"超级管理员权限数: {stats['admin_permissions']}")
        print(f"普通用户权限数: {stats['user_permissions']}")
        print("="*50 + "\n")
        
    except Exception as e:
        logger.error(f"更新权限数据失败: {str(e)}")
        print(f"更新权限数据失败: {e}")
    finally:
        # 关闭数据库连接
        connection.close()
        logger.info("数据库连接已关闭")

if __name__ == "__main__":
    main() 