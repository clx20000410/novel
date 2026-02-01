"""
记忆层服务

提供角色状态追踪、时间线管理、因果链维护的核心功能。
"""
from typing import Optional, List, Dict, Any
import json
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from ..models.memory_layer import (
    CharacterState,
    TimelineEvent,
    CausalChain,
    StoryTimeTracker
)
from .llm_service import LLMService
from .prompt_service import PromptService

logger = logging.getLogger(__name__)


class MemoryLayerService:
    """记忆层服务"""

    def __init__(self, db: AsyncSession, llm_service: LLMService, prompt_service: PromptService):
        self.db = db
        self.llm_service = llm_service
        self.prompt_service = prompt_service

    # ===== 角色状态管理 =====

    async def get_character_state(
        self, 
        project_id: str, 
        character_name: str, 
        chapter_number: Optional[int] = None
    ) -> Optional[CharacterState]:
        """获取角色在指定章节的状态（默认最新）"""
        query = select(CharacterState).where(
            and_(
                CharacterState.project_id == project_id,
                CharacterState.character_name == character_name
            )
        )
        
        if chapter_number:
            query = query.where(CharacterState.chapter_number <= chapter_number)
        
        query = query.order_by(desc(CharacterState.chapter_number)).limit(1)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all_character_states(
        self, 
        project_id: str, 
        chapter_number: int
    ) -> List[CharacterState]:
        """获取所有角色在指定章节的最新状态"""
        # 使用子查询获取每个角色的最新状态
        subquery = (
            select(
                CharacterState.character_name,
                CharacterState.chapter_number.label("max_chapter")
            )
            .where(
                and_(
                    CharacterState.project_id == project_id,
                    CharacterState.chapter_number <= chapter_number
                )
            )
            .group_by(CharacterState.character_name)
            .subquery()
        )
        
        query = (
            select(CharacterState)
            .join(
                subquery,
                and_(
                    CharacterState.character_name == subquery.c.character_name,
                    CharacterState.chapter_number == subquery.c.max_chapter
                )
            )
            .where(CharacterState.project_id == project_id)
        )
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_character_state(
        self,
        project_id: str,
        character_name: str,
        chapter_number: int,
        state_updates: Dict[str, Any],
        character_id: Optional[int] = None
    ) -> CharacterState:
        """更新角色状态（创建新的状态快照）"""
        # 获取上一章的状态作为基础
        prev_state = await self.get_character_state(project_id, character_name, chapter_number - 1)
        
        # 创建新状态
        new_state = CharacterState(
            project_id=project_id,
            character_id=character_id or (prev_state.character_id if prev_state else None),
            character_name=character_name,
            chapter_number=chapter_number,
            # 继承上一章的状态
            location=prev_state.location if prev_state else None,
            emotion=prev_state.emotion if prev_state else None,
            emotion_intensity=prev_state.emotion_intensity if prev_state else None,
            health_status=prev_state.health_status if prev_state else "healthy",
            inventory=prev_state.inventory if prev_state else [],
            power_level=prev_state.power_level if prev_state else None,
            known_secrets=prev_state.known_secrets if prev_state else [],
            current_goals=prev_state.current_goals if prev_state else [],
        )
        
        # 应用更新
        for key, value in state_updates.items():
            if hasattr(new_state, key):
                setattr(new_state, key, value)
        
        self.db.add(new_state)
        await self.db.commit()
        await self.db.refresh(new_state)
        return new_state

    async def extract_character_states_from_chapter(
        self,
        project_id: str,
        chapter_number: int,
        chapter_content: str,
        character_names: List[str],
        user_id: int
    ) -> List[Dict[str, Any]]:
        """从章节内容中提取角色状态变化"""
        prompt = f"""分析以下章节内容，提取每个角色的状态变化。

[章节内容]
{chapter_content[:8000]}

[需要追踪的角色]
{json.dumps(character_names, ensure_ascii=False)}

请以 JSON 格式输出每个角色的状态变化：
```json
{{
  "character_states": [
    {{
      "character_name": "角色名",
      "location": "当前位置",
      "emotion": "主要情绪",
      "emotion_intensity": 1-10,
      "emotion_reason": "情绪原因",
      "health_status": "healthy/injured/critical",
      "injuries": ["受伤描述"],
      "inventory_changes": {{"gained": ["获得物品"], "lost": ["失去物品"]}},
      "relationship_changes": [{{"target": "对象", "change": "变化描述"}}],
      "new_knowledge": ["新获得的信息"],
      "goal_progress": [{{"goal": "目标", "progress": "进展"}}]
    }}
  ]
}}
```

只输出在本章中有变化或出场的角色。"""

        try:
            response = await self.llm_service.get_llm_response(
                system_prompt="你是一个专业的小说分析助手，负责追踪角色状态变化。请严格按照 JSON 格式输出。",
                conversation_history=[{"role": "user", "content": prompt}],
                temperature=0.2,
                user_id=user_id,
                timeout=120.0
            )
            
            # 解析 JSON
            content = response
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                result = json.loads(content[json_start:json_end])
                return result.get("character_states", [])
        except Exception as e:
            logger.warning(f"提取角色状态失败: {e}")
        
        return []

    # ===== 时间线管理 =====

    async def get_timeline(
        self, 
        project_id: str, 
        start_chapter: Optional[int] = None,
        end_chapter: Optional[int] = None
    ) -> List[TimelineEvent]:
        """获取时间线事件"""
        query = select(TimelineEvent).where(TimelineEvent.project_id == project_id)
        
        if start_chapter:
            query = query.where(TimelineEvent.chapter_number >= start_chapter)
        if end_chapter:
            query = query.where(TimelineEvent.chapter_number <= end_chapter)
        
        query = query.order_by(TimelineEvent.chapter_number, TimelineEvent.id)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def add_timeline_event(
        self,
        project_id: str,
        chapter_number: int,
        event_title: str,
        event_description: str,
        event_type: str = "minor",
        story_time: Optional[str] = None,
        involved_characters: Optional[List[str]] = None,
        location: Optional[str] = None,
        importance: int = 5,
        is_turning_point: bool = False
    ) -> TimelineEvent:
        """添加时间线事件"""
        event = TimelineEvent(
            project_id=project_id,
            chapter_number=chapter_number,
            event_title=event_title,
            event_description=event_description,
            event_type=event_type,
            story_time=story_time,
            involved_characters=involved_characters,
            location=location,
            importance=importance,
            is_turning_point=is_turning_point
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def extract_timeline_events_from_chapter(
        self,
        project_id: str,
        chapter_number: int,
        chapter_content: str,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """从章节内容中提取时间线事件"""
        prompt = f"""分析以下章节内容，提取关键事件。

[章节内容]
{chapter_content[:8000]}

请以 JSON 格式输出关键事件：
```json
{{
  "events": [
    {{
      "event_title": "事件标题（简短）",
      "event_description": "事件描述",
      "event_type": "major/minor/background",
      "story_time": "故事内时间（如'第三天早上'）",
      "involved_characters": ["涉及角色"],
      "location": "发生地点",
      "importance": 1-10,
      "is_turning_point": true/false
    }}
  ]
}}
```

只提取重要事件，不要列出琐碎细节。"""

        try:
            response = await self.llm_service.get_llm_response(
                system_prompt="你是一个专业的小说分析助手，负责提取关键事件。请严格按照 JSON 格式输出。",
                conversation_history=[{"role": "user", "content": prompt}],
                temperature=0.2,
                user_id=user_id,
                timeout=120.0
            )
            
            content = response
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                result = json.loads(content[json_start:json_end])
                return result.get("events", [])
        except Exception as e:
            logger.warning(f"提取时间线事件失败: {e}")
        
        return []

    # ===== 因果链管理 =====

    async def get_pending_causal_chains(self, project_id: str) -> List[CausalChain]:
        """获取待解决的因果链"""
        result = await self.db.execute(
            select(CausalChain).where(
                and_(
                    CausalChain.project_id == project_id,
                    CausalChain.status == "pending"
                )
            ).order_by(CausalChain.cause_chapter)
        )
        return list(result.scalars().all())

    async def add_causal_chain(
        self,
        project_id: str,
        cause_description: str,
        cause_chapter: int,
        effect_description: str,
        cause_type: str = "event",
        effect_type: str = "event",
        involved_characters: Optional[List[str]] = None,
        importance: int = 5
    ) -> CausalChain:
        """添加因果链"""
        chain = CausalChain(
            project_id=project_id,
            cause_type=cause_type,
            cause_description=cause_description,
            cause_chapter=cause_chapter,
            effect_type=effect_type,
            effect_description=effect_description,
            involved_characters=involved_characters,
            importance=importance,
            status="pending"
        )
        self.db.add(chain)
        await self.db.commit()
        await self.db.refresh(chain)
        return chain

    async def resolve_causal_chain(
        self,
        chain_id: int,
        effect_chapter: int,
        resolution_description: str
    ) -> Optional[CausalChain]:
        """解决因果链"""
        result = await self.db.execute(
            select(CausalChain).where(CausalChain.id == chain_id)
        )
        chain = result.scalar_one_or_none()
        
        if chain:
            chain.status = "resolved"
            chain.effect_chapter = effect_chapter
            chain.resolution_description = resolution_description
            await self.db.commit()
            await self.db.refresh(chain)
        
        return chain

    # ===== 故事时间追踪 =====

    async def get_or_create_time_tracker(self, project_id: str) -> StoryTimeTracker:
        """获取或创建故事时间追踪器"""
        result = await self.db.execute(
            select(StoryTimeTracker).where(StoryTimeTracker.project_id == project_id)
        )
        tracker = result.scalar_one_or_none()
        
        if not tracker:
            tracker = StoryTimeTracker(
                project_id=project_id,
                chapter_time_map={}
            )
            self.db.add(tracker)
            await self.db.commit()
            await self.db.refresh(tracker)
        
        return tracker

    async def update_chapter_time(
        self,
        project_id: str,
        chapter_number: int,
        start_time: str,
        end_time: str,
        duration: str
    ) -> StoryTimeTracker:
        """更新章节时间"""
        tracker = await self.get_or_create_time_tracker(project_id)
        
        chapter_time_map = tracker.chapter_time_map or {}
        chapter_time_map[str(chapter_number)] = {
            "start_time": start_time,
            "end_time": end_time,
            "duration": duration
        }
        tracker.chapter_time_map = chapter_time_map
        tracker.current_time = end_time
        
        await self.db.commit()
        await self.db.refresh(tracker)
        return tracker

    # ===== 综合上下文生成 =====

    async def get_memory_context(
        self,
        project_id: str,
        chapter_number: int,
        involved_characters: Optional[List[str]] = None
    ) -> str:
        """生成记忆层上下文（用于注入到写作提示词）"""
        lines = ["# 记忆层上下文\n"]
        
        # 1. 角色状态
        character_states = await self.get_all_character_states(project_id, chapter_number - 1)
        if character_states:
            lines.append("## 角色当前状态\n")
            for state in character_states:
                if involved_characters and state.character_name not in involved_characters:
                    continue
                lines.append(f"### {state.character_name}")
                if state.location:
                    lines.append(f"- 位置：{state.location}")
                if state.emotion:
                    lines.append(f"- 情绪：{state.emotion}（强度 {state.emotion_intensity}/10）")
                if state.health_status and state.health_status != "healthy":
                    lines.append(f"- 健康：{state.health_status}")
                if state.current_goals:
                    lines.append(f"- 当前目标：{', '.join(state.current_goals[:3])}")
                lines.append("")
        
        # 2. 最近事件
        recent_events = await self.get_timeline(
            project_id, 
            start_chapter=max(1, chapter_number - 5),
            end_chapter=chapter_number - 1
        )
        if recent_events:
            lines.append("## 最近事件\n")
            for event in recent_events[-10:]:  # 最多显示 10 个
                lines.append(f"- 第{event.chapter_number}章：{event.event_title}")
                if event.is_turning_point:
                    lines.append("  （转折点）")
            lines.append("")
        
        # 3. 待解决的因果链
        pending_chains = await self.get_pending_causal_chains(project_id)
        if pending_chains:
            lines.append("## 待解决的因果链\n")
            for chain in pending_chains[:5]:  # 最多显示 5 个
                lines.append(f"- 【第{chain.cause_chapter}章】{chain.cause_description}")
                lines.append(f"  → 预期效果：{chain.effect_description}")
            lines.append("")
        
        # 4. 故事时间
        tracker = await self.get_or_create_time_tracker(project_id)
        if tracker.current_time:
            lines.append("## 故事时间\n")
            lines.append(f"- 当前时间：{tracker.current_time}")
            if tracker.current_date:
                lines.append(f"- 当前日期：{tracker.current_date}")
            lines.append("")
        
        return "\n".join(lines) if len(lines) > 1 else "（无记忆层上下文）"

    async def update_memory_after_chapter(
        self,
        project_id: str,
        chapter_number: int,
        chapter_content: str,
        character_names: List[str],
        user_id: int
    ) -> Dict[str, Any]:
        """章节完成后更新记忆层"""
        results = {
            "character_states_updated": 0,
            "timeline_events_added": 0,
            "causal_chains_added": 0
        }
        
        # 1. 提取并更新角色状态
        character_states = await self.extract_character_states_from_chapter(
            project_id, chapter_number, chapter_content, character_names, user_id
        )
        for state_data in character_states:
            char_name = state_data.pop("character_name", None)
            if char_name:
                await self.update_character_state(
                    project_id, char_name, chapter_number, state_data
                )
                results["character_states_updated"] += 1
        
        # 2. 提取并添加时间线事件
        events = await self.extract_timeline_events_from_chapter(
            project_id, chapter_number, chapter_content, user_id
        )
        for event_data in events:
            await self.add_timeline_event(
                project_id=project_id,
                chapter_number=chapter_number,
                **event_data
            )
            results["timeline_events_added"] += 1
        
        logger.info(
            f"项目 {project_id} 第 {chapter_number} 章记忆层更新完成: "
            f"角色状态 {results['character_states_updated']}, "
            f"时间线事件 {results['timeline_events_added']}"
        )
        
        return results

    async def check_consistency(
        self,
        project_id: str,
        chapter_number: int,
        chapter_content: str,
        user_id: int
    ) -> Dict[str, Any]:
        """检查章节与记忆层的一致性"""
        issues = []
        
        # 获取记忆层上下文
        memory_context = await self.get_memory_context(project_id, chapter_number)
        
        prompt = f"""检查以下章节内容与记忆层上下文的一致性。

[记忆层上下文]
{memory_context}

[章节内容]
{chapter_content[:6000]}

请检查以下方面的一致性：
1. 角色位置是否合理（不能瞬移）
2. 角色情绪是否连贯
3. 角色持有物品是否正确
4. 时间流逝是否合理
5. 事件因果是否自洽

以 JSON 格式输出检查结果：
```json
{{
  "consistent": true/false,
  "issues": [
    {{
      "type": "location/emotion/inventory/time/causality",
      "severity": "critical/warning/minor",
      "description": "问题描述",
      "suggestion": "修复建议"
    }}
  ]
}}
```"""

        try:
            response = await self.llm_service.get_llm_response(
                system_prompt="你是一个专业的小说一致性检查助手。请严格按照 JSON 格式输出。",
                conversation_history=[{"role": "user", "content": prompt}],
                temperature=0.2,
                user_id=user_id,
                timeout=120.0
            )
            
            content = response
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(content[json_start:json_end])
        except Exception as e:
            logger.warning(f"一致性检查失败: {e}")
        
        return {"consistent": True, "issues": []}
