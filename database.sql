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
    id INT NOT NULL AUTO_INCREMENT  COMMENT '用户ID',
    username VARCHAR(80) NOT NULL COMMENT '用户名',
    password_hash VARCHAR(255) DEFAULT NULL COMMENT '密码哈希值',
    created_at DATETIME DEFAULT NULL COMMENT '创建时间',
    is_active TINYINT(1) DEFAULT '1' COMMENT '是否活跃',
    last_login DATETIME DEFAULT NULL COMMENT '最后登录时间',
    updated_at DATETIME DEFAULT NULL COMMENT '更新时间',
    PRIMARY KEY (id),
    UNIQUE KEY username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户管理表';

-- 股票表
CREATE TABLE IF NOT EXISTS stocks (
    id INT NOT NULL AUTO_INCREMENT COMMENT '股票ID',
    code VARCHAR(20) NOT NULL COMMENT '股票代码',
    market VARCHAR(10) NOT NULL COMMENT '市场',
    code_name VARCHAR(100) NOT NULL COMMENT '股票名称',
    google_name VARCHAR(200) DEFAULT NULL COMMENT '谷歌股票名称',
    created_at DATETIME DEFAULT NULL COMMENT '创建时间',
    updated_at DATETIME DEFAULT NULL COMMENT '更新时间',
    PRIMARY KEY (id),
    UNIQUE KEY uix_code_market (code, market)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票基础信息表';

-- 股票交易表
CREATE TABLE IF NOT EXISTS stock_transactions (
    id INT NOT NULL AUTO_INCREMENT COMMENT '交易ID',
    user_id INT NOT NULL COMMENT '用户ID',
    transaction_code VARCHAR(20) NOT NULL COMMENT '交易代码',
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    market VARCHAR(10) NOT NULL COMMENT '市场',
    transaction_type VARCHAR(10) NOT NULL COMMENT '交易类型',
    transaction_date DATETIME NOT NULL COMMENT '交易日期',
    total_amount FLOAT DEFAULT NULL COMMENT '总金额',
    total_quantity INT DEFAULT NULL COMMENT '总数量',
    broker_fee FLOAT DEFAULT NULL COMMENT '佣金',
    stamp_duty FLOAT DEFAULT NULL COMMENT '印花税',
    transaction_levy FLOAT DEFAULT NULL COMMENT '交易征费',
    trading_fee FLOAT DEFAULT NULL COMMENT '交易费',
    deposit_fee FLOAT DEFAULT NULL COMMENT '存入证券费',
    prev_quantity INT DEFAULT NULL COMMENT '交易前持仓数量',
    prev_cost DECIMAL(10,2) DEFAULT NULL COMMENT '交易前总成本',
    prev_avg_cost DECIMAL(10,2) DEFAULT NULL COMMENT '交易前移动加权平均价',
    current_quantity INT DEFAULT NULL COMMENT '交易后持仓数量',
    current_cost DECIMAL(10,2) DEFAULT NULL COMMENT '交易后总成本',
    current_avg_cost DECIMAL(10,2) DEFAULT NULL COMMENT '交易后移动加权平均价',
    total_fees DECIMAL(10,2) DEFAULT NULL COMMENT '总费用',
    net_amount DECIMAL(10,2) DEFAULT NULL COMMENT '净金额',
    running_quantity INT DEFAULT NULL COMMENT '累计数量',
    running_cost DECIMAL(10,2) DEFAULT NULL COMMENT '累计成本',
    realized_profit DECIMAL(10,2) DEFAULT NULL COMMENT '已实现盈亏',
    profit_rate DECIMAL(10,2) DEFAULT NULL COMMENT '盈亏比率',
    created_at DATETIME DEFAULT NULL COMMENT '创建时间',
    updated_at DATETIME DEFAULT NULL COMMENT '更新时间',
    PRIMARY KEY (id),
    KEY user_id (user_id),
    CONSTRAINT stock_transactions_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票交易记录表';

-- 交易明细表
CREATE TABLE IF NOT EXISTS stock_transaction_details (
    id INT NOT NULL AUTO_INCREMENT COMMENT '交易明细ID',
    transaction_id INT NOT NULL COMMENT '交易ID',
    quantity INT NOT NULL COMMENT '数量',
    price FLOAT NOT NULL COMMENT '价格',
    created_at DATETIME DEFAULT NULL COMMENT '创建时间',
    PRIMARY KEY (id),
    KEY transaction_id (transaction_id),
    CONSTRAINT stock_transaction_details_ibfk_1 FOREIGN KEY (transaction_id) REFERENCES stock_transactions (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='交易明细表';

-- 汇率表
CREATE TABLE IF NOT EXISTS exchange_rates (
    id INT NOT NULL AUTO_INCREMENT COMMENT '汇率ID',
    currency VARCHAR(10) NOT NULL COMMENT '货币',
    rate_date DATE NOT NULL COMMENT '汇率日期',
    rate FLOAT NOT NULL COMMENT '汇率',
    source VARCHAR(20) NOT NULL COMMENT '来源',
    created_at DATETIME DEFAULT NULL COMMENT '创建时间',
    PRIMARY KEY (id),
    UNIQUE KEY uix_currency_date (currency, rate_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='汇率记录表';

-- 添加注释
ALTER TABLE users COMMENT '用户管理表';
ALTER TABLE stocks COMMENT '股票基础信息表';
ALTER TABLE stock_transactions COMMENT '股票交易记录表';
ALTER TABLE stock_transaction_details COMMENT '交易明细表';
ALTER TABLE exchange_rates COMMENT '汇率记录表'; 