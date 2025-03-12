"""
数据库配置模块
"""
import os
import pymysql
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# 从环境变量获取数据库配置
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = int(os.environ.get('DB_PORT', 3306))
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'your_password_here')
DB_NAME = os.environ.get('DB_NAME', 'stock')
DB_CHARSET = os.environ.get('DB_CHARSET', 'utf8mb4')

# 数据库基础配置
DB_CONFIG = {
    'host': DB_HOST,
    'user': DB_USER,
    'password': DB_PASSWORD,
    'port': DB_PORT,
    'charset': DB_CHARSET,
}

# 不同环境的数据库名配置
DB_NAMES = {
    'development': DB_NAME,
    'testing': 'stock_test',
    'production': DB_NAME
}

# SQLAlchemy 配置
SQLALCHEMY_CONFIG = {
    'pool_size': 20,
    'max_overflow': 40,
    'pool_timeout': 60,
    'pool_recycle': 1800,
    'pool_pre_ping': True,
    'connect_args': {
        'connect_timeout': 30,
        'read_timeout': 30,
        'write_timeout': 30,
        'charset': DB_CHARSET
    }
}

def get_db_config(env: str = 'production') -> Dict[str, Any]:
    """获取数据库配置"""
    configs = {
        'development': {
            'host': DB_HOST,
            'port': DB_PORT,
            'user': DB_USER,
            'password': DB_PASSWORD,
            'db': DB_NAME,
            'charset': DB_CHARSET
        },
        'testing': {
            'host': DB_HOST,
            'port': DB_PORT,
            'user': DB_USER,
            'password': DB_PASSWORD,
            'db': 'stock_test',
            'charset': DB_CHARSET
        },
        'production': {
            'host': DB_HOST,
            'port': DB_PORT,
            'user': DB_USER,
            'password': DB_PASSWORD,
            'db': DB_NAME,
            'charset': DB_CHARSET
        }
    }
    
    # 获取配置
    config = configs.get(env, configs['production'])
    
    # 尝试检测实际数据库名称（处理大小写问题）
    try:
        # 连接到MySQL服务器，不指定数据库
        conn = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            charset=config['charset'],
            connect_timeout=5  # 添加超时设置
        )
        
        with conn.cursor() as cursor:
            # 列出所有数据库
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            
            # 检查数据库是否存在（不区分大小写）
            target_db = config['db']
            db_exists = False
            for db in databases:
                if db[0].lower() == target_db.lower():
                    if db[0] != target_db:
                        logger.warning(f"数据库名称大小写不一致: 配置中为 '{target_db}'，实际为 '{db[0]}'")
                        # 更新配置中的数据库名称
                        config['db'] = db[0]
                    db_exists = True
                    break
            
            if not db_exists:
                logger.warning(f"数据库 '{target_db}' 不存在，可能需要创建数据库")
        
        conn.close()
    except Exception as e:
        logger.warning(f"检查数据库名称时出错: {str(e)}")
        logger.warning("将使用配置中的默认值继续")
    
    return config

def get_sqlalchemy_uri(env: str = 'production') -> str:
    """获取SQLAlchemy连接URI"""
    config = get_db_config(env)
    return f"mysql+pymysql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['db']}?charset={config['charset']}"

def get_sqlalchemy_config() -> Dict[str, Any]:
    """获取SQLAlchemy配置"""
    return {
        'pool_size': 20,         # 保持连接池基本大小
        'max_overflow': 40,      # 允许的最大连接溢出数
        'pool_timeout': 60,      # 等待连接的超时时间
        'pool_recycle': 600,     # 减少回收时间到10分钟，更频繁地刷新连接
        'pool_pre_ping': True,   # 在使用连接前ping一下，确保连接有效
        'connect_args': {
            'connect_timeout': 10,      # 减少连接超时，更快失败
            'read_timeout': 30,
            'write_timeout': 30,
            'charset': DB_CHARSET,
            # 增加重连次数和等待时间
            'client_flag': 2,           # 启用CLIENT_FOUND_ROWS标志
            'autocommit': True,         # 自动提交事务
            'program_name': 'stock-backend', # 添加程序名称标识
        }
    }

# 添加一个新的测试连接功能，用于主动检查连接是否可用
def test_db_connection(config=None) -> bool:
    """测试数据库连接是否正常"""
    if config is None:
        config = get_db_config('production')
        
    try:
        # 尝试建立连接
        conn = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['db'],
            charset=config['charset'],
            connect_timeout=5
        )
        
        # 执行简单查询
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
        # 关闭连接
        conn.close()
        
        # 检查结果
        return result is not None and result[0] == 1
    except Exception as e:
        logger.error(f"数据库连接测试失败: {str(e)}")
        return False 