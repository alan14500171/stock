"""
应用配置模块
"""

import os
from datetime import timedelta

class Config:
    """基础配置类"""
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev'
    PORT = 9099
    HOST = '127.0.0.1'
    DEBUG = False
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:Zxc000123@172.16.0.109:3306/stock'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'max_overflow': 40,
        'pool_timeout': 60,
        'pool_recycle': 1800,
        'pool_pre_ping': True,
        'connect_args': {
            'connect_timeout': 30,
            'read_timeout': 30,
            'write_timeout': 30,
            'charset': 'utf8mb4'
        }
    }
    
    # Session配置
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # 模板自动重载
    TEMPLATES_AUTO_RELOAD = True

class DevelopmentConfig(Config):
    """开发环境配置类"""
    DEBUG = True
    HOST = '127.0.0.1'
    PORT = 9099
    
    # 开发环境数据库配置
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:Zxc000123@172.16.0.109:3306/stock'
    
    # 开发环境日志配置
    LOG_LEVEL = 'DEBUG'
    LOG_TO_STDOUT = True

class TestingConfig(Config):
    """测试环境配置类"""
    TESTING = True
    DEBUG = True
    
    # 测试环境数据库配置
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:Zxc000123@172.16.0.109:3306/stock_test'
    
    # 测试环境日志配置
    LOG_LEVEL = 'DEBUG'
    LOG_TO_STDOUT = True

class ProductionConfig(Config):
    """生产环境配置类"""
    DEBUG = False
    
    # 生产环境数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root:Zxc000123@172.16.0.109:3306/stock'
    
    # 生产环境日志配置
    LOG_LEVEL = 'INFO'
    LOG_TO_STDOUT = False

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 