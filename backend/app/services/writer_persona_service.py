"""
Writer 人格服务

提供 Writer 人格的 CRUD 操作和风格注入功能。
"""
from typing import Optional, List
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.writer_persona import WriterPersona
from .llm_service import LLMService
from .prompt_service import PromptService


class WriterPersonaService:
    """Writer 人格服务"""

    def __init__(self, db: AsyncSession, llm_service: LLMService, prompt_service: PromptService):
        self.db = db
        self.llm_service = llm_service
        self.prompt_service = prompt_service

    async def get_active_persona(self, project_id: str) -> Optional[WriterPersona]:
        """获取项目的活跃 Writer 人格"""
        result = await self.db.execute(
            select(WriterPersona).where(
                WriterPersona.project_id == project_id,
                WriterPersona.is_active == True
            )
        )
        return result.scalar_one_or_none()

    async def get_all_personas(self, project_id: str) -> List[WriterPersona]:
        """获取项目的所有 Writer 人格"""
        result = await self.db.execute(
            select(WriterPersona).where(WriterPersona.project_id == project_id)
        )
        return list(result.scalars().all())

    async def get_persona_by_id(self, persona_id: int) -> Optional[WriterPersona]:
        """根据 ID 获取 Writer 人格"""
        result = await self.db.execute(
            select(WriterPersona).where(WriterPersona.id == persona_id)
        )
        return result.scalar_one_or_none()

    async def create_persona(self, project_id: str, data: dict) -> WriterPersona:
        """创建 Writer 人格"""
        persona = WriterPersona(project_id=project_id)
        
        for key, value in data.items():
            if hasattr(persona, key):
                setattr(persona, key, value)
        
        self.db.add(persona)
        await self.db.commit()
        await self.db.refresh(persona)
        return persona

    async def create_default_qidian_persona(self, project_id: str) -> WriterPersona:
        """创建起点中文网风格的默认 Writer"""
        persona = WriterPersona.create_default_qidian_writer(project_id)
        self.db.add(persona)
        await self.db.commit()
        await self.db.refresh(persona)
        return persona

    async def update_persona(self, persona_id: int, data: dict) -> Optional[WriterPersona]:
        """更新 Writer 人格"""
        persona = await self.get_persona_by_id(persona_id)
        if persona is None:
            return None
        
        for key, value in data.items():
            if hasattr(persona, key):
                setattr(persona, key, value)
        
        await self.db.commit()
        await self.db.refresh(persona)
        return persona

    async def set_active_persona(self, project_id: str, persona_id: int) -> bool:
        """设置活跃的 Writer 人格"""
        # 先将所有人格设为非活跃
        result = await self.db.execute(
            select(WriterPersona).where(WriterPersona.project_id == project_id)
        )
        personas = result.scalars().all()
        for p in personas:
            p.is_active = False
        
        # 设置指定人格为活跃
        persona = await self.get_persona_by_id(persona_id)
        if persona is None or persona.project_id != project_id:
            return False
        
        persona.is_active = True
        await self.db.commit()
        return True

    async def ensure_default_persona(self, project_id: str) -> WriterPersona:
        """确保项目有一个默认的 Writer 人格"""
        persona = await self.get_active_persona(project_id)
        if persona is None:
            persona = await self.create_default_qidian_persona(project_id)
        return persona

    def get_persona_context(self, persona: Optional[WriterPersona]) -> str:
        """获取人格上下文（用于注入到写作提示词）"""
        if persona is None:
            return "（使用默认写作风格）"
        return persona.to_prompt_context()

    def get_version_style_hint(self, persona: Optional[WriterPersona], version_index: int) -> str:
        """获取版本差异化风格提示"""
        base_hints = [
            "情绪更细腻，节奏更慢，多写内心戏和感官描写",
            "冲突更强，节奏更快，多写动作和对话",
            "悬念更重，多埋伏笔，结尾钩子更强"
        ]
        
        hint = base_hints[version_index % len(base_hints)]
        
        # 如果有人格，增加人格特定的变化
        if persona:
            if persona.catchphrases:
                catchphrase = persona.catchphrases[version_index % len(persona.catchphrases)]
                hint += f"，适当使用口头禅「{catchphrase}」"
            
            if persona.imperfection_patterns:
                pattern = persona.imperfection_patterns[version_index % len(persona.imperfection_patterns)]
                hint += f"，体现「{pattern}」"
        
        return hint

    async def check_style_compliance(
        self,
        project_id: str,
        chapter_content: str
    ) -> dict:
        """检查章节是否符合 Writer 风格"""
        persona = await self.get_active_persona(project_id)
        
        if persona is None:
            return {
                "compliance": True,
                "score": 100,
                "issues": [],
                "summary": "未设置 Writer 人格，跳过风格检查"
            }
        
        # 检查反 AI 检测规则
        issues = []
        
        # 检查是否有 AI 典型模式
        ai_patterns = persona.avoid_patterns or [
            "总的来说",
            "综上所述",
            "由此可见",
            "首先.*其次.*最后",
            "然而.*但是.*不过"
        ]
        
        import re
        for pattern in ai_patterns:
            if re.search(pattern, chapter_content):
                issues.append({
                    "type": "ai_pattern",
                    "severity": "warning",
                    "description": f"检测到 AI 典型模式：{pattern}",
                    "suggestion": "请使用更自然的表达方式"
                })
        
        # 检查口头禅使用
        if persona.catchphrases:
            catchphrase_used = any(cp in chapter_content for cp in persona.catchphrases)
            if not catchphrase_used:
                issues.append({
                    "type": "missing_catchphrase",
                    "severity": "info",
                    "description": "未使用任何口头禅",
                    "suggestion": f"建议适当使用：{', '.join(persona.catchphrases[:3])}"
                })
        
        score = 100 - len([i for i in issues if i["severity"] == "warning"]) * 10 - len([i for i in issues if i["severity"] == "info"]) * 2
        
        return {
            "compliance": len([i for i in issues if i["severity"] == "warning"]) == 0,
            "score": max(0, score),
            "issues": issues,
            "summary": f"风格检查完成，发现 {len(issues)} 个问题"
        }
