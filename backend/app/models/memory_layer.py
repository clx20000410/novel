"""
记忆层数据模型

提供角色状态表、时间线、因果链的数据结构定义。
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, JSON, 
    ForeignKey, DateTime, Boolean, Float, Enum
)
from sqlalchemy.orm import relationship
import enum

from ..db.base import Base


class CharacterStateType(str, enum.Enum):
    """角色状态类型"""
    LOCATION = "location"  # 位置
    EMOTION = "emotion"  # 情绪
    HEALTH = "health"  # 健康状态
    INVENTORY = "inventory"  # 持有物品
    RELATIONSHIP = "relationship"  # 关系变化
    POWER = "power"  # 能力/实力
    KNOWLEDGE = "knowledge"  # 知识/信息
    GOAL = "goal"  # 目标
    SECRET = "secret"  # 秘密


class CharacterState(Base):
    """
    角色状态表
    
    追踪每个角色在每个章节结束时的状态。
    """
    __tablename__ = "character_states"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(String(255), ForeignKey("novel_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    character_id = Column(BigInteger, ForeignKey("blueprint_characters.id", ondelete="CASCADE"), nullable=False, index=True)
    character_name = Column(String(255), nullable=False)  # 冗余存储，方便查询
    
    # 状态快照（章节结束时）
    chapter_number = Column(Integer, nullable=False, index=True)
    
    # 位置状态
    location = Column(String(255))  # 当前位置
    location_detail = Column(Text)  # 位置详情
    
    # 情绪状态
    emotion = Column(String(64))  # 主要情绪
    emotion_intensity = Column(Integer)  # 情绪强度 1-10
    emotion_reason = Column(Text)  # 情绪原因
    
    # 健康状态
    health_status = Column(String(64))  # healthy/injured/critical/dead
    injuries = Column(JSON)  # 受伤列表
    
    # 持有物品
    inventory = Column(JSON)  # 物品列表
    inventory_changes = Column(JSON)  # 本章物品变化
    
    # 关系变化
    relationship_changes = Column(JSON)  # 本章关系变化
    
    # 能力/实力
    power_level = Column(String(64))  # 实力等级
    power_changes = Column(JSON)  # 本章能力变化
    
    # 知识/信息
    known_secrets = Column(JSON)  # 已知秘密
    new_knowledge = Column(JSON)  # 本章新获得的信息
    
    # 目标
    current_goals = Column(JSON)  # 当前目标
    goal_progress = Column(JSON)  # 目标进展
    
    # 元数据
    extra = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TimelineEvent(Base):
    """
    时间线事件
    
    追踪故事内的时间流逝和关键事件。
    """
    __tablename__ = "timeline_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(String(255), ForeignKey("novel_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 时间信息
    chapter_number = Column(Integer, nullable=False, index=True)
    story_time = Column(String(255))  # 故事内时间（如"第三天早上"）
    story_date = Column(String(64))  # 故事内日期（如"2024-01-15"）
    time_elapsed = Column(String(128))  # 距离上一事件的时间
    
    # 事件信息
    event_type = Column(String(64))  # major/minor/background
    event_title = Column(String(255), nullable=False)
    event_description = Column(Text)
    
    # 关联信息
    involved_characters = Column(JSON)  # 涉及角色
    location = Column(String(255))  # 发生地点
    
    # 因果关系
    caused_by_event_id = Column(BigInteger, ForeignKey("timeline_events.id", ondelete="SET NULL"))
    leads_to_event_ids = Column(JSON)  # 导致的后续事件
    
    # 元数据
    importance = Column(Integer, default=5)  # 重要性 1-10
    is_turning_point = Column(Boolean, default=False)  # 是否为转折点
    extra = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class CausalChain(Base):
    """
    因果链
    
    追踪事件之间的因果关系，确保逻辑自洽。
    """
    __tablename__ = "causal_chains"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(String(255), ForeignKey("novel_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 因果关系
    cause_type = Column(String(64))  # event/action/decision/external
    cause_description = Column(Text, nullable=False)
    cause_chapter = Column(Integer, nullable=False)
    
    effect_type = Column(String(64))  # event/state_change/relationship_change
    effect_description = Column(Text, nullable=False)
    effect_chapter = Column(Integer)  # 可能尚未发生
    
    # 关联信息
    involved_characters = Column(JSON)
    cause_event_id = Column(BigInteger, ForeignKey("timeline_events.id", ondelete="SET NULL"))
    effect_event_id = Column(BigInteger, ForeignKey("timeline_events.id", ondelete="SET NULL"))
    
    # 状态
    status = Column(String(32), default="pending")  # pending/resolved/abandoned
    resolution_description = Column(Text)
    
    # 元数据
    importance = Column(Integer, default=5)  # 重要性 1-10
    extra = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StoryTimeTracker(Base):
    """
    故事时间追踪器
    
    追踪整体的故事时间流逝。
    """
    __tablename__ = "story_time_trackers"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(String(255), ForeignKey("novel_projects.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # 时间设定
    time_system = Column(String(64), default="modern")  # modern/ancient/fantasy/scifi
    start_date = Column(String(64))  # 故事开始日期
    current_date = Column(String(64))  # 当前故事日期
    current_time = Column(String(64))  # 当前故事时间
    
    # 时间流速
    default_chapter_duration = Column(String(64), default="1 day")  # 默认每章时间跨度
    
    # 章节时间映射
    chapter_time_map = Column(JSON)  # {chapter_number: {start_time, end_time, duration}}
    
    # 元数据
    extra = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
