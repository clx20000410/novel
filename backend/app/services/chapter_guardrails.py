# AIMETA P=章节护栏_后置一致性检查|R=禁止角色检测_全知视角检测_登场协议检查|NR=不含LLM调用|E=none|X=internal|A=检测_验证|D=re|S=none|RD=./README.ai
"""
ChapterGuardrails: 章节后置一致性检查服务

核心职责：
1. 检测正文中是否出现禁止角色的名字
2. 检测全知视角的 cue 词
3. 检测新角色登场是否符合协议
4. 输出违规列表，供自动修复使用
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Set


@dataclass
class Violation:
    """违规记录"""
    type: str  # forbidden_name | omniscient_cue | sudden_familiarity
    severity: str  # high | medium | low
    description: str
    position: Optional[int] = None  # 违规位置（字符索引）
    context: Optional[str] = None  # 违规上下文（前后 50 字）


@dataclass
class GuardrailResult:
    """护栏检查结果"""
    passed: bool
    violations: List[Violation] = field(default_factory=list)
    
    def add_violation(self, violation: Violation):
        self.violations.append(violation)
        self.passed = False


class ChapterGuardrails:
    """
    章节护栏检查器。
    
    检查维度：
    A) ForbiddenNameMention：正文出现 forbidden_characters 中任意名字（高优先级）
    B) OmniscientCue：出现全知视角的 cue 词（中优先级）
    C) SuddenFamiliarity：新角色首次出现前 120 字内没有介绍痕迹（中优先级）
    """

    # 全知视角 cue 词列表
    OMNISCIENT_CUES = [
        r"与此同时",
        r"另一边",
        r"此时某地",
        r"殊不知",
        r"他并不知道",
        r"她并不知道",
        r"他们并不知道",
        r"如果他知道",
        r"如果她知道",
        r"在他不知道的地方",
        r"在她不知道的地方",
        r"远在.*的.*正在",
        r"而此刻.*却",
    ]

    # 介绍性词汇（用于检测角色登场是否有介绍）
    INTRO_INDICATORS = [
        r"看见",
        r"看到",
        r"注意到",
        r"发现",
        r"出现",
        r"走来",
        r"走进",
        r"站着",
        r"坐着",
        r"一个.*人",
        r"一位",
        r"陌生",
        r"不认识",
        r"第一次见",
        r"从未见过",
        r"身穿",
        r"穿着",
        r"长相",
        r"面容",
        r"身材",
        r"气质",
    ]

    def __init__(self):
        self._omniscient_pattern = re.compile(
            "|".join(self.OMNISCIENT_CUES), re.IGNORECASE
        )
        self._intro_pattern = re.compile(
            "|".join(self.INTRO_INDICATORS), re.IGNORECASE
        )

    def check(
        self,
        generated_text: str,
        forbidden_characters: List[str],
        allowed_new_characters: Optional[List[str]] = None,
        pov: Optional[str] = None,
    ) -> GuardrailResult:
        """
        执行护栏检查。

        Args:
            generated_text: 生成的章节正文
            forbidden_characters: 禁止出现的角色名列表
            allowed_new_characters: 本章允许登场的新角色列表
            pov: 本章视角角色名

        Returns:
            GuardrailResult: 检查结果
        """
        result = GuardrailResult(passed=True)

        # A) 检测禁止角色名
        self._check_forbidden_names(generated_text, forbidden_characters, result)

        # B) 检测全知视角 cue
        self._check_omniscient_cues(generated_text, result)

        # C) 检测新角色登场协议
        if allowed_new_characters:
            self._check_character_introduction(
                generated_text, allowed_new_characters, result
            )

        return result

    def _check_forbidden_names(
        self, text: str, forbidden_characters: List[str], result: GuardrailResult
    ):
        """检测禁止角色名"""
        for name in forbidden_characters:
            if not name:
                continue
            # 使用正则进行精确匹配（避免部分匹配）
            pattern = re.compile(re.escape(name))
            for match in pattern.finditer(text):
                pos = match.start()
                context = self._extract_context(text, pos)
                result.add_violation(
                    Violation(
                        type="forbidden_name",
                        severity="high",
                        description=f"出现了禁止角色「{name}」的名字",
                        position=pos,
                        context=context,
                    )
                )

    def _check_omniscient_cues(self, text: str, result: GuardrailResult):
        """检测全知视角 cue 词"""
        for match in self._omniscient_pattern.finditer(text):
            pos = match.start()
            cue = match.group()
            context = self._extract_context(text, pos)
            result.add_violation(
                Violation(
                    type="omniscient_cue",
                    severity="medium",
                    description=f"出现全知视角 cue 词「{cue}」",
                    position=pos,
                    context=context,
                )
            )

    def _check_character_introduction(
        self, text: str, new_characters: List[str], result: GuardrailResult
    ):
        """检测新角色登场是否有介绍"""
        for name in new_characters:
            if not name:
                continue
            # 找到角色名首次出现的位置
            pattern = re.compile(re.escape(name))
            match = pattern.search(text)
            if not match:
                continue  # 角色未出现，不算违规

            pos = match.start()
            # 检查前 120 字是否有介绍性词汇
            intro_range = max(0, pos - 120)
            intro_text = text[intro_range:pos]
            
            if not self._intro_pattern.search(intro_text):
                context = self._extract_context(text, pos)
                result.add_violation(
                    Violation(
                        type="sudden_familiarity",
                        severity="medium",
                        description=f"新角色「{name}」首次出现前缺少介绍性描写",
                        position=pos,
                        context=context,
                    )
                )

    def _extract_context(self, text: str, pos: int, window: int = 50) -> str:
        """提取违规位置的上下文"""
        start = max(0, pos - window)
        end = min(len(text), pos + window)
        return f"...{text[start:end]}..."

    def format_violations_for_rewrite(self, result: GuardrailResult) -> str:
        """
        将违规列表格式化为可供 rewrite prompt 使用的文本。
        """
        if result.passed:
            return ""
        
        lines = ["检测到以下违规，需要修复："]
        for i, v in enumerate(result.violations, 1):
            lines.append(f"{i}. [{v.severity.upper()}] {v.description}")
            if v.context:
                lines.append(f"   上下文：{v.context}")
        return "\n".join(lines)
