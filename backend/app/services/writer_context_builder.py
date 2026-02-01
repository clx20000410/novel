# AIMETA P=写作上下文构建_信息可见性过滤|R=角色登场检测_蓝图裁剪_已知未知分离|NR=不含LLM调用|E=none|X=internal|A=过滤_构建|D=none|S=none|RD=./README.ai
"""
WriterContextBuilder: 写作层信息可见性过滤服务

核心职责：
1. 检测已登场角色（从已完成章节中提取）
2. 检测本章计划登场的新角色（从大纲/导演脚本中提取）
3. 裁剪蓝图信息，移除剧透字段和未登场角色
4. 输出 Writer 可见的上下文，防止主角全知问题
"""

import re
from copy import deepcopy
from typing import Dict, List, Optional, Set


def _detect_names(all_names: List[str], texts: List[str]) -> Set[str]:
    """
    从文本列表中检测出现过的角色名。
    使用简单的字符串匹配，后续可升级为 NER。
    """
    found = set()
    combined_text = "\n".join(t for t in texts if t)
    for name in all_names:
        if name and name in combined_text:
            found.add(name)
    return found


def _shallow_copy_blueprint(blueprint: dict) -> dict:
    """浅拷贝蓝图，避免修改原始数据。"""
    return deepcopy(blueprint)


class WriterContextBuilder:
    """
    构建写作层可见的上下文，实现信息可见性过滤。
    
    核心原则：
    - L3 Writer 只能看到「已公开」的信息
    - 未登场角色不能出现在 prompt 中（连名字都不出现）
    - full_synopsis 等剧透字段必须移除
    """

    # 禁止传递给 Writer 的蓝图字段（防剧透）
    FORBIDDEN_BLUEPRINT_KEYS = {
        "full_synopsis",
        "one_sentence_summary",
        "chapter_outline",  # 完整大纲也不能给
        "chapter_summaries",
        "chapter_details",
        "chapter_dialogues",
        "chapter_events",
        "conversation_history",
        "character_timelines",
    }

    def build_visibility_context(
        self,
        blueprint: dict,
        completed_summaries: List[str],
        previous_tail: str,
        outline_title: str,
        outline_summary: str,
        writing_notes: str,
        allowed_new_characters: Optional[List[str]] = None,
    ) -> Dict:
        """
        构建 Writer 可见的上下文。

        Args:
            blueprint: 原始蓝图数据
            completed_summaries: 已完成章节的摘要列表
            previous_tail: 上一章结尾文本
            outline_title: 当前章节标题
            outline_summary: 当前章节摘要
            writing_notes: 写作指令
            allowed_new_characters: 导演脚本指定的本章允许登场的新角色

        Returns:
            包含裁剪后蓝图和角色信息的字典
        """
        # 1. 提取所有角色名
        all_names = [
            c.get("name") for c in blueprint.get("characters", []) if c.get("name")
        ]

        # 2. 检测已登场角色（从已完成章节中）
        introduced = _detect_names(all_names, completed_summaries + [previous_tail])

        # 3. 检测本章计划提及的角色（从大纲/写作指令中）
        planned = _detect_names(
            all_names, [outline_title, outline_summary, writing_notes]
        )

        # 4. 合并允许的角色集合
        allowed = introduced | planned
        if allowed_new_characters:
            allowed.update(allowed_new_characters)

        # 5. 裁剪蓝图
        writer_blueprint = _shallow_copy_blueprint(blueprint)

        # 移除禁止字段
        for key in self.FORBIDDEN_BLUEPRINT_KEYS:
            writer_blueprint.pop(key, None)

        # 裁剪角色列表：只保留允许的角色
        if "characters" in writer_blueprint:
            writer_blueprint["characters"] = [
                c for c in writer_blueprint.get("characters", [])
                if c.get("name") in allowed
            ]

        # 裁剪关系列表：只保留与允许角色相关的关系
        if "relationships" in writer_blueprint:
            rels = writer_blueprint.get("relationships", [])
            writer_blueprint["relationships"] = [
                r for r in rels
                if r.get("from") in allowed and r.get("to") in allowed
            ]

        # 6. 计算禁止角色列表（用于 Guardrails 检查）
        forbidden = set(all_names) - allowed

        return {
            "writer_blueprint": writer_blueprint,
            "introduced_characters": sorted(list(introduced)),
            "planned_characters": sorted(list(planned)),
            "allowed_characters": sorted(list(allowed)),
            "forbidden_characters": sorted(list(forbidden)),
        }

    def get_forbidden_names_pattern(self, forbidden_characters: List[str]) -> Optional[re.Pattern]:
        """
        生成用于检测禁止角色名的正则表达式。
        
        Args:
            forbidden_characters: 禁止出现的角色名列表
            
        Returns:
            编译后的正则表达式，如果列表为空则返回 None
        """
        if not forbidden_characters:
            return None
        # 转义特殊字符并构建正则
        escaped = [re.escape(name) for name in forbidden_characters if name]
        if not escaped:
            return None
        pattern = "|".join(escaped)
        return re.compile(pattern)
