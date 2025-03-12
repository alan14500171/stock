# 数据库结构文档

## 表: exchange_rates

### 表结构

| 字段名 | 类型 | 可空 | 键 | 默认值 | 额外 |
|--------|------|------|-----|--------|------|
| id | int | NO | PRI | NULL | auto_increment |
| currency | varchar(10) | NO | MUL | NULL |  |
| rate_date | date | NO |  | NULL |  |
| rate | float | NO |  | NULL |  |
| source | varchar(20) | NO |  | NULL |  |
| created_at | datetime | YES |  | NULL |  |

### 样本数据

| id | currency | rate_date | rate | source | created_at |
|---|---|---|---|---|---|
| 22 | USD | 2025-01-21 | 7.77376 | EXCHANGE_RATES_API | 2025-02-14 15:19:54 |
| 23 | USD | 2025-02-15 | 7.78916 | EXCHANGE_RATES_API | 2025-02-14 17:57:07 |
| 24 | USD | 2025-01-15 | 7.77376 | EXCHANGE_RATES_API | 2025-02-15 18:20:01 |
| 25 | USD | 2025-02-16 | 7.7841 | EXCHANGE_RATES_API | 2025-02-15 18:21:22 |
| 26 | USD | 2025-01-16 | 7.77376 | EXCHANGE_RATES_API | 2025-02-15 18:23:35 |
| 27 | USD | 2025-01-24 | 7.77376 | EXCHANGE_RATES_API | 2025-02-15 18:25:51 |
| 28 | USD | 2025-01-27 | 7.77376 | EXCHANGE_RATES_API | 2025-02-16 07:04:19 |
| 29 | USD | 2025-01-25 | 7.77376 | EXCHANGE_RATES_API | 2025-02-16 07:12:02 |
| 30 | USD | 2025-01-28 | 7.77376 | EXCHANGE_RATES_API | 2025-02-16 07:27:20 |
| 31 | USD | 2025-01-31 | 7.77376 | EXCHANGE_RATES_API | 2025-02-16 07:39:17 |

## 表: holders

### 表结构

| 字段名 | 类型 | 可空 | 键 | 默认值 | 额外 |
|--------|------|------|-----|--------|------|
| id | int | NO | PRI | NULL | auto_increment |
| name | varchar(100) | NO | UNI | NULL |  |
| type | varchar(20) | YES |  | individual |  |
| user_id | int | YES | MUL | NULL |  |
| status | tinyint(1) | YES |  | 1 |  |
| created_at | datetime | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
| updated_at | datetime | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED on update CURRENT_TIMESTAMP |

### 样本数据

| id | name | type | user_id | status | created_at | updated_at |
|---|---|---|---|---|---|---|
| 1 | alan | individual | 3 | 1 | 2025-02-28 03:30:34 | 2025-02-28 16:39:14 |
| 2 | lili | individual | 4 | 1 | 2025-02-28 03:30:34 | 2025-02-28 16:39:17 |

## 表: permissions

### 表结构

| 字段名 | 类型 | 可空 | 键 | 默认值 | 额外 |
|--------|------|------|-----|--------|------|
| id | int | NO | PRI | NULL | auto_increment |
| name | varchar(100) | NO |  | NULL |  |
| code | varchar(100) | NO | UNI | NULL |  |
| description | text | YES |  | NULL |  |
| type | tinyint(1) | YES |  | 3 |  |
| parent_id | int | YES | MUL | NULL |  |
| path | varchar(255) | YES | MUL | NULL |  |
| level | int | NO |  | 0 |  |
| sort_order | int | NO |  | 0 |  |
| is_menu | tinyint(1) | NO |  | 0 |  |
| icon | varchar(50) | YES |  | NULL |  |
| component | varchar(255) | YES |  | NULL |  |
| route_path | varchar(255) | YES |  | NULL |  |
| created_at | timestamp | NO |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
| updated_at | timestamp | NO |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED on update CURRENT_TIMESTAMP |

### 样本数据

