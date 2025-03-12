-- 数据库结构创建脚本

CREATE DATABASE IF NOT EXISTS `stock` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE `stock`;

-- 表结构: exchange_rates
CREATE TABLE `exchange_rates` (
  `id` int NOT NULL AUTO_INCREMENT,
  `currency` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `rate_date` date NOT NULL,
  `rate` float NOT NULL,
  `source` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uix_currency_date` (`currency`,`rate_date`)
) ENGINE=InnoDB AUTO_INCREMENT=47 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='汇率记录表';

-- 表结构: holders
CREATE TABLE `holders` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '持有人ID',
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '持有人姓名',
  `type` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT 'individual' COMMENT '类型：individual-个人，institution-机构',
  `user_id` int DEFAULT NULL COMMENT '关联的系统用户ID',
  `status` tinyint(1) DEFAULT '1' COMMENT '状态：0-禁用，1-启用',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_name` (`name`),
  KEY `idx_user_id` (`user_id`),
  CONSTRAINT `fk_holder_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='持有人表';

-- 表结构: permissions
CREATE TABLE `permissions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `code` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `type` tinyint(1) DEFAULT '3' COMMENT '权限类型：1-模块，2-菜单，3-按钮，4-数据，5-接口',
  `parent_id` int DEFAULT NULL,
  `path` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `level` int NOT NULL DEFAULT '0',
  `sort_order` int NOT NULL DEFAULT '0',
  `is_menu` tinyint(1) NOT NULL DEFAULT '0',
  `icon` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `component` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `route_path` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  KEY `idx_permissions_parent_id` (`parent_id`),
  KEY `idx_permissions_path` (`path`),
  KEY `idx_permissions_code` (`code`),
  CONSTRAINT `permissions_ibfk_1` FOREIGN KEY (`parent_id`) REFERENCES `permissions` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=68 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 表结构: role_permissions
CREATE TABLE `role_permissions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `role_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `role_id` (`role_id`,`permission_id`),
  KEY `idx_role_permissions_role_id` (`role_id`),
  KEY `idx_role_permissions_permission_id` (`permission_id`),
  CONSTRAINT `role_permissions_ibfk_1` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON DELETE CASCADE,
  CONSTRAINT `role_permissions_ibfk_2` FOREIGN KEY (`permission_id`) REFERENCES `permissions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=95 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 表结构: roles
CREATE TABLE `roles` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 表结构: stock_transaction_details
CREATE TABLE `stock_transaction_details` (
  `id` int NOT NULL AUTO_INCREMENT,
  `transaction_id` int NOT NULL,
  `quantity` int NOT NULL,
  `price` float NOT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `transaction_id` (`transaction_id`),
  CONSTRAINT `stock_transaction_details_ibfk_1` FOREIGN KEY (`transaction_id`) REFERENCES `stock_transactions` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=389 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='交易明细表';

-- 表结构: stock_transactions
CREATE TABLE `stock_transactions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `transaction_code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `stock_code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `market` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `transaction_type` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `transaction_date` datetime NOT NULL,
  `total_amount` float DEFAULT NULL,
  `total_quantity` int DEFAULT NULL,
  `broker_fee` float DEFAULT NULL,
  `stamp_duty` float DEFAULT NULL,
  `transaction_levy` float DEFAULT NULL,
  `trading_fee` float DEFAULT NULL,
  `deposit_fee` float DEFAULT NULL,
  `prev_quantity` int DEFAULT NULL COMMENT '交易前持仓数量',
  `prev_cost` decimal(10,2) DEFAULT NULL COMMENT '交易前总成本',
  `prev_avg_cost` decimal(10,2) DEFAULT NULL COMMENT '交易前移动加权平均价',
  `current_quantity` int DEFAULT NULL COMMENT '交易后持仓数量',
  `current_cost` decimal(10,2) DEFAULT NULL COMMENT '交易后总成本',
  `current_avg_cost` decimal(10,2) DEFAULT NULL COMMENT '交易后移动加权平均价',
  `total_fees` decimal(10,2) DEFAULT NULL COMMENT '总费用',
  `net_amount` decimal(10,2) DEFAULT NULL COMMENT '净金额',
  `running_quantity` int DEFAULT NULL COMMENT '累计数量',
  `running_cost` decimal(10,2) DEFAULT NULL COMMENT '累计成本',
  `realized_profit` decimal(10,2) DEFAULT NULL COMMENT '已实现盈亏',
  `profit_rate` decimal(10,2) DEFAULT NULL COMMENT '盈亏比率',
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `currency` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT 'CNY' COMMENT '货币',
  `realized_pnl` decimal(10,2) DEFAULT '0.00' COMMENT '已实现盈亏',
  `realized_pnl_ratio` decimal(10,2) DEFAULT '0.00' COMMENT '盈亏比率（%）',
  `has_splits` tinyint(1) DEFAULT '0' COMMENT '是否有分单记录：0-无，1-有',
  `avg_price` decimal(10,4) DEFAULT NULL COMMENT '平均价格',
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `stock_transactions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=284 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票交易记录表';

-- 表结构: stocks
CREATE TABLE `stocks` (
  `id` int NOT NULL AUTO_INCREMENT,
  `code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `market` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `code_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `google_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uix_code_market` (`code`,`market`)
) ENGINE=InnoDB AUTO_INCREMENT=37 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票基础信息表';

-- 表结构: transaction_splits
CREATE TABLE `transaction_splits` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `original_transaction_id` int NOT NULL COMMENT '原始交易ID',
  `holder_id` int DEFAULT NULL COMMENT '持有人ID',
  `holder_name` varchar(100) DEFAULT NULL COMMENT '持有人名称',
  `split_ratio` decimal(10,4) NOT NULL COMMENT '分摊比例',
  `transaction_date` date NOT NULL COMMENT '交易日期',
  `stock_id` int DEFAULT NULL COMMENT '股票ID',
  `stock_code` varchar(20) NOT NULL COMMENT '股票代码',
  `stock_name` varchar(100) NOT NULL COMMENT '股票名称',
  `market` varchar(20) NOT NULL COMMENT '市场',
  `transaction_code` varchar(50) DEFAULT NULL COMMENT '交易编号',
  `transaction_type` varchar(10) NOT NULL COMMENT '交易类型(买入/卖出)',
  `total_amount` float NOT NULL COMMENT '总金额',
  `total_quantity` int NOT NULL COMMENT '总数量',
  `broker_fee` float DEFAULT NULL COMMENT '佣金',
  `stamp_duty` float DEFAULT NULL COMMENT '印花税',
  `transaction_levy` float DEFAULT NULL COMMENT '交易征费',
  `trading_fee` float DEFAULT NULL COMMENT '交易费',
  `deposit_fee` float DEFAULT NULL COMMENT '存入证券费',
  `prev_quantity` int DEFAULT NULL COMMENT '交易前持仓数量',
  `prev_cost` decimal(10,2) DEFAULT NULL COMMENT '交易前总成本',
  `prev_avg_cost` decimal(10,2) DEFAULT NULL COMMENT '交易前移动加权平均价',
  `current_quantity` int DEFAULT NULL COMMENT '交易后持仓数量',
  `current_cost` decimal(10,2) DEFAULT NULL COMMENT '交易后总成本',
  `current_avg_cost` decimal(10,2) DEFAULT NULL COMMENT '交易后移动加权平均价',
  `total_fees` decimal(10,2) DEFAULT NULL COMMENT '总费用',
  `net_amount` decimal(10,2) DEFAULT NULL COMMENT '净金额',
  `running_quantity` int DEFAULT NULL COMMENT '累计数量',
  `running_cost` decimal(10,2) DEFAULT NULL COMMENT '累计成本',
  `realized_profit` decimal(10,2) DEFAULT NULL COMMENT '已实现盈亏',
  `profit_rate` decimal(10,2) DEFAULT NULL COMMENT '盈亏比率',
  `exchange_rate` decimal(10,4) DEFAULT '1.0000' COMMENT '汇率',
  `remarks` text COMMENT '备注',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `avg_price` decimal(10,4) DEFAULT NULL COMMENT '平均价格',
  PRIMARY KEY (`id`),
  KEY `idx_original_transaction` (`original_transaction_id`),
  KEY `idx_holder` (`holder_id`),
  KEY `idx_stock` (`stock_code`,`market`),
  KEY `idx_transaction_date` (`transaction_date`),
  CONSTRAINT `fk_original_transaction_id` FOREIGN KEY (`original_transaction_id`) REFERENCES `stock_transactions` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_ts_holder_id` FOREIGN KEY (`holder_id`) REFERENCES `holders` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=258 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='交易分单记录';

-- 表结构: user_roles
CREATE TABLE `user_roles` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `role_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`,`role_id`),
  KEY `idx_user_roles_user_id` (`user_id`),
  KEY `idx_user_roles_role_id` (`role_id`),
  CONSTRAINT `user_roles_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `user_roles_ibfk_2` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 表结构: users
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `display_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '显示名称',
  `email` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '电子邮箱（不使用）',
  `avatar` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '头像',
  `password_hash` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  `last_login` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户管理表';

