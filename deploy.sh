#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}====================================${NC}"
echo -e "${BLUE}     股票交易系统部署脚本启动中     ${NC}"
echo -e "${BLUE}====================================${NC}"

# 确保后端网络存在
echo -e "${YELLOW}检查后端网络是否存在...${NC}"
if ! docker network ls | grep -q stock_backend_network; then
    echo -e "${YELLOW}创建后端网络 stock_backend_network...${NC}"
    docker network create stock_backend_network
fi

# 部署数据库
echo -e "${YELLOW}部署数据库服务...${NC}"
cat > db-compose.yml << EOF
version: '3.8'

services:
  db:
    image: mysql:8.0
    container_name: stock-db
    restart: unless-stopped
    environment:
      - MYSQL_ROOT_PASSWORD=rootpassword
      - MYSQL_DATABASE=stock
      - MYSQL_USER=stockuser
      - MYSQL_PASSWORD=rootpassword
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./backend/mysql.cnf:/etc/mysql/conf.d/mysql.cnf
    networks:
      - stock_backend_network
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-prootpassword"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

networks:
  stock_backend_network:
    external: true

volumes:
  mysql_data:
    driver: local
EOF

# 停止并移除现有数据库容器
echo -e "${YELLOW}停止并移除现有数据库容器...${NC}"
docker-compose -f db-compose.yml down

# 启动数据库容器
echo -e "${YELLOW}启动数据库容器...${NC}"
docker-compose -f db-compose.yml up -d

# 等待数据库启动
echo -e "${YELLOW}等待数据库启动...${NC}"
sleep 10

# 部署后端
echo -e "${YELLOW}部署后端服务...${NC}"
cd backend
bash deploy.sh
cd ..

# 部署前端
echo -e "${YELLOW}部署前端服务...${NC}"
cd frontend
bash deploy.sh
cd ..

# 检查所有容器状态
echo -e "${YELLOW}检查所有容器状态...${NC}"
docker ps --filter "network=stock_backend_network"

echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}     股票交易系统部署完成!     ${NC}"
echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}前端服务访问地址: http://localhost:9009${NC}"
echo -e "${GREEN}后端API地址: http://localhost:9099${NC}"
echo -e "${GREEN}====================================${NC}" 