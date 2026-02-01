# AIMETA P=LLM配置仓库_配置数据访问|R=配置CRUD|NR=不含业务逻辑|E=LLMConfigRepository|X=internal|A=仓库类|D=sqlalchemy|S=db|RD=./README.ai
from typing import Optional, List

from sqlalchemy import select

from .base import BaseRepository
from ..models import LLMConfig


class LLMConfigRepository(BaseRepository[LLMConfig]):
    """LLM 配置仓库，支持多配置管理。"""

    model = LLMConfig

    async def list_by_user(self, user_id: int) -> List[LLMConfig]:
        """获取用户的所有配置列表，按创建时间降序排列"""
        result = await self.session.execute(
            select(LLMConfig)
            .where(LLMConfig.user_id == user_id)
            .order_by(LLMConfig.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, config_id: int, user_id: int) -> Optional[LLMConfig]:
        """根据 ID 获取用户的某个配置"""
        result = await self.session.execute(
            select(LLMConfig).where(
                LLMConfig.id == config_id,
                LLMConfig.user_id == user_id
            )
        )
        return result.scalars().first()

    async def get_active_config(self, user_id: int) -> Optional[LLMConfig]:
        """获取用户当前激活的配置"""
        result = await self.session.execute(
            select(LLMConfig).where(
                LLMConfig.user_id == user_id,
                LLMConfig.is_active == True  # noqa: E712
            )
        )
        return result.scalars().first()

    async def deactivate_all(self, user_id: int) -> None:
        """取消激活用户的所有配置"""
        configs = await self.list_by_user(user_id)
        for config in configs:
            config.is_active = False
        await self.session.flush()

    async def count_by_user(self, user_id: int) -> int:
        """统计用户的配置数量"""
        configs = await self.list_by_user(user_id)
        return len(configs)

    # 兼容旧接口，保留 get_by_user 方法（获取激活配置）
    async def get_by_user(self, user_id: int) -> Optional[LLMConfig]:
        """兼容旧接口：获取用户当前激活的配置"""
        return await self.get_active_config(user_id)