| id | name | code | description | type | parent_id | path | level | sort_order | is_menu | icon | component | route_path | created_at | updated_at |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 股票管理 | stock | 股票管理相关功能 | 1 | NULL | 1 | 0 | 1 | 1 | bi-graph-up | NULL | NULL | 2025-02-28 01:57:03 | 2025-03-03 03:19:24 |
| 2 | 股票列表 | stock:list | 股票列表管理 | 2 | 1 | 1/2 | 1 | 1 | 1 | bi-list-ul | views/StockManager.vue | /stock | 2025-02-28 01:57:03 | 2025-03-03 03:19:25 |
| 3 | 查看股票 | stock:list:view | 查看股票列表 | 3 | 2 | 1/2/3 | 2 | 1 | 0 | NULL | NULL | NULL | 2025-02-28 01:57:03 | 2025-02-28 01:57:03 |
| 4 | 添加股票 | stock:list:add | 添加新股票 | 3 | 2 | 1/2/4 | 2 | 2 | 0 | NULL | NULL | NULL | 2025-02-28 01:57:03 | 2025-02-28 01:57:03 |
| 5 | 编辑股票 | stock:list:edit | 编辑股票信息 | 3 | 2 | 1/2/5 | 2 | 3 | 0 | NULL | NULL | NULL | 2025-02-28 01:57:03 | 2025-02-28 01:57:03 |
| 6 | 删除股票 | stock:list:delete | 删除股票 | 3 | 2 | 1/2/6 | 2 | 4 | 0 | NULL | NULL | NULL | 2025-02-28 01:57:03 | 2025-02-28 01:57:03 |
| 7 | 持仓管理 | stock:holdings | 股票持仓管理 | 2 | 1 | 1/7 | 1 | 2 | 1 | bi-briefcase | views/StockManager.vue | /stock | 2025-02-28 01:57:03 | 2025-03-03 03:19:27 |
| 8 | 查看持仓 | stock:holdings:view | 查看持仓列表 | 3 | 7 | 1/7/8 | 2 | 1 | 0 | NULL | NULL | NULL | 2025-02-28 01:57:03 | 2025-02-28 01:57:03 |
| 9 | 导出持仓 | stock:holdings:export | 导出持仓数据 | 3 | 7 | 1/7/9 | 2 | 2 | 0 | NULL | NULL | NULL | 2025-02-28 01:57:03 | 2025-02-28 01:57:03 |
| 10 | 交易管理 | transaction | 交易管理相关功能 | 1 | NULL | 10 | 0 | 2 | 1 | bi-currency-exchange | NULL | NULL | 2025-02-28 01:57:03 | 2025-03-03 03:19:28 |

## 表: role_permissions

### 表结构

| 字段名 | 类型 | 可空 | 键 | 默认值 | 额外 |
|--------|------|------|-----|--------|------|
| id | int | NO | PRI | NULL | auto_increment |
| role_id | int | NO | MUL | NULL |  |
| permission_id | int | NO | MUL | NULL |  |

### 样本数据

| id | role_id | permission_id |
|---|---|---|
| 1 | 6 | 1 |
| 6 | 6 | 2 |
| 8 | 6 | 3 |
| 9 | 6 | 4 |
| 10 | 6 | 5 |
| 11 | 6 | 6 |
| 7 | 6 | 7 |
| 12 | 6 | 8 |
| 13 | 6 | 9 |
| 2 | 6 | 10 |

## 表: roles

### 表结构

| 字段名 | 类型 | 可空 | 键 | 默认值 | 额外 |
|--------|------|------|-----|--------|------|
| id | int | NO | PRI | NULL | auto_increment |
| name | varchar(50) | NO | UNI | NULL |  |
| description | text | YES |  | NULL |  |
| created_at | timestamp | NO |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
| updated_at | timestamp | NO |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED on update CURRENT_TIMESTAMP |

### 样本数据

| id | name | description | created_at | updated_at |
|---|---|---|---|---|
| 6 | admin | 超级管理员 | 2025-02-27 16:59:55 | 2025-02-27 16:59:55 |
| 7 | user | 普通用户 | 2025-02-27 16:59:55 | 2025-02-27 16:59:55 |

## 表: stock_transaction_details

### 表结构

| 字段名 | 类型 | 可空 | 键 | 默认值 | 额外 |
|--------|------|------|-----|--------|------|
| id | int | NO | PRI | NULL | auto_increment |
| transaction_id | int | NO | MUL | NULL |  |
| quantity | int | NO |  | NULL |  |
| price | float | NO |  | NULL |  |
| created_at | datetime | YES |  | NULL |  |

