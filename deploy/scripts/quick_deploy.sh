#!/bin/bash
# 一键部署脚本（适用于生产服务器）

set -e

echo "========================================="
echo "AI-Novel 一键部署脚本"
echo "========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 服务器信息
SERVER_IP="45.15.185.52"
SERVER_USER="root"
PROJECT_DIR="/root/AI-novel"

echo ""
echo "目标服务器："
echo "  IP: $SERVER_IP"
echo "  用户: $SERVER_USER"
echo "  项目目录: $PROJECT_DIR"
echo ""

# 确认部署
echo -e "${YELLOW}确认要部署到生产服务器吗？(yes/no)${NC}"
read -r response
if [ "$response" != "yes" ]; then
    echo -e "${RED}部署已取消${NC}"
    exit 0
fi

# SSH 连接测试
echo ""
echo "测试 SSH 连接..."
if ssh -o ConnectTimeout=5 $SERVER_USER@$SERVER_IP "echo 'SSH 连接成功'" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ SSH 连接成功${NC}"
else
    echo -e "${RED}✗ SSH 连接失败${NC}"
    echo "请检查："
    echo "  1. 服务器 IP 是否正确"
    echo "  2. SSH 密钥是否已配置"
    echo "  3. 服务器是否在线"
    exit 1
fi

# 在服务器上执行部署
echo ""
echo -e "${BLUE}开始远程部署...${NC}"
echo ""

ssh $SERVER_USER@$SERVER_IP bash << 'ENDSSH'
set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="/root/AI-novel"

echo "========================================="
echo "远程服务器部署流程"
echo "========================================="

# 1. 检查项目目录
echo ""
echo "1. 检查项目目录..."
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${YELLOW}项目目录不存在，正在克隆仓库...${NC}"
    cd /root
    git clone https://github.com/all666666all/AI-novel.git
    cd AI-novel
else
    echo -e "${GREEN}✓ 项目目录存在${NC}"
    cd $PROJECT_DIR
fi

# 2. 拉取最新代码
echo ""
echo "2. 拉取最新代码..."
git fetch origin
git reset --hard origin/main
echo -e "${GREEN}✓ 代码已更新到最新版本${NC}"

# 3. 检查 .env 文件
echo ""
echo "3. 检查环境配置..."
if [ ! -f ".env" ]; then
    echo -e "${RED}✗ 未找到 .env 文件${NC}"
    echo "请先创建 .env 文件并配置环境变量"
    exit 1
fi
echo -e "${GREEN}✓ .env 文件存在${NC}"

# 4. 检查 Docker
echo ""
echo "4. 检查 Docker 环境..."
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker 未安装，正在安装...${NC}"
    curl -fsSL https://get.docker.com | bash
    systemctl start docker
    systemctl enable docker
fi
echo -e "${GREEN}✓ Docker 已就绪${NC}"

# 5. 执行数据库迁移
echo ""
echo "5. 执行数据库迁移..."
if [ -f "deploy/scripts/run_migrations.sh" ]; then
    bash deploy/scripts/run_migrations.sh || echo -e "${YELLOW}⚠ 迁移脚本执行失败或已执行过${NC}"
else
    echo -e "${YELLOW}⚠ 未找到迁移脚本${NC}"
fi

# 6. 部署 Docker 容器
echo ""
echo "6. 部署 Docker 容器..."
bash deploy/scripts/deploy_docker.sh

echo ""
echo "========================================="
echo -e "${GREEN}远程部署完成！${NC}"
echo "========================================="

ENDSSH

# 部署完成
echo ""
echo "========================================="
echo -e "${GREEN}一键部署完成！${NC}"
echo "========================================="
echo ""
echo "访问地址："
echo "  http://$SERVER_IP"
echo ""
echo "查看远程日志："
echo "  ssh $SERVER_USER@$SERVER_IP 'cd $PROJECT_DIR && docker-compose -f deploy/docker-compose.yml logs -f'"
echo ""
