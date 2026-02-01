"""
势力关系网络数据模型

势力系统用于管理小说中的组织、门派、国家等势力实体：
- 势力档案（名称、类型、目标、现状）
- 势力关系（盟友、敌人、竞争者、中立）
- 成员管理（角色与势力的关联）
- 关系变更追踪（历史记录）
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base

LONG_TEXT_TYPE = Text().with_variant(LONGTEXT, "mysql")


class Faction(Base):
    """势力实体"""

    __tablename__ = "factions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("novel_projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    # ===== 基础信息 =====
    name: Mapped[str] = mapped_column(String(255), nullable=False)  # 势力名称
    faction_type: Mapped[Optional[str]] = mapped_column(String(64))  # 类型（门派/国家/组织/家族等）
    description: Mapped[Optional[str]] = mapped_column(LONG_TEXT_TYPE)  # 详细描述
    
    # ===== 势力属性 =====
    power_level: Mapped[Optional[str]] = mapped_column(String(64))  # 实力等级
    territory: Mapped[Optional[str]] = mapped_column(Text)  # 领地/势力范围
    resources: Mapped[Optional[list]] = mapped_column(JSON)  # 资源列表
    
    # ===== 组织结构 =====
    leader: Mapped[Optional[str]] = mapped_column(String(255))  # 领袖
    hierarchy: Mapped[Optional[dict]] = mapped_column(JSON)  # 组织架构
    member_count: Mapped[Optional[str]] = mapped_column(String(64))  # 成员规模
    
    # ===== 目标与现状 =====
    goals: Mapped[Optional[list]] = mapped_column(JSON)  # 目标列表
    current_status: Mapped[Optional[str]] = mapped_column(Text)  # 当前状态
    recent_events: Mapped[Optional[list]] = mapped_column(JSON)  # 近期事件
    
    # ===== 文化特征 =====
    culture: Mapped[Optional[str]] = mapped_column(Text)  # 文化特征
    rules: Mapped[Optional[list]] = mapped_column(JSON)  # 门规/法律
    traditions: Mapped[Optional[list]] = mapped_column(JSON)  # 传统
    
    # ===== 元数据 =====
    extra: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class FactionRelationship(Base):
    """势力间关系"""

    __tablename__ = "faction_relationships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("novel_projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    # ===== 关系双方 =====
    faction_from_id: Mapped[int] = mapped_column(
        ForeignKey("factions.id", ondelete="CASCADE"), nullable=False
    )
    faction_to_id: Mapped[int] = mapped_column(
        ForeignKey("factions.id", ondelete="CASCADE"), nullable=False
    )
    
    # ===== 关系属性 =====
    relationship_type: Mapped[str] = mapped_column(String(64), nullable=False)  # 关系类型
    # 可选值：ally（盟友）, enemy（敌人）, rival（竞争者）, neutral（中立）, 
    #        vassal（附庸）, overlord（宗主）, trade_partner（贸易伙伴）, at_war（交战中）
    
    strength: Mapped[Optional[int]] = mapped_column(Integer)  # 关系强度 1-10
    description: Mapped[Optional[str]] = mapped_column(Text)  # 关系描述
    terms: Mapped[Optional[list]] = mapped_column(JSON)  # 条约/协议内容
    
    # ===== 历史记录 =====
    established_at: Mapped[Optional[str]] = mapped_column(String(255))  # 建立时间（故事内时间）
    reason: Mapped[Optional[str]] = mapped_column(Text)  # 建立原因
    
    # ===== 元数据 =====
    extra: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class FactionMember(Base):
    """势力成员（角色与势力的关联）"""

    __tablename__ = "faction_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("novel_projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    faction_id: Mapped[int] = mapped_column(
        ForeignKey("factions.id", ondelete="CASCADE"), nullable=False
    )
    character_id: Mapped[int] = mapped_column(
        ForeignKey("blueprint_characters.id", ondelete="CASCADE"), nullable=False
    )
    
    # ===== 成员属性 =====
    role: Mapped[Optional[str]] = mapped_column(String(128))  # 在势力中的角色/职位
    rank: Mapped[Optional[str]] = mapped_column(String(64))  # 等级/地位
    loyalty: Mapped[Optional[int]] = mapped_column(Integer)  # 忠诚度 1-10
    joined_at: Mapped[Optional[str]] = mapped_column(String(255))  # 加入时间（故事内时间）
    
    # ===== 元数据 =====
    extra: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class FactionRelationshipHistory(Base):
    """势力关系变更历史"""

    __tablename__ = "faction_relationship_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    relationship_id: Mapped[int] = mapped_column(
        ForeignKey("faction_relationships.id", ondelete="CASCADE"), nullable=False
    )
    
    # ===== 变更内容 =====
    old_type: Mapped[Optional[str]] = mapped_column(String(64))  # 旧关系类型
    new_type: Mapped[str] = mapped_column(String(64), nullable=False)  # 新关系类型
    old_strength: Mapped[Optional[int]] = mapped_column(Integer)  # 旧强度
    new_strength: Mapped[Optional[int]] = mapped_column(Integer)  # 新强度
    
    # ===== 变更原因 =====
    reason: Mapped[Optional[str]] = mapped_column(Text)  # 变更原因
    chapter_number: Mapped[Optional[int]] = mapped_column(Integer)  # 发生在哪一章
    story_time: Mapped[Optional[str]] = mapped_column(String(255))  # 故事内时间
    
    # ===== 元数据 =====
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
