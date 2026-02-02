#!/bin/bash
# 数据库迁移执行脚本
# 更新日期: 2026-02-02
# 功能: 执行全部迁移脚本，确保数据库结构与 ORM 模型同步

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

# 创建数据库（如不存在）
echo "确保数据库存在..."
mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" -e "CREATE DATABASE IF NOT EXISTS \`$DB_NAME\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null
echo "✓ 数据库 $DB_NAME 已就绪"
echo ""

# 创建备份
BACKUP_DIR="./backups"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"

echo "创建数据库备份..."
mysqldump -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" > "$BACKUP_FILE" 2>/dev/null || echo "  ⚠ 数据库为空，跳过备份"
if [ -s "$BACKUP_FILE" ]; then
    echo "✓ 备份已保存到: $BACKUP_FILE"
else
    rm -f "$BACKUP_FILE"
    echo "  （数据库为空，无需备份）"
fi
echo ""

# 执行迁移脚本
MIGRATION_DIR="./backend/db/migrations"
SCHEMA_FILE="./backend/db/schema.sql"

echo "========================================="
echo "方式选择"
echo "========================================="
echo "  1) 全量建表 - 适用于全新安装（使用 schema.sql）"
echo "  2) 增量迁移 - 适用于已有数据库升级"
echo ""
read -p "请选择 [1/2] (默认: 2): " CHOICE
CHOICE=${CHOICE:-2}

if [ "$CHOICE" = "1" ]; then
    echo ""
    echo "执行全量建表脚本..."
    if [ -f "$SCHEMA_FILE" ]; then
        mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < "$SCHEMA_FILE"
        echo "✓ 全量建表完成（37 个表）"
    else
        echo "✗ 未找到 schema.sql 文件"
        exit 1
    fi
else
    echo ""
    echo "执行增量迁移脚本..."

    # 1. Novel-Kit 功能迁移（宪法、人格、势力、伏笔增强）
    if [ -f "$MIGRATION_DIR/add_novel_kit_features.sql" ]; then
        echo "  执行: add_novel_kit_features.sql"
        mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < "$MIGRATION_DIR/add_novel_kit_features.sql"
        echo "  ✓ Novel-Kit 功能迁移完成"
    else
        echo "  ⚠ 未找到: add_novel_kit_features.sql"
    fi

    # 2. 深度优化功能迁移（记忆层、项目记忆、章节蓝图、伏笔增强表）
    if [ -f "$MIGRATION_DIR/add_deep_optimization_features.sql" ]; then
        echo "  执行: add_deep_optimization_features.sql"
        mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < "$MIGRATION_DIR/add_deep_optimization_features.sql"
        echo "  ✓ 深度优化功能迁移完成"
    else
        echo "  ⚠ 未找到: add_deep_optimization_features.sql"
    fi

    # 3. chapter_outlines 表添加 metadata 字段
    echo "  添加 chapter_outlines.metadata 字段..."
    mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "
        ALTER TABLE chapter_outlines
        ADD COLUMN IF NOT EXISTS metadata JSON NULL;
    " 2>/dev/null || echo "  ⚠ 字段可能已存在"

    # 4. llm_configs 表迁移到多配置模式
    echo "  检查 llm_configs 表结构..."
    HAS_ID=$(mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -N -e "
        SELECT COUNT(*) FROM information_schema.columns
        WHERE table_schema='$DB_NAME' AND table_name='llm_configs' AND column_name='id';
    " 2>/dev/null)

    if [ "$HAS_ID" = "0" ] 2>/dev/null; then
        echo "  检测到旧版 llm_configs 表，执行迁移..."
        mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "
            ALTER TABLE llm_configs
                ADD COLUMN id INT AUTO_INCREMENT FIRST,
                ADD COLUMN name VARCHAR(64) NOT NULL DEFAULT '默认配置' AFTER user_id,
                ADD COLUMN is_active TINYINT(1) DEFAULT 0 AFTER name,
                ADD COLUMN api_format VARCHAR(32) NOT NULL DEFAULT 'openai_chat' AFTER is_active,
                ADD COLUMN blueprint_batch_size INT NOT NULL DEFAULT 5 AFTER llm_provider_model,
                ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                DROP PRIMARY KEY,
                ADD PRIMARY KEY (id),
                ADD INDEX idx_llm_configs_user_id (user_id);
        " 2>/dev/null && echo "  ✓ llm_configs 表迁移完成" || echo "  ⚠ llm_configs 迁移可能部分失败，请检查"
    else
        echo "  ✓ llm_configs 已是新版结构"
    fi

    # 5. 确保 email_verification_codes 表存在
    echo "  检查 email_verification_codes 表..."
    mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "
        CREATE TABLE IF NOT EXISTS email_verification_codes (
            email VARCHAR(255) PRIMARY KEY,
            code_hash VARCHAR(64) NOT NULL,
            expires_at DATETIME NOT NULL,
            last_sent_at DATETIME NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        );
    " 2>/dev/null
    echo "  ✓ email_verification_codes 表已就绪"
fi

echo ""
echo "========================================="
echo "迁移完成"
echo "========================================="
echo ""
echo "请运行验证脚本检查迁移结果："
echo "  bash deploy/scripts/verify_migration.sh"
