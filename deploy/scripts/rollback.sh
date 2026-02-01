#!/bin/bash
# 回滚脚本

set -e

echo "========================================="
echo "AI-Novel 回滚脚本"
echo "========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查是否在项目根目录
if [ ! -f "deploy/docker-compose.yml" ]; then
    echo -e "${RED}错误：请在项目根目录执行此脚本${NC}"
    exit 1
fi

# 检查备份目录
BACKUP_DIR="./backups"
if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${RED}错误：未找到备份目录${NC}"
    exit 1
fi

# 列出可用的备份
echo ""
echo "可用的数据库备份："
echo ""
ls -lh $BACKUP_DIR/*.sql 2>/dev/null || {
    echo -e "${RED}未找到任何备份文件${NC}"
    exit 1
}

echo ""
echo -e "${YELLOW}请输入要恢复的备份文件名（例如：backup_20260113_120000.sql）：${NC}"
read -r backup_file

BACKUP_PATH="$BACKUP_DIR/$backup_file"

if [ ! -f "$BACKUP_PATH" ]; then
    echo -e "${RED}错误：备份文件不存在: $BACKUP_PATH${NC}"
    exit 1
fi

# 确认回滚
echo ""
echo -e "${RED}警告：回滚将覆盖当前数据库！${NC}"
echo "备份文件: $BACKUP_PATH"
echo "文件大小: $(du -h $BACKUP_PATH | cut -f1)"
echo "创建时间: $(stat -c %y $BACKUP_PATH 2>/dev/null || stat -f %Sm $BACKUP_PATH)"
echo ""
echo -e "${YELLOW}确认要执行回滚吗？(yes/no)${NC}"
read -r response

if [ "$response" != "yes" ]; then
    echo -e "${RED}回滚已取消${NC}"
    exit 0
fi

# 加载环境变量
if [ ! -f ".env" ]; then
    echo -e "${RED}错误：未找到 .env 文件${NC}"
    exit 1
fi
source .env

# 数据库连接信息
DB_HOST="${MYSQL_HOST:-localhost}"
DB_PORT="${MYSQL_PORT:-3306}"
DB_USER="${MYSQL_USER:-arboris}"
DB_PASSWORD="${MYSQL_PASSWORD}"
DB_NAME="${MYSQL_DATABASE:-arboris}"

if [ -z "$DB_PASSWORD" ]; then
    echo -e "${RED}错误：未设置 MYSQL_PASSWORD 环境变量${NC}"
    exit 1
fi

# 创建当前数据库的备份（以防回滚失败）
echo ""
echo "创建当前数据库的安全备份..."
SAFETY_BACKUP="$BACKUP_DIR/safety_backup_$(date +%Y%m%d_%H%M%S).sql"
mysqldump -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" > "$SAFETY_BACKUP"
echo -e "${GREEN}✓ 安全备份已保存到: $SAFETY_BACKUP${NC}"

# 停止服务
echo ""
echo "停止服务..."
cd deploy
docker-compose down || true
cd ..
echo -e "${GREEN}✓ 服务已停止${NC}"

# 恢复数据库
echo ""
echo "恢复数据库..."
mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < "$BACKUP_PATH"
echo -e "${GREEN}✓ 数据库已恢复${NC}"

# 重启服务
echo ""
echo "重启服务..."
cd deploy
DB_PROVIDER="${DB_PROVIDER:-sqlite}"
if [ "$DB_PROVIDER" = "mysql" ]; then
    docker-compose --profile mysql up -d
else
    docker-compose up -d
fi
cd ..

# 等待服务启动
echo ""
echo "等待服务启动..."
sleep 10

# 检查健康状态
echo ""
echo "检查服务健康状态..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f http://127.0.0.1:${APP_PORT:-80}/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 服务健康检查通过${NC}"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo "等待服务启动... ($RETRY_COUNT/$MAX_RETRIES)"
        sleep 2
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}✗ 服务健康检查失败${NC}"
    echo "尝试恢复到安全备份..."
    mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < "$SAFETY_BACKUP"
    echo "请检查日志："
    cd deploy && docker-compose logs --tail=50 app
    exit 1
fi

echo ""
echo "========================================="
echo -e "${GREEN}回滚成功！${NC}"
echo "========================================="
echo ""
echo "已恢复到备份: $backup_file"
echo "安全备份保存在: $SAFETY_BACKUP"
echo ""
