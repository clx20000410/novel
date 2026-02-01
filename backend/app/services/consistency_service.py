# AIMETA P=一致性检查服务_剧情逻辑矛盾检测|R=一致性检查_冲突检测_修复建议|NR=不含生成逻辑|E=ConsistencyService|X=internal|A=一致性检查_自动修复|D=llm_service|S=none|RD=./README.ai
"""
一致性检查服务 (ConsistencyService)

融合自 AI_NovelGenerator 的 consistency_checker.py 设计理念，提供：
1. 设定一致性检查（世界观、规则）
2. 角色状态一致性检查（位置、能力、知识）
3. 剧情逻辑一致性检查（因果关系、时间线）
4. 伏笔一致性检查（已埋伏笔的回收状态）

检查结果分为三个等级：
- critical: 严重冲突，需要自动触发重写
- major: 主要问题，生成修订版本供选择
- minor: 轻微问题，仅标注提示
"""
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session

from ..models.project_memory import ProjectMemory
from ..models.novel import NovelBlueprint, Chapter
from ..models.foreshadowing import Foreshadowing
from .llm_service import LLMService

logger = logging.getLogger(__name__)


class ViolationSeverity(str, Enum):
    """冲突严重程度"""
    CRITICAL = "critical"  # 严重：自动触发重写
    MAJOR = "major"        # 主要：生成修订版本
    MINOR = "minor"        # 轻微：仅标注


@dataclass
class ConsistencyViolation:
    """一致性冲突"""
    severity: ViolationSeverity
    category: str  # setting/character/plot/foreshadowing
    description: str
    location: Optional[str] = None  # 冲突位置（段落/句子）
    suggested_fix: Optional[str] = None
    confidence: float = 0.8


@dataclass
class ConsistencyCheckResult:
    """一致性检查结果"""
    is_consistent: bool
    violations: List[ConsistencyViolation]
    summary: str
    check_time_ms: int = 0


# ==================== 提示词模板 ====================

CONSISTENCY_CHECK_PROMPT = """\
请检查下面的小说设定与最新章节是否存在明显冲突或不一致之处。

## 检查维度

### 1. 设定一致性
- 世界观规则是否被违反
- 魔法/科技体系是否自洽
- 地理/时间设定是否正确

### 2. 角色状态一致性
- 角色位置是否合理（不能瞬移）
- 角色能力是否符合设定
- 角色知识是否符合其信息来源
- 角色性格是否一致

### 3. 剧情逻辑一致性
- 因果关系是否合理
- 时间线是否正确
- 事件发展是否符合逻辑

### 4. 伏笔一致性
- 已埋伏笔是否被正确引用
- 伏笔回收是否合理

## 输入信息

### 小说设定：
{novel_setting}

### 角色状态（当前已知）：
{character_state}

### 前文摘要：
{global_summary}

### 已记录的未解决冲突或剧情要点：
{plot_arcs}

### 最新章节内容：
{chapter_text}

## 输出要求

请以JSON格式返回检查结果：
{{
  "is_consistent": true/false,
  "violations": [
    {{
      "severity": "critical/major/minor",
      "category": "setting/character/plot/foreshadowing",
      "description": "冲突描述",
      "location": "冲突位置（引用原文）",
      "suggested_fix": "修复建议",
      "confidence": 0.0-1.0
    }}
  ],
  "summary": "总体评估摘要"
}}

如果没有发现冲突，violations 数组为空，is_consistent 为 true。
仅返回JSON，不要解释任何内容。
"""

GENERATE_FIX_PROMPT = """\
以下章节内容存在一致性问题，请进行修复：

## 原始章节内容：
{chapter_text}

## 发现的问题：
{violations}

## 修复要求：
1. 保持原有的故事走向和情节发展
2. 仅修改与冲突相关的部分
3. 确保修复后的内容与设定一致
4. 保持原有的写作风格和语气

## 参考信息：
- 小说设定：{novel_setting}
- 角色状态：{character_state}
- 前文摘要：{global_summary}

请返回修复后的完整章节内容，不要解释修改内容。
"""


