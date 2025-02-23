# 股票交易管理系统

一个基于 Python Flask 和 Vue.js 的股票交易管理系统。

## 项目结构

```
.
├── frontend/                # 前端项目目录
│   ├── src/                # 源代码
│   │   ├── components/     # 通用组件
│   │   ├── views/         # 页面组件
│   │   ├── router/        # 路由配置
│   │   ├── composables/   # 组合式函数
│   │   └── main.js        # 入口文件
│   ├── public/            # 静态资源
│   ├── index.html         # HTML 模板
│   └── package.json       # 项目配置
│
├── backend/               # 后端项目目录
│   ├── config/           # 配置文件
│   │   ├── __init__.py
│   │   ├── config.py     # 主配置文件
│   │   ├── mysql.cnf     # 数据库配置
│   │   └── database.py   # 数据库连接配置
│   ├── routes/           # API 路由
│   │   ├── auth.py       # 认证相关
│   │   ├── stock.py      # 股票相关
│   │   └── profit.py     # 盈利统计
│   ├── models/           # 数据模型
│   ├── services/         # 业务逻辑
│   ├── utils/            # 工具函数
│   ├── scripts/          # 脚本文件
│   ├── tests/            # 测试文件
│   ├── main.py          # 主程序入口
│   └── requirements.txt  # Python 依赖
│
├── logs/                 # 日志文件
├── database.sql          # 数据库结构
└── README.md            # 项目说明
```

## 开发环境设置

### 后端设置

1. 创建并激活虚拟环境：
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置数据库：
```bash
mysql -u root -p < database.sql
```

4. 启动后端服务（默认端口 9099）：
```bash
python main.py
```

### 前端设置

1. 安装依赖：
```bash
cd frontend
npm install
```

2. 启动开发服务器（默认端口 9009）：
```bash
npm run dev
```

## 主要功能

- 股票交易记录管理
- 盈亏统计分析
- 持仓监控
- 交易费用计算
- 数据导出

## 技术栈

### 前端
- Vue 3
- Vue Router
- Bootstrap 5
- Axios

### 后端
- Python 3.8+
- Flask
- MySQL
- SQLAlchemy

## 开发规范

1. 代码风格
   - 前端遵循 Vue 3 组合式 API 风格
   - 后端遵循 PEP 8 规范
   - 使用 ESLint 和 Prettier 进行代码格式化

2. 提交规范
   - feat: 新功能
   - fix: 修复问题
   - docs: 文档修改
   - style: 代码格式修改
   - refactor: 代码重构
   - test: 测试用例修改
   - chore: 其他修改

3. 分支管理
   - main: 主分支，用于生产环境
   - develop: 开发分支
   - feature/*: 功能分支
   - bugfix/*: 问题修复分支

## 部署说明

1. 后端部署
   - 使用 gunicorn 作为 WSGI 服务器
   - 使用 supervisor 进行进程管理
   - 使用 nginx 作为反向代理

2. 前端部署
   - 构建静态文件：`npm run build`
   - 使用 nginx 托管静态文件

## 许可证

MIT License