### 样本数据

| id | transaction_id | quantity | price | created_at |
|---|---|---|---|---|
| 174 | 110 | 2 | 415.97 | 2025-02-24 21:05:18 |
| 175 | 110 | 1 | 415.97 | 2025-02-24 21:05:18 |
| 176 | 110 | 2 | 415.98 | 2025-02-24 21:05:18 |
| 177 | 110 | 25 | 415.99 | 2025-02-24 21:05:18 |
| 178 | 111 | 2 | 414.26 | 2025-02-24 21:06:32 |
| 179 | 111 | 1 | 414.27 | 2025-02-24 21:06:32 |
| 180 | 111 | 12 | 414.31 | 2025-02-24 21:06:33 |
| 181 | 112 | 25 | 414.59 | 2025-02-24 21:27:54 |
| 182 | 112 | 20 | 414.58 | 2025-02-24 21:27:54 |
| 183 | 113 | 5 | 43.29 | 2025-02-24 21:29:25 |

## 表: stock_transactions

### 表结构

| 字段名 | 类型 | 可空 | 键 | 默认值 | 额外 |
|--------|------|------|-----|--------|------|
| id | int | NO | PRI | NULL | auto_increment |
| user_id | int | NO | MUL | NULL |  |
| transaction_code | varchar(20) | NO |  | NULL |  |
| stock_code | varchar(20) | NO |  | NULL |  |
| market | varchar(10) | NO |  | NULL |  |
| transaction_type | varchar(10) | NO |  | NULL |  |
| transaction_date | datetime | NO |  | NULL |  |
| total_amount | float | YES |  | NULL |  |
| total_quantity | int | YES |  | NULL |  |
| broker_fee | float | YES |  | NULL |  |
| stamp_duty | float | YES |  | NULL |  |
| transaction_levy | float | YES |  | NULL |  |
| trading_fee | float | YES |  | NULL |  |
| deposit_fee | float | YES |  | NULL |  |
| prev_quantity | int | YES |  | NULL |  |
| prev_cost | decimal(10,2) | YES |  | NULL |  |
| prev_avg_cost | decimal(10,2) | YES |  | NULL |  |
| current_quantity | int | YES |  | NULL |  |
| current_cost | decimal(10,2) | YES |  | NULL |  |
| current_avg_cost | decimal(10,2) | YES |  | NULL |  |
| total_fees | decimal(10,2) | YES |  | NULL |  |
| net_amount | decimal(10,2) | YES |  | NULL |  |
| running_quantity | int | YES |  | NULL |  |
| running_cost | decimal(10,2) | YES |  | NULL |  |
| realized_profit | decimal(10,2) | YES |  | NULL |  |
| profit_rate | decimal(10,2) | YES |  | NULL |  |
| created_at | datetime | YES |  | NULL |  |
| updated_at | datetime | YES |  | NULL |  |
| currency | varchar(10) | YES |  | CNY |  |
| realized_pnl | decimal(10,2) | YES |  | 0.00 |  |
| realized_pnl_ratio | decimal(10,2) | YES |  | 0.00 |  |
| has_splits | tinyint(1) | YES |  | 0 |  |
| avg_price | decimal(10,4) | YES |  | NULL |  |

### 样本数据

