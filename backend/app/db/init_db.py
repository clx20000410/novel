# AIMETA P=数据库初始化_创建表和默认数据|R=创建表_初始化管理员|NR=不含业务逻辑|E=init_db|X=internal|A=初始化函数|D=sqlalchemy|S=db|RD=./README.ai
import logging

from pathlib import Path

from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from ..core.config import settings
from ..core.security import hash_password
from ..models import Prompt, SystemConfig, User
from .base import Base
from .system_config_defaults import SYSTEM_CONFIG_DEFAULTS
from .session import AsyncSessionLocal, engine

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """初始化数据库结构并确保默认管理员存在。"""

    await _ensure_database_exists()

    # ---- 第一步：创建所有表结构 ----
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("数据库表结构已初始化")
    await _ensure_schema_updates()

    # ---- 第二步：确保管理员账号至少存在一个 ----
    async with AsyncSessionLocal() as session:
        admin_exists = await session.execute(select(User).where(User.is_admin.is_(True)))
        if not admin_exists.scalars().first():
            logger.warning("未检测到管理员账号，正在创建默认管理员 ...")
            admin_user = User(
                username=settings.admin_default_username,
                email=settings.admin_default_email,
                hashed_password=hash_password(settings.admin_default_password),
                is_admin=True,
            )

            session.add(admin_user)
            try:
                await session.commit()
                logger.info("默认管理员创建完成：%s", settings.admin_default_username)
            except IntegrityError:
                await session.rollback()
                logger.exception("默认管理员创建失败，可能是并发启动导致，请检查数据库状态")

        # ---- 第三步：同步系统配置到数据库 ----
        for entry in SYSTEM_CONFIG_DEFAULTS:
            value = entry.value_getter(settings)
            if value is None:
                continue
            existing = await session.get(SystemConfig, entry.key)
            if existing:
                if entry.description and existing.description != entry.description:
                    existing.description = entry.description
                continue
            session.add(
                SystemConfig(
                    key=entry.key,
                    value=value,
                    description=entry.description,
                )
            )

        await _ensure_default_prompts(session)

        await session.commit()


async def _ensure_database_exists() -> None:
    """在首次连接前确认数据库存在，针对不同驱动做最小化准备工作。"""
    url = make_url(settings.sqlalchemy_database_uri)

    if url.get_backend_name() == "sqlite":
        # SQLite 采用文件数据库，确保父目录存在即可，无需额外建库语句
        db_path = Path(url.database or "").expanduser()
        if not db_path.is_absolute():
            project_root = Path(__file__).resolve().parents[2]
            db_path = (project_root / db_path).resolve()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return

    database = (url.database or "").strip("/")
    if not database:
        return

    admin_url = URL.create(
        drivername=url.drivername,
        username=url.username,
        password=url.password,
        host=url.host,
        port=url.port,
        database=None,
        query=url.query,
    )

    admin_engine = create_async_engine(
        admin_url.render_as_string(hide_password=False),
        isolation_level="AUTOCOMMIT",
    )
    async with admin_engine.begin() as conn:
        await conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{database}`"))
    await admin_engine.dispose()


async def _ensure_schema_updates() -> None:
    """补齐历史版本缺失的列，避免旧库在新版本报错。"""
    async with engine.begin() as conn:
        def _upgrade(sync_conn):
            inspector = inspect(sync_conn)

            # 升级 chapter_outlines 表
            if "chapter_outlines" in inspector.get_table_names():
                columns = {col["name"] for col in inspector.get_columns("chapter_outlines")}
                if "metadata" not in columns:
                    sync_conn.execute(text("ALTER TABLE chapter_outlines ADD COLUMN metadata JSON"))

            # 升级 llm_configs 表（从单配置迁移到多配置）
            if "llm_configs" in inspector.get_table_names():
                columns = {col["name"] for col in inspector.get_columns("llm_configs")}
                if "id" not in columns:
                    logger.info("检测到旧版 llm_configs 表结构，正在迁移到多配置模式...")
                    _migrate_llm_configs_table(sync_conn)
                    logger.info("llm_configs 表迁移完成")

        await conn.run_sync(_upgrade)


def _migrate_llm_configs_table(sync_conn) -> None:
    """将 llm_configs 表从单配置（user_id 主键）迁移到多配置（id 主键）"""
    # 1. 创建临时表（新结构）
    sync_conn.execute(text("""
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

    # 2. 迁移现有数据（旧配置自动设为激活状态，名称为"默认配置"）
    sync_conn.execute(text("""
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
    sync_conn.execute(text("DROP TABLE llm_configs"))

    # 4. 重命名新表
    sync_conn.execute(text("ALTER TABLE llm_configs_new RENAME TO llm_configs"))

    # 5. 创建索引
    sync_conn.execute(text("CREATE INDEX IF NOT EXISTS ix_llm_configs_user_id ON llm_configs(user_id)"))


async def _ensure_default_prompts(session: AsyncSession) -> None:
    prompts_dir = Path(__file__).resolve().parents[2] / "prompts"
    if not prompts_dir.is_dir():
        return

    result = await session.execute(select(Prompt.name))
    existing_names = set(result.scalars().all())

    for prompt_file in sorted(prompts_dir.glob("*.md")):
        name = prompt_file.stem
        if name in existing_names:
            continue
        content = prompt_file.read_text(encoding="utf-8")
        session.add(Prompt(name=name, content=content))
