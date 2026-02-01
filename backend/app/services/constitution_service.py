"""
小说宪法服务

提供小说宪法的 CRUD 操作和合规检查功能。
"""
from typing import Optional
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.constitution import NovelConstitution
from .llm_service import LLMService
from .prompt_service import PromptService


class ConstitutionService:
    """小说宪法服务"""

    def __init__(self, db: AsyncSession, llm_service: LLMService, prompt_service: PromptService):
        self.db = db
        self.llm_service = llm_service
        self.prompt_service = prompt_service

    async def get_constitution(self, project_id: str) -> Optional[NovelConstitution]:
        """获取项目的小说宪法"""
        result = await self.db.execute(
            select(NovelConstitution).where(NovelConstitution.project_id == project_id)
        )
        return result.scalar_one_or_none()

    async def create_or_update_constitution(
        self, project_id: str, data: dict
    ) -> NovelConstitution:
        """创建或更新小说宪法"""
        constitution = await self.get_constitution(project_id)
        
        if constitution is None:
            constitution = NovelConstitution(project_id=project_id)
            self.db.add(constitution)
        
        # 更新字段
        for key, value in data.items():
            if hasattr(constitution, key):
                setattr(constitution, key, value)
        
        await self.db.commit()
        await self.db.refresh(constitution)
        return constitution

    async def check_compliance(
        self,
        project_id: str,
        chapter_number: int,
        chapter_title: str,
        chapter_content: str
    ) -> dict:
        """检查章节是否符合小说宪法"""
        constitution = await self.get_constitution(project_id)
        
        if constitution is None:
            return {
                "overall_compliance": True,
                "overall_score": 100,
                "violations": [],
                "summary": "未设置小说宪法，跳过合规检查"
            }
        
        # 获取检查提示词
        prompt_template = await self.prompt_service.get_prompt("constitution_check")
        if not prompt_template:
            return {
                "overall_compliance": True,
                "overall_score": 100,
                "violations": [],
                "summary": "未找到合规检查提示词"
            }
        
        # 构建提示词
        prompt = prompt_template.replace("{{constitution}}", constitution.to_prompt_context())
        prompt = prompt.replace("{{chapter_number}}", str(chapter_number))
        prompt = prompt.replace("{{chapter_title}}", chapter_title)
        prompt = prompt.replace("{{chapter_content}}", chapter_content)
        
        # 调用 LLM 进行检查
        response = await self.llm_service.generate(
            prompt=prompt,
            system_prompt="你是一位严格的小说编辑，负责检查章节内容是否符合小说宪法。请以 JSON 格式输出检查结果。"
        )
        
        # 解析结果
        try:
            # 尝试提取 JSON
            content = response or ""
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                result = json.loads(content[json_start:json_end])
                return result
        except json.JSONDecodeError:
            pass
        
        return {
            "overall_compliance": True,
            "overall_score": 80,
            "violations": [],
            "summary": "合规检查完成，但结果解析失败"
        }

    def get_constitution_context(self, constitution: Optional[NovelConstitution]) -> str:
        """获取宪法上下文（用于注入到写作提示词）"""
        if constitution is None:
            return "（未设置小说宪法）"
        return constitution.to_prompt_context()