| id | user_id | transaction_code | stock_code | market | transaction_type | transaction_date | total_amount | total_quantity | broker_fee | stamp_duty | transaction_levy | trading_fee | deposit_fee | prev_quantity | prev_cost | prev_avg_cost | current_quantity | current_cost | current_avg_cost | total_fees | net_amount | running_quantity | running_cost | realized_profit | profit_rate | created_at | updated_at | currency | realized_pnl | realized_pnl_ratio | has_splits | avg_price |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 110 | 3 | P-779926 | TSLA | USA | buy | 2025-01-15 00:00:00 | 12479.6 | 30 | 31.2 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0.00 | 0.00 | 30 | 12510.80 | 417.03 | 31.20 | 12510.80 | 30 | 12510.80 | 0.00 | 0.00 | 2025-02-24 21:05:17 | 2025-02-26 20:56:34 | CNY | 0.00 | 0.00 | 1 | 415.9867 |
| 111 | 3 | P-800444 | TSLA | USA | buy | 2025-01-16 00:00:00 | 6214.51 | 15 | 15.54 | 0.0 | 0.0 | 0.0 | 0.0 | 30 | 12510.80 | 417.03 | 45 | 18740.85 | 416.46 | 15.54 | 6230.05 | 45 | 18740.85 | 0.00 | 0.00 | 2025-02-24 21:06:31 | 2025-02-26 20:56:34 | CNY | 0.00 | 0.00 | 1 | 414.3007 |
| 112 | 3 | S-137277 | TSLA | USA | sell | 2025-01-24 00:00:00 | 18656.3 | 45 | 46.65 | 0.0 | 0.0 | 0.52 | 0.0 | 45 | 18740.85 | 416.46 | 0 | 0.00 | 0.00 | 47.17 | 18609.13 | 0 | 0.00 | -131.72 | -0.70 | 2025-02-24 21:27:53 | 2025-02-26 20:56:34 | CNY | 0.00 | 0.00 | 1 | 414.5845 |
| 113 | 3 | P-157925 | OKLO | USA | buy | 2025-01-24 00:00:00 | 12994.1 | 300 | 32.49 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0.00 | 0.00 | 300 | 13026.59 | 43.42 | 32.49 | 13026.59 | 300 | 13026.59 | 0.00 | 0.00 | 2025-02-24 21:29:25 | 2025-02-26 20:56:35 | CNY | 0.00 | 0.00 | 1 | 43.3137 |
| 114 | 3 | S-138037 | OKLO | USA | sell | 2025-01-24 00:00:00 | 12900.0 | 300 | 32.25 | 0.0 | 0.0 | 0.36 | 0.0 | 300 | 13026.59 | 43.42 | 0 | 0.00 | 0.00 | 32.61 | 12867.39 | 0 | 0.00 | -159.20 | -1.22 | 2025-02-24 21:30:25 | 2025-02-26 20:56:35 | CNY | 0.00 | 0.00 | 1 | 43.0000 |
| 115 | 3 | P-236969 | OKLO | USA | buy | 2025-01-31 00:00:00 | 13469.6 | 300 | 33.68 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0.00 | 0.00 | 300 | 13503.28 | 45.01 | 33.68 | 13503.28 | 300 | 13503.28 | 0.00 | 0.00 | 2025-02-24 21:31:24 | 2025-02-26 20:56:35 | CNY | 0.00 | 0.00 | 1 | 44.8987 |
| 116 | 3 | S-231915 | OKLO | USA | sell | 2025-02-03 00:00:00 | 13112.0 | 300 | 32.79 | 0.0 | 0.0 | 0.37 | 0.0 | 300 | 13503.28 | 45.01 | 0 | 0.00 | 0.00 | 33.16 | 13078.84 | 0 | 0.00 | -424.44 | -3.14 | 2025-02-24 21:32:14 | 2025-02-26 20:56:35 | CNY | 0.00 | 0.00 | 1 | 43.7067 |
| 117 | 3 | P-341863 | OKLO | USA | buy | 2025-02-05 00:00:00 | 9924.0 | 200 | 24.81 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0.00 | 0.00 | 200 | 9948.81 | 49.74 | 24.81 | 9948.81 | 200 | 9948.81 | 0.00 | 0.00 | 2025-02-24 21:33:43 | 2025-02-26 20:56:36 | CNY | 0.00 | 0.00 | 1 | 49.6200 |
| 118 | 3 | S-297980 | OKLO | USA | sell | 2025-02-05 00:00:00 | 5000.0 | 100 | 12.5 | 0.0 | 0.0 | 0.14 | 0.0 | 200 | 9948.81 | 49.74 | 100 | 4974.41 | 49.74 | 12.64 | 4987.36 | 100 | 4974.41 | 12.96 | 0.26 | 2025-02-24 21:34:56 | 2025-02-26 20:56:36 | CNY | 0.00 | 0.00 | 1 | 50.0000 |
| 119 | 3 | S-297982 | OKLO | USA | sell | 2025-02-05 00:00:00 | 5011.0 | 100 | 12.53 | 0.0 | 0.0 | 0.14 | 0.0 | 100 | 4974.41 | 49.74 | 0 | 0.00 | 0.00 | 12.67 | 4998.33 | 0 | 0.00 | 23.93 | 0.48 | 2025-02-24 21:35:29 | 2025-02-26 20:56:36 | CNY | 0.00 | 0.00 | 1 | 50.1100 |