class ConsistencyService:
    """
    一致性检查服务
    
    负责检查章节内容与已有设定、状态的一致性。
    """
    
    def __init__(
        self,
        db: Session,
        llm_service: LLMService
    ):
        self.db = db
        self.llm_service = llm_service
    
    async def check_consistency(
        self,
        project_id: str,
        chapter_text: str,
        user_id: int,
        include_foreshadowing: bool = True
    ) -> ConsistencyCheckResult:
        """
        检查章节一致性
        
        Args:
            project_id: 项目ID
            chapter_text: 章节内容
            user_id: 用户ID
            include_foreshadowing: 是否检查伏笔一致性
            
        Returns:
            ConsistencyCheckResult
        """
        import time
        import json
        
        start_time = time.time()
        
        # 获取检查所需的上下文
        context = await self._get_check_context(project_id, include_foreshadowing)
        
        # 构建检查提示词
        prompt = CONSISTENCY_CHECK_PROMPT.format(
            novel_setting=context.get("novel_setting", "（未设定）"),
            character_state=context.get("character_state", "（未记录）"),
            global_summary=context.get("global_summary", "（无前文摘要）"),
            plot_arcs=context.get("plot_arcs", "（无剧情线记录）"),
            chapter_text=chapter_text
        )
        
        try:
            response = await self.llm_service.generate(
                prompt=prompt,
                user_id=user_id,
                max_tokens=2000,
                temperature=0.2  # 低温度以获得更稳定的判断
            )
            
            # 解析响应
            result = self._parse_check_response(response)
            result.check_time_ms = int((time.time() - start_time) * 1000)
            
            return result
            
        except Exception as e:
            logger.error(f"一致性检查失败: {e}")
            return ConsistencyCheckResult(
                is_consistent=True,  # 检查失败时默认通过
                violations=[],
                summary=f"检查过程出错: {str(e)}",
                check_time_ms=int((time.time() - start_time) * 1000)
            )
    
    async def auto_fix(
        self,
        project_id: str,
        chapter_text: str,
        violations: List[ConsistencyViolation],
        user_id: int
    ) -> Optional[str]:
        """
        自动修复一致性问题
        
        Args:
            project_id: 项目ID
            chapter_text: 原始章节内容
            violations: 发现的冲突列表
            user_id: 用户ID
            
        Returns:
            修复后的章节内容，如果修复失败返回None
        """
        if not violations:
            return chapter_text
        
        # 获取上下文
        context = await self._get_check_context(project_id)
        
        # 格式化冲突信息
        violations_text = "\n".join([
            f"- [{v.severity.value}] {v.category}: {v.description}"
            + (f"\n  位置: {v.location}" if v.location else "")
            + (f"\n  建议: {v.suggested_fix}" if v.suggested_fix else "")
            for v in violations
        ])
        
        prompt = GENERATE_FIX_PROMPT.format(
            chapter_text=chapter_text,
            violations=violations_text,
            novel_setting=context.get("novel_setting", ""),
            character_state=context.get("character_state", ""),
            global_summary=context.get("global_summary", "")
        )
        
        try:
            response = await self.llm_service.generate(
                prompt=prompt,
                user_id=user_id,
                max_tokens=8000,
                temperature=0.5
            )
            return response.strip() if response else None
        except Exception as e:
            logger.error(f"自动修复失败: {e}")
            return None
    
    async def check_and_fix(
        self,
        project_id: str,
        chapter_text: str,
        user_id: int,
        auto_fix_threshold: ViolationSeverity = ViolationSeverity.CRITICAL
    ) -> Dict[str, Any]:
        """
        检查并自动修复一致性问题
        
        Args:
            project_id: 项目ID
            chapter_text: 章节内容
            user_id: 用户ID
            auto_fix_threshold: 自动修复的严重程度阈值
            
        Returns:
            包含检查结果和修复内容的字典
        """
        # 执行检查
        check_result = await self.check_consistency(
            project_id=project_id,
            chapter_text=chapter_text,
            user_id=user_id
        )
        
        result = {
            "check_result": check_result,
            "fixed_content": None,
            "needs_manual_review": False
        }
        
        if check_result.is_consistent:
            return result
        
        # 根据严重程度决定处理方式
        severity_order = [ViolationSeverity.CRITICAL, ViolationSeverity.MAJOR, ViolationSeverity.MINOR]
        threshold_index = severity_order.index(auto_fix_threshold)
        
        violations_to_fix = [
            v for v in check_result.violations
            if severity_order.index(v.severity) <= threshold_index
        ]
        
        if violations_to_fix:
            # 尝试自动修复
            fixed_content = await self.auto_fix(
                project_id=project_id,
                chapter_text=chapter_text,
                violations=violations_to_fix,
                user_id=user_id
            )
            result["fixed_content"] = fixed_content
        
        # 检查是否有需要人工审核的问题
        manual_review_violations = [
            v for v in check_result.violations
            if v.severity == ViolationSeverity.MAJOR and auto_fix_threshold == ViolationSeverity.CRITICAL
        ]
        result["needs_manual_review"] = len(manual_review_violations) > 0
        
        return result
    
    async def _get_check_context(
        self,
        project_id: str,
        include_foreshadowing: bool = True
    ) -> Dict[str, str]:
        """获取检查所需的上下文"""
        context = {}
        
        # 获取小说设定
        blueprint = self.db.query(NovelBlueprint).filter(
            NovelBlueprint.project_id == project_id
        ).first()
        
        if blueprint:
            setting_parts = []
            if blueprint.genre:
                setting_parts.append(f"类型: {blueprint.genre}")
            if blueprint.style:
                setting_parts.append(f"风格: {blueprint.style}")
            if blueprint.world_setting:
                setting_parts.append(f"世界观: {blueprint.world_setting}")
            if blueprint.full_synopsis:
                setting_parts.append(f"故事概要: {blueprint.full_synopsis}")
            context["novel_setting"] = "\n".join(setting_parts)
        
        # 获取项目记忆
        memory = self.db.query(ProjectMemory).filter(
            ProjectMemory.project_id == project_id
        ).first()
        
        if memory:
            context["global_summary"] = memory.global_summary or ""
            if memory.plot_arcs:
                import json
                context["plot_arcs"] = json.dumps(memory.plot_arcs, ensure_ascii=False, indent=2)
        
        # 获取角色状态（简化版）
        from ..models.memory_layer import CharacterState
        states = self.db.query(CharacterState).filter(
            CharacterState.project_id == project_id
        ).order_by(CharacterState.chapter_number.desc()).limit(10).all()
        
        if states:
            state_texts = []
            for s in states:
                if s.extra and "raw_state_text" in s.extra:
                    state_texts.append(s.extra["raw_state_text"])
                    break
            context["character_state"] = "\n".join(state_texts) if state_texts else ""
        
        # 获取未回收伏笔
        if include_foreshadowing:
            foreshadowings = self.db.query(Foreshadowing).filter(
                Foreshadowing.project_id == project_id,
                Foreshadowing.status.in_(["planted", "developing"])
            ).all()
            
            if foreshadowings:
                foreshadowing_texts = [
                    f"- 第{f.chapter_number}章埋设: {f.content[:100]}..."
                    for f in foreshadowings[:10]
                ]
                context["foreshadowings"] = "\n".join(foreshadowing_texts)
        
        return context
    
    def _parse_check_response(self, response: str) -> ConsistencyCheckResult:
        """解析检查响应"""
        import json
        
        try:
            # 清理响应
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            data = json.loads(response)
            
            violations = []
            for v in data.get("violations", []):
                violations.append(ConsistencyViolation(
                    severity=ViolationSeverity(v.get("severity", "minor")),
                    category=v.get("category", "unknown"),
                    description=v.get("description", ""),
                    location=v.get("location"),
                    suggested_fix=v.get("suggested_fix"),
                    confidence=v.get("confidence", 0.8)
                ))
            
            return ConsistencyCheckResult(
                is_consistent=data.get("is_consistent", True),
                violations=violations,
                summary=data.get("summary", "")
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"解析一致性检查响应失败: {e}")
            return ConsistencyCheckResult(
                is_consistent=True,
                violations=[],
                summary="响应解析失败，默认通过"
            )
    
    async def get_violation_statistics(
        self,
        project_id: str,
        chapter_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """
        获取冲突统计信息
        
        用于分析项目的一致性问题分布。
        """
        # 这里可以从历史检查记录中统计
        # 当前简化实现，返回空统计
        return {
            "total_checks": 0,
            "total_violations": 0,
            "by_severity": {
                "critical": 0,
                "major": 0,
                "minor": 0
            },
            "by_category": {
                "setting": 0,
                "character": 0,
                "plot": 0,
                "foreshadowing": 0
            }
        }
