#!/bin/bash
# 群辉NAS Docker部署脚本

echo "开始部署股票管理系统..."

# 确保日志目录存在
mkdir -p logs/frontend

# 检查Stock网络是否存在，如果不存在则创建
if ! docker network ls | grep -q "Stock"; then
  echo "创建Stock网络..."
  docker network create Stock
  if [ $? -ne 0 ]; then
    echo "创建Stock网络失败，请检查Docker权限"
    exit 1
  fi
fi

# 检查mysql-container是否存在并运行
if ! docker ps | grep -q "mysql-container"; then
  echo "警告: mysql-container未运行，请确保数据库容器已启动"
  echo "系统将继续部署，但可能无法连接到数据库"
fi

# 构建并启动后端服务
echo "构建并启动后端服务..."
cd backend
docker-compose down
docker-compose build
docker-compose up -d
if [ $? -ne 0 ]; then
  echo "后端服务启动失败，请检查日志"
  exit 1
fi
cd ..

# 构建并启动前端服务
echo "构建并启动前端服务..."
cd frontend
docker-compose down
docker-compose build
docker-compose up -d
if [ $? -ne 0 ]; then
  echo "前端服务启动失败，请检查日志"
  exit 1
fi
cd ..

echo "部署完成！"
echo "前端服务地址: http://$(hostname -I | awk '{print $1}'):9009"
echo "后端服务地址: http://$(hostname -I | awk '{print $1}'):9099" 