## 表: stocks

### 表结构

| 字段名 | 类型 | 可空 | 键 | 默认值 | 额外 |
|--------|------|------|-----|--------|------|
| id | int | NO | PRI | NULL | auto_increment |
| code | varchar(20) | NO | MUL | NULL |  |
| market | varchar(10) | NO |  | NULL |  |
| code_name | varchar(100) | NO |  | NULL |  |
| google_name | varchar(200) | YES |  | NULL |  |
| created_at | datetime | YES |  | NULL |  |
| updated_at | datetime | YES |  | NULL |  |

### 样本数据

| id | code | market | code_name | google_name | created_at | updated_at |
|---|---|---|---|---|---|---|
| 3 | 00981 | HK | 中芯国际 | 0981:HKG | 2025-02-14 15:19:15 | 2025-02-14 15:19:15 |
| 6 | 09992 | HK | 泡泡玛特 | 9992:HKG | 2025-02-14 19:52:24 | 2025-02-14 19:52:24 |
| 7 | TSLA | USA | 特斯拉 | TSLA:NASDAQ | 2025-02-15 18:15:14 | 2025-02-15 18:15:14 |
| 14 | OKLO | USA | Oklo Inc | OKLO:NYSE | 2025-02-16 06:24:11 | 2025-02-16 06:24:11 |
| 15 | SMR | USA | Nuscale Power Corp | SMR:NYSE | 2025-02-16 07:45:04 | 2025-02-16 07:45:04 |
| 16 | NVDA | USA | 英伟达 | NVDA:NASDAQ | 2025-02-16 07:46:01 | 2025-02-16 07:46:01 |
| 17 | VST | USA | Vistra Corp | VST:NYSE | 2025-02-16 07:46:33 | 2025-02-16 07:46:33 |
| 18 | KC | USA | 金山云 | KC:NASDAQ | 2025-02-16 07:47:01 | 2025-02-16 07:47:01 |
| 19 | LEU | USA | Centrus Energy Corp | LEU:NYSEAMERICAN | 2025-02-16 19:31:28 | 2025-02-16 19:31:28 |
| 24 | BABA | USA | 阿里巴巴集团 | BABA:NYSE | 2025-02-25 02:17:23 | 2025-02-25 02:17:23 |

## 表: transaction_splits

### 表结构

| 字段名 | 类型 | 可空 | 键 | 默认值 | 额外 |
|--------|------|------|-----|--------|------|
| id | int | NO | PRI | NULL | auto_increment |
| original_transaction_id | int | NO | MUL | NULL |  |
| holder_id | int | YES | MUL | NULL |  |
| holder_name | varchar(100) | YES |  | NULL |  |
| split_ratio | decimal(10,4) | NO |  | NULL |  |
| transaction_date | date | NO | MUL | NULL |  |
| stock_id | int | YES |  | NULL |  |
| stock_code | varchar(20) | NO | MUL | NULL |  |
| stock_name | varchar(100) | NO |  | NULL |  |
| market | varchar(20) | NO |  | NULL |  |
| transaction_code | varchar(50) | YES |  | NULL |  |
| transaction_type | varchar(10) | NO |  | NULL |  |
| total_amount | float | NO |  | NULL |  |
| total_quantity | int | NO |  | NULL |  |
| broker_fee | float | YES |  | NULL |  |
| stamp_duty | float | YES |  | NULL |  |
| transaction_levy | float | YES |  | NULL |  |
| trading_fee | float | YES |  | NULL |  |
| deposit_fee | float | YES |  | NULL |  |
| prev_quantity | int | YES |  | NULL |  |
| prev_cost | decimal(10,2) | YES |  | NULL |  |
| prev_avg_cost | decimal(10,2) | YES |  | NULL |  |
| current_quantity | int | YES |  | NULL |  |
| current_cost | decimal(10,2) | YES |  | NULL |  |
| current_avg_cost | decimal(10,2) | YES |  | NULL |  |
| total_fees | decimal(10,2) | YES |  | NULL |  |
| net_amount | decimal(10,2) | YES |  | NULL |  |
| running_quantity | int | YES |  | NULL |  |
| running_cost | decimal(10,2) | YES |  | NULL |  |
| realized_profit | decimal(10,2) | YES |  | NULL |  |
| profit_rate | decimal(10,2) | YES |  | NULL |  |
| exchange_rate | decimal(10,4) | YES |  | 1.0000 |  |
| remarks | text | YES |  | NULL |  |
| created_at | timestamp | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
| updated_at | timestamp | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED on update CURRENT_TIMESTAMP |
| avg_price | decimal(10,4) | YES |  | NULL |  |

