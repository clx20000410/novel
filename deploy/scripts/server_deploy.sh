#!/bin/bash
# 服务器端一键部署脚本
# 使用方法：
# 1. SSH 登录服务器: ssh root@45.15.185.52
# 2. 下载并执行: curl -fsSL https://raw.githubusercontent.com/all666666all/AI-novel/main/deploy/scripts/server_deploy.sh | bash

set -e

echo "========================================="
echo "AI-Novel 服务器端一键部署脚本"
echo "========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 1. 检查系统
echo ""
echo -e "${BLUE}1. 检查系统环境...${NC}"
if [ "$(id -u)" != "0" ]; then
   echo -e "${RED}错误：此脚本需要 root 权限${NC}"
   exit 1
fi

echo "系统信息："
uname -a
echo ""

# 2. 安装必需软件
echo -e "${BLUE}2. 安装必需软件...${NC}"

# 安装 Git
if ! command -v git &> /dev/null; then
    echo "安装 Git..."
    apt-get update
    apt-get install -y git
fi
echo -e "${GREEN}✓ Git 已安装${NC}"

# 安装 curl
if ! command -v curl &> /dev/null; then
    echo "安装 curl..."
    apt-get install -y curl
fi
echo -e "${GREEN}✓ curl 已安装${NC}"

# 安装 Docker
if ! command -v docker &> /dev/null; then
    echo "安装 Docker..."
    curl -fsSL https://get.docker.com | bash
    systemctl start docker
    systemctl enable docker
    echo -e "${GREEN}✓ Docker 已安装${NC}"
else
    echo -e "${GREEN}✓ Docker 已存在${NC}"
fi

# 检查 Docker Compose
if ! docker compose version &> /dev/null; then
    echo -e "${YELLOW}⚠ Docker Compose 插件未安装，尝试安装...${NC}"
    apt-get update
    apt-get install -y docker-compose-plugin
fi
echo -e "${GREEN}✓ Docker Compose 已就绪${NC}"

# 3. 克隆或更新项目
echo ""
echo -e "${BLUE}3. 获取项目代码...${NC}"
cd /root

if [ -d "AI-novel" ]; then
    echo "项目目录已存在，更新代码..."
    cd AI-novel
    git fetch origin
    git reset --hard origin/main
    git pull origin main
    echo -e "${GREEN}✓ 代码已更新到最新版本${NC}"
else
    echo "克隆项目..."
    git clone https://github.com/all666666all/AI-novel.git
    cd AI-novel
    echo -e "${GREEN}✓ 项目已克隆${NC}"
fi

# 4. 配置环境变量
echo ""
echo -e "${BLUE}4. 配置环境变量...${NC}"

if [ ! -f ".env" ]; then
    echo "创建 .env 文件..."
    
    # 生成随机密钥
    SECRET_KEY=$(openssl rand -hex 32)
    
    cat > .env << ENVEOF
# 应用配置
SECRET_KEY=${SECRET_KEY}
ENVIRONMENT=production
DEBUG=false
LOGGING_LEVEL=INFO
APP_PORT=80

# 数据库配置（使用 SQLite，无需额外配置）
DB_PROVIDER=sqlite
SQLITE_STORAGE_SOURCE=sqlite-data

# MySQL 配置（如果需要切换到 MySQL，修改 DB_PROVIDER=mysql 并启用 profile）
MYSQL_HOST=db
MYSQL_PORT=3306
MYSQL_USER=arboris
MYSQL_PASSWORD=AI-Novel-MySQL-$(openssl rand -hex 16)
MYSQL_DATABASE=arboris
MYSQL_ROOT_PASSWORD=AI-Novel-Root-$(openssl rand -hex 16)

# 管理员账号
ADMIN_DEFAULT_USERNAME=admin
ADMIN_DEFAULT_PASSWORD=Admin123456!
ADMIN_DEFAULT_EMAIL=admin@ai-novel.com

# OpenAI API（请手动配置）
OPENAI_API_KEY=sk-placeholder-please-replace-with-real-key
OPENAI_API_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL_NAME=gpt-4
WRITER_CHAPTER_VERSION_COUNT=2

