#!/bin/bash
# 数据库迁移验证脚本

set -e

echo "========================================="
echo "数据库迁移验证脚本"
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
echo "1. 检查 MySQL 连接..."
if mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" -e "SELECT 1;" > /dev/null 2>&1; then
    echo "   ✓ MySQL 连接成功"
else
    echo "   ✗ MySQL 连接失败"
    exit 1
fi

# 检查数据库是否存在
echo ""
echo "2. 检查数据库 $DB_NAME 是否存在..."
if mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" -e "USE $DB_NAME;" > /dev/null 2>&1; then
    echo "   ✓ 数据库存在"
else
    echo "   ✗ 数据库不存在"
    exit 1
fi

# 检查 Novel-Kit 功能表
echo ""
echo "3. 检查 Novel-Kit 功能表..."
NOVEL_KIT_TABLES=(
    "constitutions"
    "writer_personas"
    "factions"
    "faction_members"
    "faction_relationships"
    "faction_relationship_history"
)

for table in "${NOVEL_KIT_TABLES[@]}"; do
    if mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "DESCRIBE $table;" > /dev/null 2>&1; then
        echo "   ✓ 表 $table 存在"
    else
        echo "   ✗ 表 $table 不存在"
        echo "     请执行迁移脚本: backend/db/migrations/add_novel_kit_features.sql"
    fi
done

# 检查深度优化功能表
echo ""
echo "4. 检查深度优化功能表..."
OPTIMIZATION_TABLES=(
    "character_states"
    "timeline_events"
    "causal_chains"
    "story_time_trackers"
    "periodic_reviews"
    "reader_feedbacks"
    "critique_records"
    "revision_histories"
    "emotion_curve_configs"
)

for table in "${OPTIMIZATION_TABLES[@]}"; do
    if mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "DESCRIBE $table;" > /dev/null 2>&1; then
        echo "   ✓ 表 $table 存在"
    else
        echo "   ✗ 表 $table 不存在"
        echo "     请执行迁移脚本: backend/db/migrations/add_deep_optimization_features.sql"
    fi
done

# 检查 chapter_outlines 表的 metadata 字段
echo ""
echo "5. 检查 chapter_outlines 表的 metadata 字段..."
if mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "DESCRIBE chapter_outlines metadata;" > /dev/null 2>&1; then
    echo "   ✓ chapter_outlines.metadata 字段存在"
else
    echo "   ✗ chapter_outlines.metadata 字段不存在"
    echo "     请执行: ALTER TABLE chapter_outlines ADD COLUMN metadata JSON NULL;"
fi

# 检查 foreshadowings 表的扩展字段
echo ""
echo "6. 检查 foreshadowings 表的扩展字段..."
FORESHADOWING_FIELDS=(
    "status"
    "planted_chapter"
    "revealed_chapter"
    "planned_reveal_chapter"
)

for field in "${FORESHADOWING_FIELDS[@]}"; do
    if mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "DESCRIBE foreshadowings $field;" > /dev/null 2>&1; then
        echo "   ✓ foreshadowings.$field 字段存在"
    else
        echo "   ✗ foreshadowings.$field 字段不存在"
    fi
done

echo ""
echo "========================================="
echo "验证完成"
echo "========================================="
