#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 设置错误处理
set -e

# 记录开始时间
START_TIME=$(date +%s)

echo -e "${BLUE}====================================${NC}"
echo -e "${BLUE}     前端服务部署脚本启动中...     ${NC}"
echo -e "${BLUE}====================================${NC}"
echo -e "${YELLOW}开始时间: $(date '+%Y-%m-%d %H:%M:%S')${NC}"

# 创建日志目录
echo -e "${YELLOW}创建日志目录...${NC}"
mkdir -p ../logs/frontend
chmod 777 ../logs/frontend

# 检查后端网络是否存在
echo -e "${YELLOW}检查后端网络是否存在...${NC}"
if ! docker network ls | grep -q stock-backend_stock-network; then
    echo -e "${RED}警告: 后端网络 stock-backend_stock-network 不存在!${NC}"
    echo -e "${YELLOW}尝试创建后端网络...${NC}"
    docker network create stock-backend_stock-network || true
fi

# 创建docker-compose文件
echo -e "${YELLOW}创建docker-compose配置...${NC}"
cat > docker-compose.yml << EOF
version: '3.8'

services:
  frontend:
    container_name: stock-frontend
    build:
      context: .
      dockerfile: Dockerfile
    restart: unless-stopped
    ports:
      - "9009:80"
    volumes:
      - ./dist:/usr/share/nginx/html
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - ../logs/frontend:/var/log/nginx
    environment:
      - TZ=Asia/Shanghai
      - BACKEND_HOST=stock-backend
      - BACKEND_PORT=9099
      - NODE_ENV=production
    networks:
      - frontend_network
      - stock-backend_stock-network
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

networks:
  frontend_network:
    driver: bridge
  stock-backend_stock-network:
    external: true
EOF

# 停止并移除现有容器
echo -e "${YELLOW}停止并移除现有容器...${NC}"
docker-compose down --remove-orphans || {
    echo -e "${RED}停止容器失败，尝试强制移除...${NC}"
    docker rm -f stock-frontend || true
}

# 清理旧镜像
echo -e "${YELLOW}清理旧镜像...${NC}"
docker-compose rm -f || true

# 构建新镜像
echo -e "${YELLOW}构建新镜像...${NC}"
docker-compose build --no-cache || {
    echo -e "${RED}构建镜像失败，请检查Dockerfile和构建上下文${NC}"
    exit 1
}

# 启动容器
echo -e "${YELLOW}启动容器...${NC}"
docker-compose up -d || {
    echo -e "${RED}启动容器失败，请检查docker-compose配置${NC}"
    exit 1
}

# 等待容器启动
echo -e "${YELLOW}等待容器启动...${NC}"
sleep 5

# 检查容器状态
echo -e "${YELLOW}检查容器状态...${NC}"
CONTAINER_STATUS=$(docker inspect --format='{{.State.Status}}' stock-frontend 2>/dev/null || echo "not_found")

if [ "$CONTAINER_STATUS" != "running" ]; then
    echo -e "${RED}容器未正常运行，状态: $CONTAINER_STATUS${NC}"
    echo -e "${YELLOW}查看容器日志:${NC}"
    docker logs stock-frontend
    exit 1
else
    echo -e "${GREEN}容器运行正常!${NC}"
fi

# 记录结束时间并计算耗时
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}     前端服务部署完成!     ${NC}"
echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}前端服务访问地址: http://localhost:9009${NC}"
echo -e "${YELLOW}部署耗时: ${DURATION} 秒${NC}"
echo -e "${YELLOW}完成时间: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo -e "${GREEN}====================================${NC}" 