#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}====================================${NC}"
echo -e "${BLUE}     后端服务部署脚本启动中...     ${NC}"
echo -e "${BLUE}====================================${NC}"

# 确保后端网络存在
echo -e "${YELLOW}检查后端网络是否存在...${NC}"
if ! docker network ls | grep -q stock_backend_network; then
    echo -e "${YELLOW}创建后端网络 stock_backend_network...${NC}"
    docker network create stock_backend_network
fi

# 创建docker-compose文件
echo -e "${YELLOW}创建docker-compose配置...${NC}"
cat > docker-compose.yml << EOF
version: '3.8'

services:
  backend:
    container_name: stock-backend
    build:
      context: .
      dockerfile: Dockerfile
    restart: unless-stopped
    ports:
      - "9099:9099"
    volumes:
      - .:/app
      - ../logs:/app/logs
    environment:
      - FLASK_ENV=production
      - PYTHONUNBUFFERED=1
      - TZ=Asia/Shanghai
      - DB_HOST=stock-db
      - DB_PORT=3306
      - DB_USER=root
      - DB_PASSWORD=rootpassword
      - DB_NAME=stock
      - DB_CHARSET=utf8mb4
      - DB_CONNECT_RETRY=5
      - DB_CONNECT_RETRY_DELAY=3
    networks:
      - stock_backend_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9099/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

networks:
  stock_backend_network:
    external: true
EOF

# 停止并移除现有容器
echo -e "${YELLOW}停止并移除现有容器...${NC}"
docker-compose down

# 构建新镜像
echo -e "${YELLOW}构建新镜像...${NC}"
docker-compose build

# 启动容器
echo -e "${YELLOW}启动容器...${NC}"
docker-compose up -d

# 检查容器状态
echo -e "${YELLOW}检查容器状态...${NC}"
docker-compose ps

echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}     后端服务部署完成!     ${NC}"
echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}后端API地址: http://localhost:9099${NC}"
echo -e "${GREEN}====================================${NC}" 