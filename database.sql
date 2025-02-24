-- 创建数据库
CREATE DATABASE IF NOT EXISTS stock DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE stock;

-- 修改数据库字符集
ALTER DATABASE stock CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 修改表字符集
ALTER TABLE users CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE stocks CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE stock_transactions CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE stock_transaction_details CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE exchange_rates CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT NOT NULL AUTO_INCREMENT,
    username VARCHAR(80) NOT NULL,
    password_hash VARCHAR(255) DEFAULT NULL,
    created_at DATETIME DEFAULT NULL,
    is_active TINYINT(1) DEFAULT '1',
    last_login DATETIME DEFAULT NULL,
    updated_at DATETIME DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户管理表';

-- 股票表
CREATE TABLE IF NOT EXISTS stocks (
    id INT NOT NULL AUTO_INCREMENT,
    code VARCHAR(20) NOT NULL,
    market VARCHAR(10) NOT NULL,
    code_name VARCHAR(100) NOT NULL,
    google_name VARCHAR(200) DEFAULT NULL,
    created_at DATETIME DEFAULT NULL,
    updated_at DATETIME DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uix_code_market (code, market)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票基础信息表';

-- 股票交易表
CREATE TABLE IF NOT EXISTS stock_transactions (
    id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    transaction_code VARCHAR(20) NOT NULL,
    stock_code VARCHAR(20) NOT NULL,
    market VARCHAR(10) NOT NULL,
    transaction_type VARCHAR(10) NOT NULL,
    transaction_date DATETIME NOT NULL,
    total_amount FLOAT DEFAULT NULL,
    total_quantity INT DEFAULT NULL,
    exchange_rate FLOAT DEFAULT NULL,
    broker_fee FLOAT DEFAULT NULL,
    stamp_duty FLOAT DEFAULT NULL,
    transaction_levy FLOAT DEFAULT NULL,
    trading_fee FLOAT DEFAULT NULL,
    clearing_fee FLOAT DEFAULT NULL,
    deposit_fee FLOAT DEFAULT NULL,
    prev_quantity INT DEFAULT NULL COMMENT '交易前持仓数量',
    prev_cost DECIMAL(10,2) DEFAULT NULL COMMENT '交易前总成本',
    prev_avg_cost DECIMAL(10,2) DEFAULT NULL COMMENT '交易前移动加权平均价',
    current_quantity INT DEFAULT NULL COMMENT '交易后持仓数量',
    current_cost DECIMAL(10,2) DEFAULT NULL COMMENT '交易后总成本',
    current_avg_cost DECIMAL(10,2) DEFAULT NULL COMMENT '交易后移动加权平均价',
    total_fees DECIMAL(10,2) DEFAULT NULL COMMENT '总费用',
    net_amount DECIMAL(10,2) DEFAULT NULL COMMENT '净金额',
    average_cost DECIMAL(10,2) DEFAULT NULL COMMENT '平均成本',
    running_quantity INT DEFAULT NULL COMMENT '累计数量',
    running_cost DECIMAL(10,2) DEFAULT NULL COMMENT '累计成本',
    current_average_cost DECIMAL(10,2) DEFAULT NULL COMMENT '当前平均成本',
    realized_profit DECIMAL(10,2) DEFAULT NULL COMMENT '已实现盈亏',
    profit_rate DECIMAL(10,2) DEFAULT NULL COMMENT '盈亏比率',
    created_at DATETIME DEFAULT NULL,
    updated_at DATETIME DEFAULT NULL,
    PRIMARY KEY (id),
    KEY user_id (user_id),
    CONSTRAINT stock_transactions_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票交易记录表';

-- 交易明细表
CREATE TABLE IF NOT EXISTS stock_transaction_details (
    id INT NOT NULL AUTO_INCREMENT,
    transaction_id INT NOT NULL,
    quantity INT NOT NULL,
    price FLOAT NOT NULL,
    created_at DATETIME DEFAULT NULL,
    PRIMARY KEY (id),
    KEY transaction_id (transaction_id),
    CONSTRAINT stock_transaction_details_ibfk_1 FOREIGN KEY (transaction_id) REFERENCES stock_transactions (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='交易明细表';

-- 汇率表
CREATE TABLE IF NOT EXISTS exchange_rates (
    id INT NOT NULL AUTO_INCREMENT,
    currency VARCHAR(10) NOT NULL,
    rate_date DATE NOT NULL,
    rate FLOAT NOT NULL,
    source VARCHAR(20) NOT NULL,
    created_at DATETIME DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uix_currency_date (currency, rate_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='汇率记录表';

-- 添加注释
ALTER TABLE users COMMENT '用户管理表';
ALTER TABLE stocks COMMENT '股票基础信息表';
ALTER TABLE stock_transactions COMMENT '股票交易记录表';
ALTER TABLE stock_transaction_details COMMENT '交易明细表';
ALTER TABLE exchange_rates COMMENT '汇率记录表'; 