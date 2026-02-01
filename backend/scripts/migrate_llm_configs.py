"""
LLM 配置表迁移脚本
将旧的单配置表（user_id 为主键）迁移到新的多配置表（id 为主键）

运行方式:
    cd backend
    python -m scripts.migrate_llm_configs

注意:
    - 迁移前请务必备份数据库
    - 该脚本会自动检测是否需要迁移
    - 迁移是一次性操作，已迁移的数据库不会重复迁移
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


async def check_migration_needed(session: AsyncSession) -> bool:
    """检查是否需要迁移"""
    try:
        # 检查表是否存在 id 列
        result = await session.execute(text("PRAGMA table_info(llm_configs)"))
        columns = {row[1]: row for row in result.fetchall()}

        # 如果已存在 id 列，说明已经迁移过
        if 'id' in columns:
            print("✓ 数据库已经是新结构，无需迁移")
            return False

        # 如果没有 id 列但有 user_id 作为主键，说明需要迁移
        if 'user_id' in columns:
            print("→ 检测到旧版表结构，需要迁移")
            return True

        print("? 表结构未知，跳过迁移")
        return False

    except Exception as e:
        print(f"✗ 检查表结构失败: {e}")
        return False


async def migrate_llm_configs(session: AsyncSession) -> bool:
    """执行迁移"""
    try:
        print("开始迁移 llm_configs 表...")

        # 1. 创建临时表
        print("  1/5 创建临时表...")
        await session.execute(text("""
            CREATE TABLE llm_configs_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name VARCHAR(64) NOT NULL DEFAULT '默认配置',
                is_active BOOLEAN NOT NULL DEFAULT 1,
                llm_provider_url TEXT,
                llm_provider_api_key TEXT,
                llm_provider_model TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # 2. 迁移数据
        print("  2/5 迁移现有数据...")
        await session.execute(text("""
            INSERT INTO llm_configs_new (
                user_id, name, is_active,
                llm_provider_url, llm_provider_api_key, llm_provider_model,
                created_at, updated_at
            )
            SELECT
                user_id, '默认配置', 1,
                llm_provider_url, llm_provider_api_key, llm_provider_model,
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            FROM llm_configs
        """))

        # 3. 删除旧表
        print("  3/5 删除旧表...")
        await session.execute(text("DROP TABLE llm_configs"))

        # 4. 重命名新表
        print("  4/5 重命名新表...")
        await session.execute(text("ALTER TABLE llm_configs_new RENAME TO llm_configs"))

        # 5. 创建索引
        print("  5/5 创建索引...")
        await session.execute(text("CREATE INDEX ix_llm_configs_user_id ON llm_configs(user_id)"))
        await session.execute(text("CREATE INDEX ix_llm_configs_id ON llm_configs(id)"))

        await session.commit()
        print("✓ 迁移完成！")
        return True

    except Exception as e:
        await session.rollback()
        print(f"✗ 迁移失败: {e}")
        return False


async def create_table_if_not_exists(session: AsyncSession) -> bool:
    """如果表不存在，创建新表"""
    try:
        # 检查表是否存在
        result = await session.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='llm_configs'"
        ))
        table_exists = result.fetchone() is not None

        if table_exists:
            return True

        print("→ llm_configs 表不存在，创建新表...")
        await session.execute(text("""
            CREATE TABLE llm_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name VARCHAR(64) NOT NULL DEFAULT '默认配置',
                is_active BOOLEAN NOT NULL DEFAULT 0,
                llm_provider_url TEXT,
                llm_provider_api_key TEXT,
                llm_provider_model TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        await session.execute(text("CREATE INDEX ix_llm_configs_user_id ON llm_configs(user_id)"))
        await session.execute(text("CREATE INDEX ix_llm_configs_id ON llm_configs(id)"))
        await session.commit()
        print("✓ 表创建完成！")
        return True

    except Exception as e:
        await session.rollback()
        print(f"✗ 创建表失败: {e}")
        return False


async def main():
    """主函数"""
    print("=" * 50)
    print("LLM 配置表迁移脚本")
    print("=" * 50)

    # 创建数据库引擎
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 确保表存在
        if not await create_table_if_not_exists(session):
            return

        # 检查是否需要迁移
        if await check_migration_needed(session):
            # 执行迁移
            if not await migrate_llm_configs(session):
                print("\n迁移失败，请检查错误信息并重试")
                return

    print("\n" + "=" * 50)
    print("操作完成！")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
