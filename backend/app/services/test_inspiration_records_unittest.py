# AIMETA P=灵感记录_状态机与单活策略测试|R=状态流转_查询_放弃|NR=不依赖外部服务|E=unittest_async|X=internal|A=单元测试|D=unittest,sqlalchemy|S=db|RD=./README.ai
import unittest

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.novel import NovelProject
from app.models.user import User
from app.services.novel_service import NovelService


class TestInspirationRecords(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        self.SessionLocal = async_sessionmaker(bind=self.engine, expire_on_commit=False)

        async with self.SessionLocal() as session:
            session.add(User(id=1, username="tester", hashed_password="x"))
            await session.commit()

    async def asyncTearDown(self) -> None:
        await self.engine.dispose()

    async def test_create_project_sets_status(self) -> None:
        async with self.SessionLocal() as session:
            service = NovelService(session)
            project = await service.create_project(1, "未命名灵感", "开始灵感模式")
            self.assertEqual(project.status, "concept_in_progress")

    async def test_get_active_inspiration_project_and_abandon(self) -> None:
        async with self.SessionLocal() as session:
            service = NovelService(session)

            p1 = await service.create_project(1, "灵感1", "p1")
            p2 = await service.create_project(1, "灵感2", "p2")

            active = await service.get_active_inspiration_project(1)
            self.assertIsNotNone(active)
            self.assertEqual(active.id, p2.id)

            # blueprint_ready 不应被视为可继续的灵感
            p2.status = "blueprint_ready"
            await session.commit()

            active = await service.get_active_inspiration_project(1)
            self.assertIsNotNone(active)
            self.assertEqual(active.id, p1.id)

            # concept_complete 仍可在 /inspiration 打开蓝图确认流程
            p1.status = "concept_complete"
            await session.commit()

            active = await service.get_active_inspiration_project(1)
            self.assertIsNotNone(active)
            self.assertEqual(active.id, p1.id)

            abandoned_count = await service.abandon_active_inspiration_projects(1)
            self.assertEqual(abandoned_count, 1)

            active = await service.get_active_inspiration_project(1)
            self.assertIsNone(active)

            refreshed = await session.scalar(select(NovelProject).where(NovelProject.id == p1.id))
            self.assertIsNotNone(refreshed)
            self.assertEqual(refreshed.status, "concept_abandoned")
