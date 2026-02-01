"""
Writer 人格数据模型

Writer 人格定义了写作风格和反 AI 检测特征：
- 身份定位（专业背景、经验年限）
- 目标受众（读者画像）
- 语言特征（句式节奏、词汇偏好、独特表达）
- 人类化特征（口头禅、个人怪癖、不完美表达）
- 反 AI 检测技术（避免的模式、需要的变化）
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, Boolean, func
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base

LONG_TEXT_TYPE = Text().with_variant(LONGTEXT, "mysql")


class WriterPersona(Base):
    """Writer 人格 - 定义写作风格和反 AI 检测特征"""

    __tablename__ = "writer_personas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("novel_projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    # ===== 基础信息 =====
    name: Mapped[str] = mapped_column(String(128), nullable=False)  # Writer 名称
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)  # 是否激活
    
    # ===== 身份定位 =====
    identity: Mapped[Optional[str]] = mapped_column(Text)  # 专业背景描述
    experience_years: Mapped[Optional[int]] = mapped_column(Integer)  # 经验年限
    expertise_areas: Mapped[Optional[list]] = mapped_column(JSON)  # 专长领域
    
    # ===== 目标受众 =====
    target_audience: Mapped[Optional[str]] = mapped_column(Text)  # 读者画像
    
    # ===== 语言特征 =====
    vocabulary_level: Mapped[Optional[str]] = mapped_column(String(64))  # 词汇水平（简单/中等/高级/文学）
    sentence_rhythm: Mapped[Optional[str]] = mapped_column(Text)  # 句式节奏描述
    vocabulary_preferences: Mapped[Optional[list]] = mapped_column(JSON)  # 偏好词汇列表
    unique_expressions: Mapped[Optional[list]] = mapped_column(JSON)  # 独特表达/口头禅
    formality_level: Mapped[Optional[str]] = mapped_column(String(64))  # 正式程度
    
    # ===== 内容结构 =====
    opening_style: Mapped[Optional[str]] = mapped_column(Text)  # 开头风格
    transition_style: Mapped[Optional[str]] = mapped_column(Text)  # 过渡风格
    ending_style: Mapped[Optional[str]] = mapped_column(Text)  # 结尾风格
    
    # ===== 对话风格 =====
    dialogue_style: Mapped[Optional[str]] = mapped_column(Text)  # 对话风格
    dialogue_tags: Mapped[Optional[str]] = mapped_column(Text)  # 对话标签偏好
    
    # ===== 描写风格 =====
    description_style: Mapped[Optional[str]] = mapped_column(Text)  # 描写风格
    show_vs_tell_ratio: Mapped[Optional[str]] = mapped_column(String(64))  # 展示 vs 叙述比例
    sensory_focus: Mapped[Optional[list]] = mapped_column(JSON)  # 感官描写偏好
    
    # ===== 人类化特征（反 AI 检测核心）=====
    catchphrases: Mapped[Optional[list]] = mapped_column(JSON)  # 口头禅列表
    personal_quirks: Mapped[Optional[list]] = mapped_column(JSON)  # 个人怪癖
    imperfection_patterns: Mapped[Optional[list]] = mapped_column(JSON)  # 不完美表达模式
    thinking_pauses: Mapped[Optional[list]] = mapped_column(JSON)  # 思考停顿词
    filler_words: Mapped[Optional[list]] = mapped_column(JSON)  # 填充词
    regional_expressions: Mapped[Optional[list]] = mapped_column(JSON)  # 地域性表达
    
    # ===== 反 AI 检测规则 =====
    avoid_patterns: Mapped[Optional[list]] = mapped_column(JSON)  # 需要避免的 AI 典型模式
    variation_rules: Mapped[Optional[dict]] = mapped_column(JSON)  # 变化规则
    
    # ===== 元数据 =====
    extra: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_prompt_context(self) -> str:
        """将 Writer 人格转换为提示词上下文格式"""
        sections = []
        
        # 身份定位
        if self.identity or self.expertise_areas:
            identity_section = [f"## Writer 身份：{self.name}"]
            if self.identity:
                identity_section.append(f"{self.identity}")
            if self.experience_years:
                identity_section.append(f"- 经验：{self.experience_years} 年")
            if self.expertise_areas:
                identity_section.append(f"- 专长：{', '.join(self.expertise_areas)}")
            sections.append("\n".join(identity_section))
        
        # 语言特征
        lang_items = []
        if self.vocabulary_level:
            lang_items.append(f"- 词汇水平：{self.vocabulary_level}")
        if self.sentence_rhythm:
            lang_items.append(f"- 句式节奏：{self.sentence_rhythm}")
        if self.formality_level:
            lang_items.append(f"- 正式程度：{self.formality_level}")
        if self.vocabulary_preferences:
            lang_items.append(f"- 偏好词汇：{', '.join(self.vocabulary_preferences[:10])}")
        if self.unique_expressions:
            lang_items.append(f"- 独特表达：{', '.join(self.unique_expressions[:5])}")
        if lang_items:
            sections.append("## 语言特征\n" + "\n".join(lang_items))
        
        # 人类化特征（核心）
        human_items = []
        if self.catchphrases:
            human_items.append(f"- 口头禅：{', '.join(self.catchphrases)}")
        if self.personal_quirks:
            human_items.append(f"- 个人怪癖：{', '.join(self.personal_quirks)}")
        if self.thinking_pauses:
            human_items.append(f"- 思考停顿词：{', '.join(self.thinking_pauses)}")
        if self.filler_words:
            human_items.append(f"- 填充词：{', '.join(self.filler_words)}")
        if self.imperfection_patterns:
            human_items.append(f"- 不完美表达：{', '.join(self.imperfection_patterns)}")
        if human_items:
            sections.append("## 人类化特征（必须体现）\n" + "\n".join(human_items))
        
        # 反 AI 检测规则
        if self.avoid_patterns:
            avoid_section = ["## 反 AI 检测规则（严格遵守）"]
            avoid_section.append("**必须避免的 AI 典型模式：**")
            for pattern in self.avoid_patterns:
                avoid_section.append(f"- ❌ {pattern}")
            sections.append("\n".join(avoid_section))
        
        # 对话和描写风格
        style_items = []
        if self.dialogue_style:
            style_items.append(f"- 对话风格：{self.dialogue_style}")
        if self.description_style:
            style_items.append(f"- 描写风格：{self.description_style}")
        if self.show_vs_tell_ratio:
            style_items.append(f"- 展示/叙述比例：{self.show_vs_tell_ratio}")
        if style_items:
            sections.append("## 写作风格\n" + "\n".join(style_items))
        
        if not sections:
            return f"（使用默认 Writer：{self.name}）"
        
        return "\n\n".join(sections)

    @classmethod
    def create_default_qidian_writer(cls, project_id: str) -> "WriterPersona":
        """创建起点中文网风格的默认 Writer"""
        return cls(
            project_id=project_id,
            name="起点爽文写手",
            identity="资深网文作者，擅长都市/玄幻/仙侠类型，深谙起点读者心理",
            experience_years=5,
            expertise_areas=["节奏把控", "爽点设计", "钩子写作", "金手指设定"],
            target_audience="18-35岁男性读者，追求代入感和爽感",
            vocabulary_level="中等偏口语",
            sentence_rhythm="短句为主，长短交错，关键时刻用短促有力的句子",
            vocabulary_preferences=["卧槽", "牛逼", "这波", "稳了", "血赚", "格局"],
            unique_expressions=["这谁顶得住啊", "好家伙", "属实是", "绷不住了"],
            formality_level="口语化",
            opening_style="开门见山，前三段必须有冲突或悬念",
            transition_style="场景切换干脆，不拖泥带水",
            ending_style="必须留钩子，禁止总结性结尾",
            dialogue_style="简洁有力，符合角色身份，适当使用网络用语",
            dialogue_tags="少用'说'，多用动作描写代替",
            description_style="镜头语言，画面感强，少用形容词堆砌",
            show_vs_tell_ratio="7:3 展示为主",
            sensory_focus=["视觉", "听觉", "触觉"],
            catchphrases=["说实话", "不是我说", "懂的都懂", "这波啊"],
            personal_quirks=["喜欢用省略号制造悬念", "关键对话后加一句内心吐槽"],
            imperfection_patterns=[
                "偶尔用不完整的句子表达急促感",
                "对话中适当使用语气词",
                "描写时偶尔打破语法规则增强节奏感"
            ],
            thinking_pauses=["嗯...", "这...", "等等"],
            filler_words=["就是说", "怎么说呢", "反正"],
            regional_expressions=[],
            avoid_patterns=[
                "过度对称的句式结构",
                "机械的过渡词（首先、其次、最后）",
                "刻板的总结性结尾",
                "过度一致的段落长度",
                "缺乏变化的句式",
                "过于完美的语法",
                "AI 典型的「总的来说」「综上所述」",
                "每段都以相似方式开头"
            ],
            variation_rules={
                "sentence_length_variation": "每3-5句变化一次长度",
                "paragraph_length_variation": "段落长度随情节紧张度变化",
                "dialogue_density_variation": "动作戏对话密集，心理戏对话稀疏"
            }
        )
