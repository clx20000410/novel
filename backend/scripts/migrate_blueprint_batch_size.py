#!/usr/bin/env python3
"""
迁移脚本：给 llm_configs 表添加 blueprint_batch_size 字段

用法：
    cd backend
    python -m scripts.migrate_blueprint_batch_size
"""
import sqlite3
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings


def migrate():
    """执行迁移"""
    db_url = settings.sqlalchemy_database_uri
    if not db_url:
        print("错误：未配置数据库 URL")
        return False

    # 从 URL 中提取数据库路径
    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
    elif db_url.startswith("sqlite+aiosqlite:///"):
        db_path = db_url.replace("sqlite+aiosqlite:///", "")
    else:
        print(f"错误：不支持的数据库类型: {db_url}")
        return False

    print(f"数据库路径: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(llm_configs)")
        columns = [col[1] for col in cursor.fetchall()]

        if "blueprint_batch_size" in columns:
            print("字段 blueprint_batch_size 已存在，跳过迁移")
            conn.close()
            return True

        # 添加新字段
        print("添加字段 blueprint_batch_size...")
        cursor.execute("""
            ALTER TABLE llm_configs
            ADD COLUMN blueprint_batch_size INTEGER NOT NULL DEFAULT 5
        """)

        conn.commit()
        print("迁移完成！")

        # 验证
        cursor.execute("PRAGMA table_info(llm_configs)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"当前字段: {columns}")

        conn.close()
        return True

    except Exception as e:
        print(f"迁移失败: {e}")
        return False


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
