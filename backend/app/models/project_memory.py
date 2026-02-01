# AIMETA P=项目记忆模型_全局摘要和剧情线追踪|R=项目记忆表|NR=不含业务逻辑|E=ProjectMemory|X=internal|A=ORM模型|D=sqlalchemy|S=none|RD=./README.ai
"""
项目记忆数据模型

提供全局摘要(global_summary)和剧情线(plot_arcs)的持久化存储。
融合自 AI_NovelGenerator 的设计理念，用于：
- 跨章节的长程记忆管理
- 未回收伏笔/主线矛盾追踪
- 一致性检查的数据基础
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base

# 自定义列类型：兼容跨数据库环境
BIGINT_PK_TYPE = BigInteger().with_variant(Integer, "sqlite")
LONG_TEXT_TYPE = Text().with_variant(LONGTEXT, "mysql")


class ProjectMemory(Base):
    """
    项目记忆表
    
    存储项目级别的长程记忆信息，包括：
    - global_summary: 全局摘要，每章定稿后更新，用于提供上下文
    - plot_arcs: 剧情线追踪，记录未回收的伏笔、主线矛盾等
    - story_timeline: 故事时间线摘要
    """
    __tablename__ = "project_memories"

    id: Mapped[int] = mapped_column(BIGINT_PK_TYPE, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("novel_projects.id", ondelete="CASCADE"), 
        nullable=False, 
        unique=True,
        index=True
    )
    
    # 全局摘要 - 每章定稿后更新，控制在2000字以内
    global_summary: Mapped[Optional[str]] = mapped_column(LONG_TEXT_TYPE)
    
    # 剧情线追踪 - JSON格式存储未回收的伏笔、主线矛盾等
    # 结构: {
    #   "unresolved_hooks": [{"id": str, "description": str, "planted_chapter": int, "expected_payoff": int}],
    #   "main_conflicts": [{"id": str, "description": str, "status": str}],
    #   "character_arcs": [{"character": str, "current_stage": str, "next_milestone": str}]
    # }
    plot_arcs: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    # 故事时间线摘要
    story_timeline_summary: Mapped[Optional[str]] = mapped_column(Text)
    
    # 最后更新的章节号
    last_updated_chapter: Mapped[int] = mapped_column(Integer, default=0)
    
    # 版本号，用于乐观锁
    version: Mapped[int] = mapped_column(Integer, default=1)
    
    # 元数据
    extra: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ChapterSnapshot(Base):
    """
    章节快照表
    
    存储每章定稿时的状态快照，用于：
    - 回溯历史状态
    - 一致性检查的基准
    - 版本对比
    """
    __tablename__ = "chapter_snapshots"

    id: Mapped[int] = mapped_column(BIGINT_PK_TYPE, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("novel_projects.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    chapter_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    # 章节定稿时的全局摘要快照
    global_summary_snapshot: Mapped[Optional[str]] = mapped_column(LONG_TEXT_TYPE)
    
    # 章节定稿时的角色状态快照
    character_states_snapshot: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # 章节定稿时的剧情线快照
    plot_arcs_snapshot: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # 章节摘要
    chapter_summary: Mapped[Optional[str]] = mapped_column(Text)
    
    # 章节字数
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # 元数据
    extra: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
