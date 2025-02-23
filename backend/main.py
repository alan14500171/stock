from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from config.database import db

# 导入路由
from routes.auth import auth_bp
from routes.stock import stock_bp
from routes.profit import profit_bp

def create_app():
    # 创建应用实例
    app = Flask(__name__, static_folder='../frontend/dist')

    # 配置
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev_key'
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['JSON_AS_ASCII'] = False  # 支持中文
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 最大请求大小16MB

    # CORS配置
    CORS(app, supports_credentials=True, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:9009",
                "http://127.0.0.1:9009"
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"]
        }
    })

    # 注册蓝图
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(stock_bp, url_prefix='/api/stock')
    app.register_blueprint(profit_bp, url_prefix='/api/profit')

    # 配置日志
    if not os.path.exists('logs'):
        os.makedirs('logs')

    log_file = os.path.join('logs', f'backend_{datetime.now().strftime("%Y%m%d")}.log')
    handler = RotatingFileHandler(log_file, maxBytes=10000000, backupCount=5)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    # 初始化数据库连接
    try:
        db_config = {
            'host': '172.16.0.109',
            'user': 'root',
            'password': 'Zxc000123',
            'database': 'stock',
            'port': 3306
        }
        db.init_pool(db_config)
        app.logger.info("数据库连接池初始化成功")
    except Exception as e:
        app.logger.error(f"数据库连接池初始化失败: {str(e)}")
        raise

    # 健康检查端点
    @app.route('/api/health')
    def health_check():
        return jsonify({
            'status': 'ok',
            'timestamp': datetime.now().isoformat(),
            'db_connected': db.is_connected()
        })

    # 错误处理
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            'success': False,
            'message': '请求的资源不存在'
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'服务器错误: {str(error)}')
        return jsonify({
            'success': False,
            'message': '服务器内部错误'
        }), 500

    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({
            'success': False,
            'message': '请求数据太大'
        }), 413

    # 前端路由处理
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        if path and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')

    return app

if __name__ == '__main__':
    try:
        app = create_app()
        app.logger.info('应用启动成功')
        app.run(
            host='127.0.0.1',
            port=9099,
            debug=True,
            use_reloader=True
        )
    except Exception as e:
        logging.error(f'应用启动失败: {str(e)}')
        raise 