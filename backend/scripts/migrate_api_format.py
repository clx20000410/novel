"""
LLM 配置表 api_format 字段迁移脚本
为现有的 llm_configs 表添加 api_format 列

运行方式:
    cd backend
    python -m scripts.migrate_api_format

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

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


def get_db_url() -> str:
    """获取数据库连接 URL"""
    return settings.sqlalchemy_database_uri


def is_sqlite() -> bool:
    """判断是否为 SQLite 数据库"""
    return "sqlite" in get_db_url().lower()


def is_mysql() -> bool:
    """判断是否为 MySQL 数据库"""
    db_url = get_db_url().lower()
    return "mysql" in db_url or "mariadb" in db_url


def is_postgres() -> bool:
    """判断是否为 PostgreSQL 数据库"""
    db_url = get_db_url().lower()
    return "postgresql" in db_url or "postgres" in db_url


async def check_migration_needed(session: AsyncSession) -> bool:
    """检查是否需要迁移"""
    try:
        if is_sqlite():
            # SQLite 检查方式
            result = await session.execute(text("PRAGMA table_info(llm_configs)"))
            columns = {row[1]: row for row in result.fetchall()}
        else:
            # MySQL/PostgreSQL 检查方式
            result = await session.execute(text("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'llm_configs'
            """))
            columns = {row[0]: row for row in result.fetchall()}

        # 如果已存在 api_format 列，说明已经迁移过
        if 'api_format' in columns:
            print("✓ 数据库已包含 api_format 列，无需迁移")
            return False

        print("→ 检测到缺少 api_format 列，需要迁移")
        return True

    except Exception as e:
        print(f"✗ 检查表结构失败: {e}")
        return False


async def migrate_api_format_sqlite(session: AsyncSession) -> bool:
    """SQLite 迁移 - 添加 api_format 列"""
    try:
        print("开始迁移 (SQLite)...")

        # SQLite 支持 ALTER TABLE ADD COLUMN
        print("  添加 api_format 列...")
        await session.execute(text("""
            ALTER TABLE llm_configs
            ADD COLUMN api_format VARCHAR(32) NOT NULL DEFAULT 'openai_chat'
        """))

        await session.commit()
        print("✓ 迁移完成！")
        return True

    except Exception as e:
        await session.rollback()
        print(f"✗ 迁移失败: {e}")
        return False


async def migrate_api_format_mysql(session: AsyncSession) -> bool:
    """MySQL 迁移 - 添加 api_format 列"""
    try:
        print("开始迁移 (MySQL)...")

        print("  添加 api_format 列...")
        await session.execute(text("""
            ALTER TABLE llm_configs
            ADD COLUMN api_format VARCHAR(32) NOT NULL DEFAULT 'openai_chat'
            AFTER is_active
        """))

        await session.commit()
        print("✓ 迁移完成！")
        return True

    except Exception as e:
        await session.rollback()
        print(f"✗ 迁移失败: {e}")
        return False


async def migrate_api_format_postgres(session: AsyncSession) -> bool:
    """PostgreSQL 迁移 - 添加 api_format 列"""
    try:
        print("开始迁移 (PostgreSQL)...")

        print("  添加 api_format 列...")
        await session.execute(text("""
            ALTER TABLE llm_configs
            ADD COLUMN api_format VARCHAR(32) NOT NULL DEFAULT 'openai_chat'
        """))

        await session.commit()
        print("✓ 迁移完成！")
        return True

    except Exception as e:
        await session.rollback()
        print(f"✗ 迁移失败: {e}")
        return False


async def main():
    """主函数"""
    print("=" * 50)
    print("LLM 配置表 api_format 字段迁移脚本")
    print("=" * 50)

    # 创建数据库引擎
    db_url = get_db_url()
    print(f"数据库: {db_url}")
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 检查是否需要迁移
        if not await check_migration_needed(session):
            print("\n" + "=" * 50)
            print("操作完成！")
            print("=" * 50)
            return

        # 根据数据库类型选择迁移方式
        if is_sqlite():
            success = await migrate_api_format_sqlite(session)
        elif is_mysql():
            success = await migrate_api_format_mysql(session)
        elif is_postgres():
            success = await migrate_api_format_postgres(session)
        else:
            print(f"✗ 不支持的数据库类型: {db_url}")
            success = False

        if not success:
            print("\n迁移失败，请检查错误信息并重试")
            return

    print("\n" + "=" * 50)
    print("操作完成！")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
