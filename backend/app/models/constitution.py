"""
小说宪法数据模型

小说宪法是项目级别的创作规则集，定义了：
- 故事基础（主题、类型、核心冲突、价值观）
- 叙事视角（POV 类型、限制规则）
- 目标受众（年龄、阅读水平、内容分级）
- 风格基调（整体基调、现实程度、语言风格）
- 世界观约束（设定类型、魔法/科技系统、禁忌内容）
- 角色约束（允许角色类型、能力上限）
- 剧情约束（允许剧情类型、转折频率、伏笔规则）
- 时空约束（时间跨度、地理范围、时间流动方式）
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base


class NovelConstitution(Base):
    """小说宪法 - 项目级别的创作规则集"""

    __tablename__ = "novel_constitutions"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("novel_projects.id", ondelete="CASCADE"), primary_key=True
    )
    
    # ===== 故事基础 =====
    core_theme: Mapped[Optional[str]] = mapped_column(String(255))  # 核心主题
    genre: Mapped[Optional[str]] = mapped_column(String(128))  # 故事类型
    core_conflict: Mapped[Optional[str]] = mapped_column(String(255))  # 核心冲突类型
    story_direction: Mapped[Optional[str]] = mapped_column(String(255))  # 故事走向
    core_values: Mapped[Optional[str]] = mapped_column(Text)  # 核心价值观
    
    # ===== 叙事视角 =====
    pov_type: Mapped[Optional[str]] = mapped_column(String(64))  # POV 类型（第一人称/第三人称有限/全知等）
    pov_character: Mapped[Optional[str]] = mapped_column(String(255))  # 主视角角色
    pov_restrictions: Mapped[Optional[str]] = mapped_column(Text)  # POV 限制规则
    
    # ===== 目标受众 =====
    target_age_group: Mapped[Optional[str]] = mapped_column(String(64))  # 目标年龄段
    reading_level: Mapped[Optional[str]] = mapped_column(String(64))  # 阅读水平
    violence_rating: Mapped[Optional[str]] = mapped_column(String(64))  # 暴力内容分级
    romance_rating: Mapped[Optional[str]] = mapped_column(String(64))  # 情感/性内容分级
    
    # ===== 风格基调 =====
    overall_tone: Mapped[Optional[str]] = mapped_column(String(128))  # 整体基调
    realism_level: Mapped[Optional[str]] = mapped_column(String(128))  # 现实程度
    language_style: Mapped[Optional[str]] = mapped_column(String(128))  # 语言风格
    
    # ===== 世界观约束 =====
    world_type: Mapped[Optional[str]] = mapped_column(String(128))  # 世界设定类型
    power_system: Mapped[Optional[str]] = mapped_column(Text)  # 力量/魔法系统
    world_rules: Mapped[Optional[dict]] = mapped_column(JSON)  # 世界规则（物理/社会/魔法限制）
    forbidden_content: Mapped[Optional[list]] = mapped_column(JSON)  # 禁忌内容列表
    
    # ===== 角色约束 =====
    allowed_character_types: Mapped[Optional[list]] = mapped_column(JSON)  # 允许的角色类型
    character_power_limits: Mapped[Optional[str]] = mapped_column(Text)  # 角色能力上限
    allowed_relationship_types: Mapped[Optional[list]] = mapped_column(JSON)  # 允许的关系类型
    
    # ===== 剧情约束 =====
    allowed_plot_types: Mapped[Optional[list]] = mapped_column(JSON)  # 允许的剧情类型
    twist_frequency: Mapped[Optional[str]] = mapped_column(String(128))  # 转折频率
    foreshadowing_rules: Mapped[Optional[str]] = mapped_column(Text)  # 伏笔规则
    
    # ===== 时空约束 =====
    time_span: Mapped[Optional[str]] = mapped_column(String(128))  # 时间跨度
    geographical_scope: Mapped[Optional[str]] = mapped_column(String(128))  # 地理范围
    time_flow: Mapped[Optional[str]] = mapped_column(String(128))  # 时间流动方式
    
    # ===== 元数据 =====
    extra: Mapped[Optional[dict]] = mapped_column(JSON)  # 扩展字段
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_prompt_context(self) -> str:
        """将宪法转换为提示词上下文格式"""
        sections = []
        
        # 故事基础
        if any([self.core_theme, self.genre, self.core_conflict, self.story_direction, self.core_values]):
            story_foundation = ["## 故事基础"]
            if self.core_theme:
                story_foundation.append(f"- 核心主题：{self.core_theme}")
            if self.genre:
                story_foundation.append(f"- 故事类型：{self.genre}")
            if self.core_conflict:
                story_foundation.append(f"- 核心冲突：{self.core_conflict}")
            if self.story_direction:
                story_foundation.append(f"- 故事走向：{self.story_direction}")
            if self.core_values:
                story_foundation.append(f"- 核心价值观：{self.core_values}")
            sections.append("\n".join(story_foundation))
        
        # 叙事视角
        if any([self.pov_type, self.pov_character, self.pov_restrictions]):
            pov_section = ["## 叙事视角"]
            if self.pov_type:
                pov_section.append(f"- POV 类型：{self.pov_type}")
            if self.pov_character:
                pov_section.append(f"- 主视角角色：{self.pov_character}")
            if self.pov_restrictions:
                pov_section.append(f"- POV 限制：{self.pov_restrictions}")
            sections.append("\n".join(pov_section))
        
        # 目标受众
        if any([self.target_age_group, self.reading_level, self.violence_rating, self.romance_rating]):
            audience_section = ["## 目标受众"]
            if self.target_age_group:
                audience_section.append(f"- 目标年龄：{self.target_age_group}")
            if self.reading_level:
                audience_section.append(f"- 阅读水平：{self.reading_level}")
            if self.violence_rating:
                audience_section.append(f"- 暴力分级：{self.violence_rating}")
            if self.romance_rating:
                audience_section.append(f"- 情感分级：{self.romance_rating}")
            sections.append("\n".join(audience_section))
        
        # 风格基调
        if any([self.overall_tone, self.realism_level, self.language_style]):
            style_section = ["## 风格基调"]
            if self.overall_tone:
                style_section.append(f"- 整体基调：{self.overall_tone}")
            if self.realism_level:
                style_section.append(f"- 现实程度：{self.realism_level}")
            if self.language_style:
                style_section.append(f"- 语言风格：{self.language_style}")
            sections.append("\n".join(style_section))
        
        # 世界观约束
        if any([self.world_type, self.power_system, self.world_rules, self.forbidden_content]):
            world_section = ["## 世界观约束"]
            if self.world_type:
                world_section.append(f"- 世界类型：{self.world_type}")
            if self.power_system:
                world_section.append(f"- 力量系统：{self.power_system}")
            if self.world_rules:
                world_section.append(f"- 世界规则：{self.world_rules}")
            if self.forbidden_content:
                world_section.append(f"- 禁忌内容：{', '.join(self.forbidden_content)}")
            sections.append("\n".join(world_section))
        
        # 角色约束
        if any([self.allowed_character_types, self.character_power_limits, self.allowed_relationship_types]):
            char_section = ["## 角色约束"]
            if self.allowed_character_types:
                char_section.append(f"- 允许角色类型：{', '.join(self.allowed_character_types)}")
            if self.character_power_limits:
                char_section.append(f"- 能力上限：{self.character_power_limits}")
            if self.allowed_relationship_types:
                char_section.append(f"- 允许关系类型：{', '.join(self.allowed_relationship_types)}")
            sections.append("\n".join(char_section))
        
        # 剧情约束
        if any([self.allowed_plot_types, self.twist_frequency, self.foreshadowing_rules]):
            plot_section = ["## 剧情约束"]
            if self.allowed_plot_types:
                plot_section.append(f"- 允许剧情类型：{', '.join(self.allowed_plot_types)}")
            if self.twist_frequency:
                plot_section.append(f"- 转折频率：{self.twist_frequency}")
            if self.foreshadowing_rules:
                plot_section.append(f"- 伏笔规则：{self.foreshadowing_rules}")
            sections.append("\n".join(plot_section))
        
        # 时空约束
        if any([self.time_span, self.geographical_scope, self.time_flow]):
            time_section = ["## 时空约束"]
            if self.time_span:
                time_section.append(f"- 时间跨度：{self.time_span}")
            if self.geographical_scope:
                time_section.append(f"- 地理范围：{self.geographical_scope}")
            if self.time_flow:
                time_section.append(f"- 时间流动：{self.time_flow}")
            sections.append("\n".join(time_section))
        
        if not sections:
            return "（未设置小说宪法）"
        
        return "# 小说宪法\n\n" + "\n\n".join(sections)