# Embedding 配置
EMBEDDING_PROVIDER=openai
EMBEDDING_BASE_URL=https://api.openai.com/v1
EMBEDDING_API_KEY=\${OPENAI_API_KEY}
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_MODEL_VECTOR_SIZE=3072

# 向量数据库配置
VECTOR_DB_URL=file:./storage/rag_vectors.db
VECTOR_DB_AUTH_TOKEN=
VECTOR_TOP_K_CHUNKS=5
VECTOR_TOP_K_SUMMARIES=3
VECTOR_CHUNK_SIZE=480
VECTOR_CHUNK_OVERLAP=120

# 用户注册
ALLOW_USER_REGISTRATION=true
ENABLE_LINUXDO_LOGIN=false

# SMTP 配置（可选）
SMTP_SERVER=smtp.example.com
SMTP_PORT=465
SMTP_USERNAME=no-reply@example.com
SMTP_PASSWORD=
EMAIL_FROM=AI-Novel
ENVEOF

    echo -e "${GREEN}✓ .env 文件已创建${NC}"
    echo -e "${YELLOW}⚠ 请编辑 .env 文件，配置你的 OPENAI_API_KEY${NC}"
    echo -e "${YELLOW}   执行: nano /root/AI-novel/.env${NC}"
else
    echo -e "${GREEN}✓ .env 文件已存在${NC}"
fi

# 5. 部署 Docker 容器
echo ""
echo -e "${BLUE}5. 部署 Docker 容器...${NC}"

cd deploy

# 停止旧容器
echo "停止旧容器..."
docker compose down 2>/dev/null || true

# 构建镜像
echo "构建 Docker 镜像（这可能需要几分钟）..."
docker compose build --no-cache

# 启动容器
echo "启动容器..."
docker compose up -d

echo -e "${GREEN}✓ 容器已启动${NC}"

# 6. 等待服务启动
echo ""
echo -e "${BLUE}6. 等待服务启动...${NC}"
sleep 20

# 7. 健康检查
echo ""
echo -e "${BLUE}7. 健康检查...${NC}"

MAX_RETRIES=30
RETRY_COUNT=0
HEALTH_OK=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f http://127.0.0.1:80/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 服务健康检查通过${NC}"
        HEALTH_OK=true
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo "等待服务启动... ($RETRY_COUNT/$MAX_RETRIES)"
        sleep 2
    fi
done

if [ "$HEALTH_OK" = false ]; then
    echo -e "${RED}✗ 服务健康检查失败${NC}"
    echo ""
    echo "查看日志："
    docker compose logs --tail=50 app
    echo ""
    echo "可能的原因："
    echo "1. 端口 80 被占用"
    echo "2. 数据库配置错误"
    echo "3. 依赖安装失败"
    echo ""
    echo "请检查日志并重新运行脚本"
    exit 1
fi

# 8. 显示部署信息
echo ""
echo "========================================="
echo -e "${GREEN}部署成功！${NC}"
echo "========================================="
echo ""
echo "访问信息："
echo "  前端地址: http://$(curl -s ifconfig.me)"
echo "  本地访问: http://localhost"
echo "  API 文档: http://localhost/api/docs"
echo ""
echo "管理员账号："
echo "  用户名: admin"
echo "  密码: Admin123456!"
echo ""
echo -e "${YELLOW}重要提示：${NC}"
echo "1. 请立即修改管理员密码"
echo "2. 配置 OPENAI_API_KEY（如果还没有）："
echo "   nano /root/AI-novel/.env"
echo "   然后重启服务: cd /root/AI-novel/deploy && docker compose restart"
echo ""
echo "常用命令："
echo "  查看日志: cd /root/AI-novel/deploy && docker compose logs -f app"
echo "  重启服务: cd /root/AI-novel/deploy && docker compose restart"
echo "  停止服务: cd /root/AI-novel/deploy && docker compose down"
echo ""
echo "如需帮助，请查看: /root/AI-novel/DEPLOYMENT_GUIDE_FULL.md"
echo ""
