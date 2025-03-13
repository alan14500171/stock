#!/bin/bash
# 重启后端服务

echo "正在重启后端服务..."

# 进入后端目录
cd backend

# 重启后端服务
docker-compose restart stock-backend

# 检查服务状态
if [ $? -eq 0 ]; then
  echo "后端服务重启成功！"
  docker-compose ps
else
  echo "后端服务重启失败，请检查日志"
  docker-compose logs
fi 