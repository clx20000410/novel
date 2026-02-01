# AIMETA P=章节蓝图模型_节奏和伏笔元数据|R=章节蓝图表|NR=不含业务逻辑|E=ChapterBlueprint|X=internal|A=ORM模型|D=sqlalchemy|S=none|RD=./README.ai
"""
章节蓝图数据模型

融合自 AI_NovelGenerator 的章节蓝图设计，提供：
- 悬念密度 (suspense_density)
- 伏笔操作 (foreshadowing_ops)
- 认知颠覆等级 (cognitive_twist_level)
- 章节功能 (chapter_function)

这些字段用于指导 L2 Director 生成章节任务，实现"慢节奏 + 跨章起承转合"。
"""
from datetime import datetime
from typing import Optional
import enum

from sqlalchemy import JSON, BigInteger, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base

# 自定义列类型：兼容跨数据库环境
BIGINT_PK_TYPE = BigInteger().with_variant(Integer, "sqlite")
LONG_TEXT_TYPE = Text().with_variant(LONGTEXT, "mysql")


class SuspenseDensity(str, enum.Enum):
    """悬念密度类型"""
    COMPACT = "compact"      # 紧凑 - 高密度悬念，适合高潮章节
    GRADUAL = "gradual"      # 渐进 - 逐步铺垫，适合过渡章节
    EXPLOSIVE = "explosive"  # 爆发 - 集中释放，适合转折章节
    RELAXED = "relaxed"      # 舒缓 - 低密度，适合缓冲章节


class ForeshadowingOp(str, enum.Enum):
    """伏笔操作类型"""
    PLANT = "plant"          # 埋设 - 埋下新伏笔
    REINFORCE = "reinforce"  # 强化 - 加深已有伏笔
    PAYOFF = "payoff"        # 回收 - 揭示伏笔
    NONE = "none"            # 无操作


class ChapterFunction(str, enum.Enum):
    """章节功能类型"""
    PROGRESSION = "progression"  # 推进 - 推动主线发展
    TURNING = "turning"          # 转折 - 剧情转折点
    REVELATION = "revelation"    # 揭示 - 揭示重要信息
    BUILDUP = "buildup"          # 铺垫 - 为后续章节铺垫
    CLIMAX = "climax"            # 高潮 - 情节高潮
    RESOLUTION = "resolution"    # 收束 - 解决冲突
    INTERLUDE = "interlude"      # 过渡 - 章节间过渡


class ChapterBlueprint(Base):
    """
    章节蓝图表
    
    存储每章的节奏控制元数据，用于指导章节生成。
    这些字段可以在大纲生成时自动填充，也可以由用户手动调整。
    """
    __tablename__ = "chapter_blueprints"

    id: Mapped[int] = mapped_column(BIGINT_PK_TYPE, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("novel_projects.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    chapter_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    # === 核心节奏控制字段 ===
    
    # 悬念密度：控制本章悬念的分布密度
    suspense_density: Mapped[Optional[str]] = mapped_column(
        String(32), 
        default=SuspenseDensity.GRADUAL.value
    )
    
    # 伏笔操作：本章对伏笔的操作类型
    # 支持多个操作，用逗号分隔，如 "plant,reinforce"
    foreshadowing_ops: Mapped[Optional[str]] = mapped_column(String(128))
    
    # 认知颠覆等级：1-5级，控制本章的反转强度
    cognitive_twist_level: Mapped[int] = mapped_column(Integer, default=1)
    
    # 章节功能：本章在整体叙事中的作用
    chapter_function: Mapped[Optional[str]] = mapped_column(
        String(32),
        default=ChapterFunction.PROGRESSION.value
    )
    
    # === 扩展节奏控制字段 ===
    
    # 章节定位：角色/事件/主题等
    chapter_focus: Mapped[Optional[str]] = mapped_column(String(255))
    
    # 核心悬念类型：信息差/道德困境/时间压力等
    suspense_type: Mapped[Optional[str]] = mapped_column(String(128))
    
    # 情感基调迁移：如 "怀疑→恐惧→决绝"
    emotional_arc: Mapped[Optional[str]] = mapped_column(String(255))
    
    # 涉及的伏笔ID列表（JSON数组）
    involved_foreshadowings: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    
    # 本章任务约束（JSON格式）
    # 结构: {
    #   "must_include": ["场景A", "对话B"],
    #   "must_not_include": ["提前揭示X"],
    #   "word_budget": {"min": 2000, "max": 4000},
    #   "pov_character": "主角名"
    # }
    mission_constraints: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    # === 生成指导字段 ===
    
    # 本章简述（一句话概括）
    brief_summary: Mapped[Optional[str]] = mapped_column(Text)
    
    # 详细导演脚本（可选，由 L2 Director 生成）
    director_script: Mapped[Optional[str]] = mapped_column(LONG_TEXT_TYPE)
    
    # 节拍表（JSON格式，详细的场景节拍）
    beat_sheet: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # === 状态追踪 ===
    
    # 是否已生成章节
    is_generated: Mapped[bool] = mapped_column(default=False)
    
    # 是否已定稿
    is_finalized: Mapped[bool] = mapped_column(default=False)
    
    # 生成质量评分（0-100）
    quality_score: Mapped[Optional[float]] = mapped_column(Float)
    
    # 元数据
    extra: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class BlueprintTemplate(Base):
    """
    蓝图模板表
    
    存储预设的章节蓝图模板，用于快速应用到新章节。
    例如："高潮章节模板"、"过渡章节模板"等。
    """
    __tablename__ = "blueprint_templates"

    id: Mapped[int] = mapped_column(BIGINT_PK_TYPE, primary_key=True, autoincrement=True)
    
    # 模板名称
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    
    # 模板描述
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # 模板类型：system（系统预设）/ user（用户自定义）
    template_type: Mapped[str] = mapped_column(String(32), default="system")
    
    # 所属用户（用户自定义模板）
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    
    # 模板配置（JSON格式）
    config: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # 使用次数
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
