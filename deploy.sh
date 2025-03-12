#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}股票交易系统部署脚本${NC}"
echo "============================"

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker未安装${NC}"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}错误: Docker Compose未安装${NC}"
    exit 1
fi

# 停止并删除现有容器
echo -e "${YELLOW}停止并删除现有容器...${NC}"
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

echo -e "${GREEN}部署完成!${NC}"
echo "前端访问地址: http://localhost:9009"
echo "后端API地址: http://localhost:9099"
echo "============================" 