window.APP_CONFIG = {
    // 使用相对路径，让 Nginx 处理代理
    API_BASE_URL: '/api',
    APP_VERSION: '1.0.0',
    ENV: 'production',
    // 调试配置
    DEBUG: true,
    TIMEOUT: 30000,
    ENABLE_LOGS: true,
    DEFAULT_LOCALE: 'zh-CN',
    // 重试配置
    RETRY_COUNT: 3,
    RETRY_DELAY: 1000,
    // 健康检查配置
    HEALTH_CHECK_ENABLED: true,
    HEALTH_CHECK_INTERVAL: 30000,
    // API 配置
    API_TIMEOUT: 30000,
    API_RETRY_COUNT: 3,
    API_RETRY_DELAY: 1000,
    // CORS 配置
    CORS_ENABLED: true,
    ALLOWED_ORIGINS: [
        'http://localhost:9009',
        'http://127.0.0.1:9009',
        'http://alanpar.myds.me:9009'
    ]
}; 