### 样本数据

| id | original_transaction_id | holder_id | holder_name | split_ratio | transaction_date | stock_id | stock_code | stock_name | market | transaction_code | transaction_type | total_amount | total_quantity | broker_fee | stamp_duty | transaction_levy | trading_fee | deposit_fee | prev_quantity | prev_cost | prev_avg_cost | current_quantity | current_cost | current_avg_cost | total_fees | net_amount | running_quantity | running_cost | realized_profit | profit_rate | exchange_rate | remarks | created_at | updated_at | avg_price |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 99 | 110 | 1 | alan | 1.0000 | 2025-01-15 | 0 | TSLA | 特斯拉 | USA | P-779926 | buy | 12479.6 | 30 | 31.2 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0.00 | 0.00 | 30 | 12510.80 | 417.03 | 31.20 | -12510.80 | 30 | 12510.80 | 0.00 | 0.00 | 1.0000 | 系统自动创建的100%分单 | 2025-02-28 17:19:14 | 2025-02-28 21:02:35 | 415.9867 |
| 100 | 111 | 1 | alan | 1.0000 | 2025-01-16 | 0 | TSLA | 特斯拉 | USA | P-800444 | buy | 6214.51 | 15 | 15.54 | 0.0 | 0.0 | 0.0 | 0.0 | 30 | 12510.80 | 417.03 | 45 | 18740.85 | 416.46 | 15.54 | -6230.05 | 45 | 18740.85 | 0.00 | 0.00 | 1.0000 | 系统自动创建的100%分单 | 2025-02-28 17:19:14 | 2025-02-28 21:02:35 | 414.3007 |
| 101 | 144 | 1 | alan | 1.0000 | 2025-01-21 | 0 | 00981 | 中芯国际 | HK | P-847256 | buy | 40850.0 | 1000 | 102.12 | 41.0 | 1.16 | 2.31 | 30.0 | 0 | 0.00 | 0.00 | 1000 | 41026.59 | 41.03 | 176.59 | -41026.59 | 1000 | 41026.59 | 0.00 | 0.00 | 1.0000 | 系统自动创建的100%分单 | 2025-02-28 17:19:16 | 2025-02-28 21:02:30 | 40.8500 |
| 102 | 145 | 1 | alan | 1.0000 | 2025-01-21 | 0 | 00981 | 中芯国际 | HK | P-847731 | buy | 40500.0 | 1000 | 101.25 | 41.0 | 1.15 | 2.29 | 30.0 | 1000 | 41026.59 | 41.03 | 2000 | 81702.28 | 40.85 | 175.69 | -40675.69 | 2000 | 81702.28 | 0.00 | 0.00 | 1.0000 | 系统自动创建的100%分单 | 2025-02-28 17:19:16 | 2025-02-28 21:02:30 | 40.5000 |
| 103 | 112 | 1 | alan | 1.0000 | 2025-01-24 | 0 | TSLA | 特斯拉 | USA | S-137277 | sell | 18656.3 | 45 | 46.65 | 0.0 | 0.0 | 0.52 | 0.0 | 45 | 18740.85 | 416.46 | 0 | 0.00 | 0.00 | 47.17 | 18609.13 | 0 | 0.00 | -131.72 | -0.70 | 1.0000 | 系统自动创建的100%分单 | 2025-02-28 17:19:16 | 2025-03-01 14:30:10 | 414.5845 |
| 104 | 113 | 1 | alan | 1.0000 | 2025-01-24 | 0 | OKLO | Oklo Inc | USA | P-157925 | buy | 12994.1 | 300 | 32.49 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0.00 | 0.00 | 300 | 13026.59 | 43.42 | 32.49 | -13026.59 | 300 | 13026.59 | 0.00 | 0.00 | 1.0000 | 系统自动创建的100%分单 | 2025-02-28 17:19:17 | 2025-02-28 21:02:34 | 43.3137 |
| 105 | 114 | 1 | alan | 1.0000 | 2025-01-24 | 0 | OKLO | Oklo Inc | USA | S-138037 | sell | 12900.0 | 300 | 32.25 | 0.0 | 0.0 | 0.36 | 0.0 | 300 | 13026.59 | 43.42 | 0 | 0.00 | 0.00 | 32.61 | 12867.39 | 0 | 0.00 | -159.20 | -1.22 | 1.0000 | 系统自动创建的100%分单 | 2025-02-28 17:19:17 | 2025-03-01 14:30:04 | 43.0000 |
| 106 | 203 | 1 | alan | 1.0000 | 2025-01-24 | 0 | 09992 | 泡泡玛特 | HK | P-142562 | buy | 36660.0 | 400 | 100.0 | 37.0 | 1.04 | 2.07 | 0.0 | 0 | 0.00 | 0.00 | 400 | 36800.11 | 92.00 | 140.11 | -36800.11 | 400 | 36800.11 | 0.00 | 0.00 | 1.0000 | 系统自动创建的100%分单 | 2025-02-28 17:19:17 | 2025-02-28 21:02:33 | 91.6500 |
| 107 | 147 | 1 | alan | 1.0000 | 2025-01-27 | 0 | 00981 | 中芯国际 | HK | S-155875 | sell | 80400.0 | 2000 | 201.0 | 81.0 | 2.29 | 4.54 | 0.0 | 2000 | 81702.28 | 40.85 | 0 | 0.00 | 0.00 | 288.83 | 80111.17 | 0 | 0.00 | -1591.11 | -1.95 | 1.0000 | 系统自动创建的100%分单 | 2025-02-28 17:19:18 | 2025-03-01 14:29:33 | 40.2000 |
| 108 | 148 | 1 | alan | 1.0000 | 2025-01-27 | 0 | 09992 | 泡泡玛特 | HK | S-156096 | sell | 37200.0 | 400 | 100.0 | 38.0 | 1.06 | 2.1 | 0.0 | 400 | 36800.11 | 92.00 | 0 | 0.00 | 0.00 | 141.16 | 37058.84 | 0 | 0.00 | 258.73 | 0.70 | 1.0000 | 系统自动创建的100%分单 | 2025-02-28 17:19:18 | 2025-03-01 14:29:53 | 93.0000 |

