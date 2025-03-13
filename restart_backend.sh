#!/bin/bash
# 重启后端服务

echo "正在重启后端服务..."

# 尝试使用docker compose命令
if command -v docker compose &> /dev/null; then
    echo "使用docker compose命令重启后端服务"
    docker compose restart backend
# 尝试使用docker-compose命令
elif command -v docker-compose &> /dev/null; then
    echo "使用docker-compose命令重启后端服务"
    docker-compose restart backend
# 尝试使用ssh连接到服务器重启服务
else
    echo "本地docker命令不可用，尝试使用ssh连接到服务器重启服务"
    # 这里需要根据实际情况修改服务器地址和用户名
    ssh user@server "cd /path/to/project && docker compose restart backend"
fi

echo "后端服务重启完成" 