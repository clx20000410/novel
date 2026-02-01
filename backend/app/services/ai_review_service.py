# AIMETA P=AI评审服务_多版本对比选优|R=版本评分_最佳选择_改进建议|NR=不含数据存储|E=none|X=internal|A=评审_对比|D=openai|S=net|RD=./README.ai
"""
AIReviewService: AI 评审服务

核心职责：
1. 对多个生成版本进行对比评审
2. 根据起点中文网爆款标准打分
3. 选出最佳版本并给出改进建议
"""

import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from ..services.llm_service import LLMService
from ..services.prompt_service import PromptService
from ..utils.json_utils import remove_think_tags, unwrap_markdown_json

logger = logging.getLogger(__name__)


@dataclass
class ReviewResult:
    """评审结果"""
    best_version_index: int
    scores: Dict[str, int]  # immersion, pacing, hook, character
    overall_evaluation: str
    critical_flaws: List[str]
    refinement_suggestions: str
    final_recommendation: str
    raw_response: Optional[str] = None


class AIReviewService:
    """
    AI 评审服务 - 金牌编辑模式
    
    使用 editor_review 提示词对多个版本进行对比评审，
    选出最具爆款潜力的版本。
    """

    def __init__(self, llm_service: LLMService, prompt_service: PromptService):
        self.llm_service = llm_service
        self.prompt_service = prompt_service

    async def review_versions(
        self,
        versions: List[str],
        chapter_mission: Optional[dict] = None,
        user_id: int = 0,
    ) -> Optional[ReviewResult]:
        """
        对多个版本进行评审，返回评审结果。

        Args:
            versions: 多个版本的正文内容
            chapter_mission: 章节导演脚本（用于评估是否符合预期）
            user_id: 用户 ID

        Returns:
            ReviewResult: 评审结果，如果失败返回 None
        """
        if not versions:
            logger.warning("没有版本可供评审")
            return None

        if len(versions) == 1:
            logger.info("只有一个版本，跳过对比评审")
            return ReviewResult(
                best_version_index=0,
                scores={"immersion": 0, "pacing": 0, "hook": 0, "character": 0},
                overall_evaluation="单版本，无需对比",
                critical_flaws=[],
                refinement_suggestions="",
                final_recommendation="采用唯一版本",
            )

        # 获取评审提示词
        review_prompt = await self.prompt_service.get_prompt("editor_review")
        if not review_prompt:
            logger.warning("未配置 editor_review 提示词，跳过 AI 评审")
            return None

        # 构建评审输入
        review_input = self._build_review_input(versions, chapter_mission)

        try:
            response = await self.llm_service.get_llm_response(
                system_prompt=review_prompt,
                conversation_history=[{"role": "user", "content": review_input}],
                temperature=0.3,
                user_id=user_id,
                timeout=180.0,
            )
            cleaned = remove_think_tags(response)
            normalized = unwrap_markdown_json(cleaned)
            
            result = self._parse_review_response(normalized)
            result.raw_response = cleaned
            
            logger.info(
                "AI 评审完成: 最佳版本=%s, 综合评分=%.1f",
                result.best_version_index,
                sum(result.scores.values()) / len(result.scores) if result.scores else 0,
            )
            return result
        except Exception as exc:
            logger.exception("AI 评审失败: %s", exc)
            return None

    def _build_review_input(
        self, versions: List[str], chapter_mission: Optional[dict]
    ) -> str:
        """构建评审输入文本"""
        lines = []

        if chapter_mission:
            lines.append("[章节导演脚本]")
            lines.append(json.dumps(chapter_mission, ensure_ascii=False, indent=2))
            lines.append("")

        lines.append("[待评审版本]")
        for i, content in enumerate(versions):
            lines.append(f"--- 版本 {i} ---")
            # 截取前 3000 字，避免超长
            truncated = content[:3000] if len(content) > 3000 else content
            lines.append(truncated)
            if len(content) > 3000:
                lines.append(f"... (已截取前 3000 字，原文共 {len(content)} 字)")
            lines.append("")

        lines.append("[评审要求]")
        lines.append("请按照评审流程，对上述版本进行对比分析，输出 JSON 格式的评审结果。")

        return "\n".join(lines)

    def _parse_review_response(self, response: str) -> ReviewResult:
        """解析评审响应"""
        try:
            data = json.loads(response)
            return ReviewResult(
                best_version_index=data.get("best_version_index", 0),
                scores=data.get("scores", {}),
                overall_evaluation=data.get("overall_evaluation", ""),
                critical_flaws=data.get("critical_flaws", []),
                refinement_suggestions=data.get("refinement_suggestions", ""),
                final_recommendation=data.get("final_recommendation", ""),
            )
        except json.JSONDecodeError:
            logger.warning("评审响应不是有效 JSON，使用默认结果")
            return ReviewResult(
                best_version_index=0,
                scores={},
                overall_evaluation=response[:500] if response else "",
                critical_flaws=[],
                refinement_suggestions="",
                final_recommendation="解析失败，建议人工审核",
            )

    async def auto_select_best_version(
        self,
        versions: List[str],
        chapter_mission: Optional[dict] = None,
        user_id: int = 0,
    ) -> int:
        """
        自动选择最佳版本的索引。

        Args:
            versions: 多个版本的正文内容
            chapter_mission: 章节导演脚本
            user_id: 用户 ID

        Returns:
            最佳版本的索引（从 0 开始）
        """
        result = await self.review_versions(versions, chapter_mission, user_id)
        if result:
            return result.best_version_index
        return 0  # 默认返回第一个版本