## 表: user_roles

### 表结构

| 字段名 | 类型 | 可空 | 键 | 默认值 | 额外 |
|--------|------|------|-----|--------|------|
| id | int | NO | PRI | NULL | auto_increment |
| user_id | int | NO | MUL | NULL |  |
| role_id | int | NO | MUL | NULL |  |

### 样本数据

| id | user_id | role_id |
|---|---|---|
| 2 | 3 | 6 |
| 3 | 4 | 7 |

## 表: users

### 表结构

| 字段名 | 类型 | 可空 | 键 | 默认值 | 额外 |
|--------|------|------|-----|--------|------|
| id | int | NO | PRI | NULL | auto_increment |
| username | varchar(80) | NO | UNI | NULL |  |
| display_name | varchar(100) | YES |  | NULL |  |
| email | varchar(100) | YES |  | NULL |  |
| avatar | varchar(255) | YES |  | NULL |  |
| password_hash | varchar(255) | YES |  | NULL |  |
| created_at | datetime | YES |  | NULL |  |
| is_active | tinyint(1) | YES |  | 1 |  |
| last_login | datetime | YES |  | NULL |  |
| updated_at | datetime | YES |  | NULL |  |

### 样本数据

| id | username | display_name | email | avatar | password_hash | created_at | is_active | last_login | updated_at |
|---|---|---|---|---|---|---|---|---|---|
| 3 | alan | 艾伦 | NULL | NULL | $2b$12$RdjrxWbNyXHEPmS1XE8y4OLAX2zbK0XUPzpFnPHi08bkcJqOtsLpS | 2025-02-15 18:11:22 | 1 | 2025-03-11 18:40:57 | NULL |
| 4 | lili | lili |  | NULL | $2b$12$FJoonRULoAe1b5qhlo56NOiWBuH1lFwXkLzeTlBUEiA1KKA6s4NHO | 2025-02-28 03:21:54 | 1 | 2025-03-11 18:18:08 | NULL |

