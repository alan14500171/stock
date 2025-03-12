import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    # 创建logs目录（如果不存在）
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 设置日志文件路径
    log_file = os.path.join(log_dir, 'app.log')
    
    # 创建日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 设置文件处理器
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.ERROR)  # 仅记录ERROR级别及以上的日志到文件
    
    # 设置控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.ERROR)  # 仅显示ERROR级别及以上的日志到控制台
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.ERROR)  # 设置为ERROR级别，过滤掉INFO和DEBUG级别的日志
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # 设置Flask和其他库的日志级别
    logging.getLogger('werkzeug').setLevel(logging.ERROR)  # 修改为ERROR级别，减少HTTP请求日志
    logging.getLogger('sqlalchemy').setLevel(logging.ERROR)  # 修改为ERROR级别，减少SQL查询日志 