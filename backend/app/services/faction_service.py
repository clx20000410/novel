"""
势力关系网络服务

提供势力的 CRUD 操作、关系管理和上下文生成功能。
"""
from typing import Optional, List, Dict, Any
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from ..models.faction import (
    Faction,
    FactionRelationship,
    FactionMember,
    FactionRelationshipHistory
)
from .prompt_service import PromptService


class FactionService:
    """势力关系网络服务"""

    def __init__(self, db: AsyncSession, prompt_service: PromptService):
        self.db = db
        self.prompt_service = prompt_service

    # ===== 势力 CRUD =====

    async def get_faction(self, faction_id: int) -> Optional[Faction]:
        """获取势力"""
        result = await self.db.execute(
            select(Faction).where(Faction.id == faction_id)
        )
        return result.scalar_one_or_none()

    async def get_factions_by_project(self, project_id: str) -> List[Faction]:
        """获取项目的所有势力"""
        result = await self.db.execute(
            select(Faction).where(Faction.project_id == project_id)
        )
        return list(result.scalars().all())

    async def create_faction(self, project_id: str, data: dict) -> Faction:
        """创建势力"""
        faction = Faction(project_id=project_id)
        for key, value in data.items():
            if hasattr(faction, key):
                setattr(faction, key, value)
        self.db.add(faction)
        await self.db.commit()
        await self.db.refresh(faction)
        return faction

    async def update_faction(self, faction_id: int, data: dict) -> Optional[Faction]:
        """更新势力"""
        faction = await self.get_faction(faction_id)
        if faction is None:
            return None
        for key, value in data.items():
            if hasattr(faction, key):
                setattr(faction, key, value)
        await self.db.commit()
        await self.db.refresh(faction)
        return faction

    # ===== 势力关系 =====

    async def get_faction_relationships(self, project_id: str) -> List[FactionRelationship]:
        """获取项目的所有势力关系"""
        result = await self.db.execute(
            select(FactionRelationship).where(FactionRelationship.project_id == project_id)
        )
        return list(result.scalars().all())

    async def get_relationships_for_faction(self, faction_id: int) -> List[FactionRelationship]:
        """获取指定势力的所有关系"""
        result = await self.db.execute(
            select(FactionRelationship).where(
                or_(
                    FactionRelationship.faction_from_id == faction_id,
                    FactionRelationship.faction_to_id == faction_id
                )
            )
        )
        return list(result.scalars().all())

    async def create_relationship(
        self,
        project_id: str,
        faction_from_id: int,
        faction_to_id: int,
        relationship_type: str,
        strength: int = 5,
        description: Optional[str] = None,
        reason: Optional[str] = None
    ) -> FactionRelationship:
        """创建势力关系"""
        relationship = FactionRelationship(
            project_id=project_id,
            faction_from_id=faction_from_id,
            faction_to_id=faction_to_id,
            relationship_type=relationship_type,
            strength=strength,
            description=description,
            reason=reason
        )
        self.db.add(relationship)
        await self.db.commit()
        await self.db.refresh(relationship)
        return relationship

    async def update_relationship(
        self,
        relationship_id: int,
        new_type: Optional[str] = None,
        new_strength: Optional[int] = None,
        reason: Optional[str] = None,
        chapter_number: Optional[int] = None
    ) -> Optional[FactionRelationship]:
        """更新势力关系并记录历史"""
        result = await self.db.execute(
            select(FactionRelationship).where(FactionRelationship.id == relationship_id)
        )
        relationship = result.scalar_one_or_none()
        
        if relationship is None:
            return None
        
        # 记录历史
        if new_type or new_strength:
            history = FactionRelationshipHistory(
                relationship_id=relationship_id,
                old_type=relationship.relationship_type if new_type else None,
                new_type=new_type or relationship.relationship_type,
                old_strength=relationship.strength if new_strength else None,
                new_strength=new_strength or relationship.strength,
                reason=reason,
                chapter_number=chapter_number
            )
            self.db.add(history)
        
        # 更新关系
        if new_type:
            relationship.relationship_type = new_type
        if new_strength:
            relationship.strength = new_strength
        
        await self.db.commit()
        await self.db.refresh(relationship)
        return relationship

    # ===== 势力成员 =====

    async def get_faction_members(self, faction_id: int) -> List[FactionMember]:
        """获取势力的所有成员"""
        result = await self.db.execute(
            select(FactionMember).where(FactionMember.faction_id == faction_id)
        )
        return list(result.scalars().all())

    async def add_member_to_faction(
        self,
        project_id: str,
        faction_id: int,
        character_id: int,
        role: Optional[str] = None,
        rank: Optional[str] = None,
        loyalty: int = 5
    ) -> FactionMember:
        """将角色添加到势力"""
        member = FactionMember(
            project_id=project_id,
            faction_id=faction_id,
            character_id=character_id,
            role=role,
            rank=rank,
            loyalty=loyalty
        )
        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(member)
        return member

    async def get_character_factions(self, character_id: int) -> List[FactionMember]:
        """获取角色所属的所有势力"""
        result = await self.db.execute(
            select(FactionMember).where(FactionMember.character_id == character_id)
        )
        return list(result.scalars().all())

    # ===== 上下文生成 =====

    async def get_faction_context(self, project_id: str) -> str:
        """生成势力上下文（用于注入到写作提示词）"""
        factions = await self.get_factions_by_project(project_id)
        relationships = await self.get_faction_relationships(project_id)
        
        if not factions:
            return "（无势力设定）"
        
        lines = ["# 势力关系网络\n"]
        
        # 势力概览
        lines.append("## 势力概览\n")
        for faction in factions:
            lines.append(f"### {faction.name}")
            if faction.faction_type:
                lines.append(f"- 类型：{faction.faction_type}")
            if faction.power_level:
                lines.append(f"- 实力：{faction.power_level}")
            if faction.leader:
                lines.append(f"- 领袖：{faction.leader}")
            if faction.description:
                lines.append(f"- 描述：{faction.description[:200]}...")
            lines.append("")
        
        # 关系网络
        if relationships:
            lines.append("## 势力关系\n")
            
            # 创建势力 ID 到名称的映射
            faction_names = {f.id: f.name for f in factions}
            
            for rel in relationships:
                from_name = faction_names.get(rel.faction_from_id, "未知势力")
                to_name = faction_names.get(rel.faction_to_id, "未知势力")
                rel_type = self._translate_relationship_type(rel.relationship_type)
                lines.append(f"- {from_name} → {to_name}：{rel_type}（强度：{rel.strength}/10）")
                if rel.description:
                    lines.append(f"  - {rel.description}")
        
        return "\n".join(lines)

    def _translate_relationship_type(self, rel_type: str) -> str:
        """翻译关系类型"""
        translations = {
            "ally": "盟友",
            "enemy": "敌人",
            "rival": "竞争者",
            "neutral": "中立",
            "vassal": "附庸",
            "overlord": "宗主",
            "trade_partner": "贸易伙伴",
            "at_war": "交战中"
        }
        return translations.get(rel_type, rel_type)

    async def get_faction_writing_context(
        self,
        project_id: str,
        involved_factions: Optional[List[int]] = None
    ) -> str:
        """获取写作用的势力上下文（可指定相关势力）"""
        
        # 获取提示词模板
        prompt_template = await self.prompt_service.get_prompt("faction_context")
        if not prompt_template:
            return await self.get_faction_context(project_id)
        
        factions = await self.get_factions_by_project(project_id)
        relationships = await self.get_faction_relationships(project_id)
        
        # 如果指定了相关势力，只获取相关的
        if involved_factions:
            factions = [f for f in factions if f.id in involved_factions]
            relationships = [
                r for r in relationships 
                if r.faction_from_id in involved_factions or r.faction_to_id in involved_factions
            ]
        
        # 构建上下文
        factions_overview = self._build_factions_overview(factions)
        faction_relationships = self._build_relationships_overview(factions, relationships)
        faction_members = await self._build_members_overview(factions)
        
        # 填充模板
        context = prompt_template
        context = context.replace("{{factions_overview}}", factions_overview)
        context = context.replace("{{faction_relationships}}", faction_relationships)
        context = context.replace("{{faction_members}}", faction_members)
        
        return context

    def _build_factions_overview(self, factions: List[Faction]) -> str:
        """构建势力概览"""
        if not factions:
            return "（无势力）"
        
        lines = []
        for faction in factions:
            lines.append(f"### {faction.name}")
            if faction.faction_type:
                lines.append(f"- 类型：{faction.faction_type}")
            if faction.power_level:
                lines.append(f"- 实力：{faction.power_level}")
            if faction.territory:
                lines.append(f"- 领地：{faction.territory}")
            if faction.goals:
                lines.append(f"- 目标：{', '.join(faction.goals[:3])}")
            if faction.culture:
                lines.append(f"- 文化：{faction.culture[:100]}...")
            lines.append("")
        
        return "\n".join(lines)

    def _build_relationships_overview(
        self, 
        factions: List[Faction], 
        relationships: List[FactionRelationship]
    ) -> str:
        """构建关系概览"""
        if not relationships:
            return "（无势力关系）"
        
        faction_names = {f.id: f.name for f in factions}
        
        lines = []
        for rel in relationships:
            from_name = faction_names.get(rel.faction_from_id, "未知")
            to_name = faction_names.get(rel.faction_to_id, "未知")
            rel_type = self._translate_relationship_type(rel.relationship_type)
            lines.append(f"- {from_name} ↔ {to_name}：{rel_type}（强度 {rel.strength}/10）")
        
        return "\n".join(lines)

    async def _build_members_overview(self, factions: List[Faction]) -> str:
        """构建成员概览"""
        lines = []
        
        for faction in factions:
            members = await self.get_faction_members(faction.id)
            if members:
                lines.append(f"### {faction.name} 成员")
                for member in members[:5]:  # 限制数量
                    role_info = f"（{member.role}）" if member.role else ""
                    lines.append(f"- 角色 ID {member.character_id}{role_info}")
                lines.append("")
        
        return "\n".join(lines) if lines else "（无成员信息）"

    async def check_faction_consistency(
        self,
        project_id: str,
        chapter_content: str
    ) -> Dict[str, Any]:
        """检查章节中势力描写的一致性"""
        factions = await self.get_factions_by_project(project_id)
        
        issues = []
        
        for faction in factions:
            # 检查势力名称是否出现
            if faction.name in chapter_content:
                # 检查领袖名称一致性
                if faction.leader and faction.leader in chapter_content:
                    # 这里可以添加更复杂的检查逻辑
                    pass
        
        return {
            "consistent": len(issues) == 0,
            "issues": issues
        }
