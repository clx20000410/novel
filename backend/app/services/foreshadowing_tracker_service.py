"""
伏笔追踪服务

提供伏笔的状态追踪、提醒和发展建议功能。
"""
from typing import Optional, List, Dict, Any
import json
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ..models.foreshadowing import (
    Foreshadowing, 
    ForeshadowingStatusHistory,
    ForeshadowingReminder
)
from .llm_service import LLMService
from .prompt_service import PromptService


class ForeshadowingTrackerService:
    """伏笔追踪服务"""

    def __init__(self, db: AsyncSession, llm_service: LLMService, prompt_service: PromptService):
        self.db = db
        self.llm_service = llm_service
        self.prompt_service = prompt_service

    async def get_active_foreshadowings(self, project_id: str) -> List[Foreshadowing]:
        """获取所有活跃的伏笔（未揭示/未放弃）"""
        result = await self.db.execute(
            select(Foreshadowing).where(
                and_(
                    Foreshadowing.project_id == project_id,
                    Foreshadowing.status.in_(["planted", "developing", "partial"])
                )
            ).order_by(Foreshadowing.chapter_number)
        )
        return list(result.scalars().all())

    async def get_foreshadowings_for_chapter(
        self, 
        project_id: str, 
        chapter_number: int
    ) -> Dict[str, List[Foreshadowing]]:
        """获取与指定章节相关的伏笔"""
        all_active = await self.get_active_foreshadowings(project_id)
        
        result = {
            "urgent": [],  # 紧迫的伏笔
            "due_soon": [],  # 即将到期的伏笔
            "overdue": [],  # 超期的伏笔
            "related": []  # 相关的伏笔
        }
        
        for fs in all_active:
            # 检查紧迫度
            if fs.urgency and fs.urgency >= 8:
                result["urgent"].append(fs)
                continue
            
            # 检查是否即将到期
            if fs.target_reveal_chapter:
                chapters_until = fs.target_reveal_chapter - chapter_number
                if 0 <= chapters_until <= 3:
                    result["due_soon"].append(fs)
                    continue
                elif chapters_until < 0:
                    result["overdue"].append(fs)
                    continue
            
            # 检查是否超期（埋下后超过20章）
            if fs.chapter_number:
                chapters_since = chapter_number - fs.chapter_number
                if chapters_since >= 20:
                    result["overdue"].append(fs)
                    continue
            
            # 其他相关伏笔
            result["related"].append(fs)
        
        return result

    async def update_foreshadowing_status(
        self,
        foreshadowing_id: int,
        new_status: str,
        chapter_number: Optional[int] = None,
        reason: Optional[str] = None,
        action_taken: Optional[str] = None
    ) -> Optional[Foreshadowing]:
        """更新伏笔状态并记录历史"""
        result = await self.db.execute(
            select(Foreshadowing).where(Foreshadowing.id == foreshadowing_id)
        )
        fs = result.scalar_one_or_none()
        
        if fs is None:
            return None
        
        old_status = fs.status
        
        # 记录状态变更历史
        history = ForeshadowingStatusHistory(
            foreshadowing_id=foreshadowing_id,
            old_status=old_status,
            new_status=new_status,
            chapter_number=chapter_number,
            reason=reason,
            action_taken=action_taken
        )
        self.db.add(history)
        
        # 更新伏笔状态
        fs.status = new_status
        if new_status == "revealed" and chapter_number:
            fs.resolved_chapter_number = chapter_number
        
        await self.db.commit()
        await self.db.refresh(fs)
        return fs

    async def create_foreshadowing(
        self,
        project_id: str,
        chapter_id: int,
        chapter_number: int,
        content: str,
        foreshadowing_type: str = "hint",
        name: Optional[str] = None,
        target_reveal_chapter: Optional[int] = None,
        importance: str = "minor",
        related_characters: Optional[List[str]] = None
    ) -> Foreshadowing:
        """创建新伏笔"""
        fs = Foreshadowing(
            project_id=project_id,
            chapter_id=chapter_id,
            chapter_number=chapter_number,
            content=content,
            type=foreshadowing_type,
            name=name,
            target_reveal_chapter=target_reveal_chapter,
            importance=importance,
            related_characters=related_characters,
            status="planted"
        )
        self.db.add(fs)
        await self.db.commit()
        await self.db.refresh(fs)
        return fs

    async def get_foreshadowing_reminders(
        self,
        project_id: str,
        chapter_number: int,
        chapter_outline: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取伏笔提醒和发展建议"""
        
        # 获取分类后的伏笔
        categorized = await self.get_foreshadowings_for_chapter(project_id, chapter_number)
        
        # 构建活跃伏笔上下文
        active_context = self._build_foreshadowing_context(categorized)
        
        # 获取提示词
        prompt_template = await self.prompt_service.get_prompt("foreshadowing_reminder")
        if not prompt_template:
            return self._create_basic_reminders(categorized, chapter_number)
        
        # 构建提示词
        prompt = prompt_template
        prompt = prompt.replace("{{chapter_number}}", str(chapter_number))
        prompt = prompt.replace("{{chapter_title}}", "")
        prompt = prompt.replace("{{chapter_outline}}", chapter_outline or "（无大纲）")
        prompt = prompt.replace("{{active_foreshadowings}}", active_context)
        
        # 调用 LLM 获取建议
        response = await self.llm_service.generate(
            prompt=prompt,
            system_prompt="你是一位专业的小说编辑，负责追踪伏笔状态并提供发展建议。请以 JSON 格式输出。"
        )
        
        # 解析结果
        try:
            content = response or ""
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                result = json.loads(content[json_start:json_end])
                return result
        except json.JSONDecodeError:
            pass
        
        return self._create_basic_reminders(categorized, chapter_number)

    def _build_foreshadowing_context(self, categorized: Dict[str, List[Foreshadowing]]) -> str:
        """构建伏笔上下文"""
        lines = []
        
        if categorized["urgent"]:
            lines.append("## 紧迫伏笔（必须处理）")
            for fs in categorized["urgent"]:
                lines.append(f"- [{fs.id}] {fs.name or '未命名'}: {fs.content[:100]}...")
                lines.append(f"  - 状态: {fs.status}, 紧迫度: {fs.urgency}")
        
        if categorized["due_soon"]:
            lines.append("\n## 即将到期伏笔")
            for fs in categorized["due_soon"]:
                lines.append(f"- [{fs.id}] {fs.name or '未命名'}: {fs.content[:100]}...")
                lines.append(f"  - 目标揭示章节: 第 {fs.target_reveal_chapter} 章")
        
        if categorized["overdue"]:
            lines.append("\n## 超期伏笔（需要关注）")
            for fs in categorized["overdue"]:
                lines.append(f"- [{fs.id}] {fs.name or '未命名'}: {fs.content[:100]}...")
                lines.append(f"  - 埋下章节: 第 {fs.chapter_number} 章")
        
        if categorized["related"]:
            lines.append("\n## 其他活跃伏笔")
            for fs in categorized["related"][:10]:  # 限制数量
                lines.append(f"- [{fs.id}] {fs.name or '未命名'}: {fs.content[:50]}...")
        
        return "\n".join(lines) if lines else "（无活跃伏笔）"

    def _create_basic_reminders(
        self, 
        categorized: Dict[str, List[Foreshadowing]], 
        chapter_number: int
    ) -> Dict[str, Any]:
        """创建基本提醒（不使用 LLM）"""
        reminders = []
        
        for fs in categorized["urgent"]:
            reminders.append({
                "id": fs.id,
                "name": fs.name or "未命名",
                "reason": f"紧迫度高（{fs.urgency}），需要立即处理",
                "urgency": "high",
                "suggested_development": "建议在本章推进或揭示"
            })
        
        for fs in categorized["due_soon"]:
            reminders.append({
                "id": fs.id,
                "name": fs.name or "未命名",
                "reason": f"目标揭示章节为第 {fs.target_reveal_chapter} 章，即将到期",
                "urgency": "medium",
                "suggested_development": "建议开始铺垫揭示"
            })
        
        for fs in categorized["overdue"]:
            reminders.append({
                "id": fs.id,
                "name": fs.name or "未命名",
                "reason": f"埋下后已超过 {chapter_number - fs.chapter_number} 章，建议处理",
                "urgency": "medium",
                "suggested_development": "建议揭示或转为红鲱鱼"
            })
        
        total_active = sum(len(v) for v in categorized.values())
        
        return {
            "foreshadowings_to_develop": reminders,
            "new_foreshadowing_suggestions": [],
            "health_assessment": {
                "total_active": total_active,
                "overdue_count": len(categorized["overdue"]),
                "average_age_chapters": 0,
                "distribution_score": 80 if total_active < 20 else 60,
                "overall_health": "healthy" if len(categorized["overdue"]) < 3 else "warning",
                "recommendations": []
            }
        }

    async def analyze_foreshadowing_health(self, project_id: str) -> Dict[str, Any]:
        """分析伏笔系统健康度"""
        all_foreshadowings = await self.db.execute(
            select(Foreshadowing).where(Foreshadowing.project_id == project_id)
        )
        all_fs = list(all_foreshadowings.scalars().all())
        
        if not all_fs:
            return {
                "total": 0,
                "health_score": 100,
                "status": "healthy",
                "recommendations": ["开始埋设伏笔以增加故事深度"]
            }
        
        # 统计各状态数量
        status_counts = {}
        for fs in all_fs:
            status_counts[fs.status] = status_counts.get(fs.status, 0) + 1
        
        total = len(all_fs)
        revealed = status_counts.get("revealed", 0)
        planted = status_counts.get("planted", 0)
        abandoned = status_counts.get("abandoned", 0)
        
        # 计算健康分数
        reveal_ratio = revealed / total if total > 0 else 0
        abandon_ratio = abandoned / total if total > 0 else 0
        
        health_score = 100
        recommendations = []
        
        # 揭示率过低
        if reveal_ratio < 0.3 and total > 10:
            health_score -= 20
            recommendations.append("伏笔揭示率较低，建议加快揭示节奏")
        
        # 放弃率过高
        if abandon_ratio > 0.2:
            health_score -= 15
            recommendations.append("伏笔放弃率较高，建议更谨慎地埋设伏笔")
        
        # 活跃伏笔过多
        if planted > 15:
            health_score -= 10
            recommendations.append(f"当前有 {planted} 个未揭示伏笔，建议控制数量")
        
        status = "healthy" if health_score >= 80 else ("warning" if health_score >= 60 else "critical")
        
        return {
            "total": total,
            "status_counts": status_counts,
            "reveal_ratio": reveal_ratio,
            "abandon_ratio": abandon_ratio,
            "health_score": max(0, health_score),
            "status": status,
            "recommendations": recommendations
        }
