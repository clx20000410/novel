#!/bin/bash
# 数据库迁移执行脚本

set -e

echo "========================================="
echo "数据库迁移执行脚本"
echo "========================================="

# 加载环境变量
if [ -f .env ]; then
    source .env
fi

# 数据库连接信息
DB_HOST="${MYSQL_HOST:-localhost}"
DB_PORT="${MYSQL_PORT:-3306}"
DB_USER="${MYSQL_USER:-arboris}"
DB_PASSWORD="${MYSQL_PASSWORD}"
DB_NAME="${MYSQL_DATABASE:-arboris}"

if [ -z "$DB_PASSWORD" ]; then
    echo "错误：未设置 MYSQL_PASSWORD 环境变量"
    exit 1
fi

echo "数据库连接信息："
echo "  主机: $DB_HOST"
echo "  端口: $DB_PORT"
echo "  用户: $DB_USER"
echo "  数据库: $DB_NAME"
echo ""

# 检查 MySQL 连接
echo "检查 MySQL 连接..."
if ! mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" -e "SELECT 1;" > /dev/null 2>&1; then
    echo "错误：无法连接到 MySQL 数据库"
    exit 1
fi
echo "✓ MySQL 连接成功"
echo ""

# 创建备份
BACKUP_DIR="./backups"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"

echo "创建数据库备份..."
mysqldump -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" > "$BACKUP_FILE"
echo "✓ 备份已保存到: $BACKUP_FILE"
echo ""

# 执行迁移脚本
MIGRATION_DIR="./backend/db/migrations"

echo "执行迁移脚本..."

# 1. Novel-Kit 功能迁移
if [ -f "$MIGRATION_DIR/add_novel_kit_features.sql" ]; then
    echo "  执行: add_novel_kit_features.sql"
    mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < "$MIGRATION_DIR/add_novel_kit_features.sql"
    echo "  ✓ 完成"
else
    echo "  ⚠ 未找到: add_novel_kit_features.sql"
fi

# 2. 深度优化功能迁移
if [ -f "$MIGRATION_DIR/add_deep_optimization_features.sql" ]; then
    echo "  执行: add_deep_optimization_features.sql"
    mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < "$MIGRATION_DIR/add_deep_optimization_features.sql"
    echo "  ✓ 完成"
else
    echo "  ⚠ 未找到: add_deep_optimization_features.sql"
fi

# 3. chapter_outlines 表添加 metadata 字段
echo "  添加 chapter_outlines.metadata 字段..."
mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "
    ALTER TABLE chapter_outlines 
    ADD COLUMN IF NOT EXISTS metadata JSON NULL;
" 2>/dev/null || echo "  ⚠ 字段可能已存在"

echo ""
echo "========================================="
echo "迁移完成"
echo "========================================="
echo ""
echo "请运行验证脚本检查迁移结果："
echo "  bash deploy/scripts/verify_migration.sh"
