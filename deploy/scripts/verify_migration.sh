#!/bin/bash
# 数据库迁移验证脚本
# 更新日期: 2026-02-02
# 验证全部 37 个表的存在性

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

# ============================================
# 第一部分：基础用户与配置表 (9个)
# ============================================
echo ""
echo "3. 检查基础用户与配置表..."
BASIC_TABLES=(
    "users"
    "llm_configs"
    "system_configs"
    "admin_settings"
    "usage_metrics"
    "user_daily_requests"
    "update_logs"
    "prompts"
    "email_verification_codes"
)

for table in "${BASIC_TABLES[@]}"; do
    if mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "DESCRIBE $table;" > /dev/null 2>&1; then
        echo "   ✓ 表 $table 存在"
    else
        echo "   ✗ 表 $table 不存在"
    fi
done

# ============================================
# 第二部分：小说项目核心表 (10个)
# ============================================
echo ""
echo "4. 检查小说项目核心表..."
NOVEL_CORE_TABLES=(
    "novel_projects"
    "novel_conversations"
    "novel_blueprints"
    "blueprint_characters"
    "blueprint_relationships"
    "chapter_outlines"
    "chapters"
    "chapter_versions"
    "chapter_evaluations"
)

for table in "${NOVEL_CORE_TABLES[@]}"; do
    if mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "DESCRIBE $table;" > /dev/null 2>&1; then
        echo "   ✓ 表 $table 存在"
    else
        echo "   ✗ 表 $table 不存在"
    fi
done

# ============================================
# 第三部分：章节蓝图与模板系统 (2个)
# ============================================
echo ""
echo "5. 检查章节蓝图与模板系统表..."
BLUEPRINT_TABLES=(
    "chapter_blueprints"
    "blueprint_templates"
)

for table in "${BLUEPRINT_TABLES[@]}"; do
    if mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "DESCRIBE $table;" > /dev/null 2>&1; then
        echo "   ✓ 表 $table 存在"
    else
        echo "   ✗ 表 $table 不存在"
    fi
done

# ============================================
# 第四部分：小说宪法与写作人格系统 (2个)
# ============================================
echo ""
echo "6. 检查小说宪法与写作人格系统表..."
CONSTITUTION_TABLES=(
    "novel_constitutions"
    "writer_personas"
)

for table in "${CONSTITUTION_TABLES[@]}"; do
    if mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "DESCRIBE $table;" > /dev/null 2>&1; then
        echo "   ✓ 表 $table 存在"
    else
        echo "   ✗ 表 $table 不存在"
    fi
done

# ============================================
# 第五部分：势力系统 (4个)
# ============================================
echo ""
echo "7. 检查势力系统表..."
FACTION_TABLES=(
    "factions"
    "faction_relationships"
    "faction_members"
    "faction_relationship_history"
)

for table in "${FACTION_TABLES[@]}"; do
    if mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "DESCRIBE $table;" > /dev/null 2>&1; then
        echo "   ✓ 表 $table 存在"
    else
        echo "   ✗ 表 $table 不存在"
    fi
done

# ============================================
# 第六部分：伏笔系统 (5个)
# ============================================
echo ""
echo "8. 检查伏笔系统表..."
FORESHADOWING_TABLES=(
    "foreshadowings"
    "foreshadowing_resolutions"
    "foreshadowing_reminders"
    "foreshadowing_status_history"
    "foreshadowing_analysis"
)

for table in "${FORESHADOWING_TABLES[@]}"; do
    if mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "DESCRIBE $table;" > /dev/null 2>&1; then
        echo "   ✓ 表 $table 存在"
    else
        echo "   ✗ 表 $table 不存在"
    fi
done

# ============================================
# 第七部分：记忆层与上下文系统 (6个)
# ============================================
echo ""
echo "9. 检查记忆层与上下文系统表..."
MEMORY_TABLES=(
    "character_states"
    "timeline_events"
    "causal_chains"
    "story_time_trackers"
    "project_memories"
    "chapter_snapshots"
)

for table in "${MEMORY_TABLES[@]}"; do
    if mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "DESCRIBE $table;" > /dev/null 2>&1; then
        echo "   ✓ 表 $table 存在"
    else
        echo "   ✗ 表 $table 不存在"
    fi
done

# ============================================
# 关键字段检查
# ============================================
echo ""
echo "10. 检查关键字段..."

# 检查 llm_configs 表的新字段
echo "    检查 llm_configs 表新字段..."
LLM_CONFIG_FIELDS=("id" "name" "is_active" "api_format" "blueprint_batch_size")
for field in "${LLM_CONFIG_FIELDS[@]}"; do
    if mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "DESCRIBE llm_configs $field;" > /dev/null 2>&1; then
        echo "   ✓ llm_configs.$field 字段存在"
    else
        echo "   ✗ llm_configs.$field 字段不存在"
    fi
done

# 检查 chapter_outlines 表的 metadata 字段
if mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "DESCRIBE chapter_outlines metadata;" > /dev/null 2>&1; then
    echo "   ✓ chapter_outlines.metadata 字段存在"
else
    echo "   ✗ chapter_outlines.metadata 字段不存在"
fi

# 检查 foreshadowings 表的扩展字段
echo "    检查 foreshadowings 表扩展字段..."
FORESHADOWING_FIELDS=(
    "status"
    "chapter_number"
    "resolved_chapter_number"
    "target_reveal_chapter"
    "name"
    "importance"
    "urgency"
)
for field in "${FORESHADOWING_FIELDS[@]}"; do
    if mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "DESCRIBE foreshadowings $field;" > /dev/null 2>&1; then
        echo "   ✓ foreshadowings.$field 字段存在"
    else
        echo "   ✗ foreshadowings.$field 字段不存在"
    fi
done

# ============================================
# 统计汇总
# ============================================
echo ""
echo "========================================="
echo "表数量统计"
echo "========================================="

TOTAL_TABLES=$(mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -N -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$DB_NAME';")
echo "当前数据库表数量: $TOTAL_TABLES"
echo "预期表数量: 37"

if [ "$TOTAL_TABLES" -ge 37 ]; then
    echo "✓ 表数量检查通过"
else
    echo "⚠ 表数量不足，可能有表未创建"
fi

echo ""
echo "========================================="
echo "验证完成"
echo "========================================="
