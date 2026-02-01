"""
自我批评-修正循环服务

实现"生成 → 自我批评 → 修正 → 再批评 → 再修正"的迭代优化循环。
"""
from typing import Optional, Dict, Any, List
from enum import Enum
import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from .llm_service import LLMService
from .prompt_service import PromptService

logger = logging.getLogger(__name__)


class CritiqueDimension(str, Enum):
    """批评维度"""
    LOGIC = "logic"  # 逻辑一致性
    CHARACTER = "character"  # 人设一致性
    WRITING = "writing"  # 文笔质量
    PACING = "pacing"  # 节奏控制
    EMOTION = "emotion"  # 情感表达
    DIALOGUE = "dialogue"  # 对话质量


class SelfCritiqueService:
    """自我批评-修正循环服务"""

    # 各维度的批评提示词
    CRITIQUE_PROMPTS = {
        CritiqueDimension.LOGIC: {
            "name": "逻辑一致性",
            "focus": [
                "事件因果是否合理",
                "时间线是否自洽",
                "角色行为动机是否充分",
                "世界观规则是否一致",
                "是否存在前后矛盾"
            ],
            "severity_weight": 1.5  # 逻辑问题权重更高
        },
        CritiqueDimension.CHARACTER: {
            "name": "人设一致性",
            "focus": [
                "角色性格是否一致",
                "角色说话方式是否符合人设",
                "角色决策是否符合其价值观",
                "角色成长是否合理",
                "是否存在 OOC（Out of Character）"
            ],
            "severity_weight": 1.3
        },
        CritiqueDimension.WRITING: {
            "name": "文笔质量",
            "focus": [
                "是否存在 AI 典型词汇（值得注意的是、总而言之等）",
                "是否存在重复啰嗦",
                "是否存在口水话",
                "描写是否生动具体",
                "是否过度使用形容词"
            ],
            "severity_weight": 1.0
        },
        CritiqueDimension.PACING: {
            "name": "节奏控制",
            "focus": [
                "节奏是否符合情绪曲线要求",
                "场景转换是否流畅",
                "是否存在拖沓或过于仓促",
                "高潮和低谷是否分布合理",
                "是否给读者喘息的空间"
            ],
            "severity_weight": 1.0
        },
        CritiqueDimension.EMOTION: {
            "name": "情感表达",
            "focus": [
                "情感是否真实可信",
                "情感变化是否自然",
                "是否过度煽情或过于冷漠",
                "读者是否能产生共鸣",
                "情感高潮是否有足够铺垫"
            ],
            "severity_weight": 0.8
        },
        CritiqueDimension.DIALOGUE: {
            "name": "对话质量",
            "focus": [
                "对话是否自然流畅",
                "是否能区分不同角色的说话风格",
                "是否存在说教或信息灌输",
                "对话是否推动剧情或展现人物",
                "是否存在无意义的对话"
            ],
            "severity_weight": 0.9
        }
    }

    def __init__(self, db: AsyncSession, llm_service: LLMService, prompt_service: PromptService):
        self.db = db
        self.llm_service = llm_service
        self.prompt_service = prompt_service

    async def critique_chapter(
        self,
        chapter_content: str,
        dimension: CritiqueDimension,
        context: Optional[Dict[str, Any]] = None,
        user_id: int = 0
    ) -> Dict[str, Any]:
        """
        对章节进行单维度批评
        
        Args:
            chapter_content: 章节内容
            dimension: 批评维度
            context: 上下文信息（如角色设定、前文摘要等）
        
        Returns:
            包含问题列表和修改建议的字典
        """
        dim_config = self.CRITIQUE_PROMPTS[dimension]
        
        context_str = ""
        if context:
            if context.get("character_profiles"):
                context_str += f"\n[角色设定]\n{context['character_profiles'][:2000]}"
            if context.get("previous_summary"):
                context_str += f"\n[前文摘要]\n{context['previous_summary'][:1000]}"
            if context.get("emotion_target"):
                context_str += f"\n[情绪目标]\n{context['emotion_target']}"
        
        focus_points = "\n".join(f"- {f}" for f in dim_config["focus"])
        
        prompt = f"""你是一位严格的文学编辑，现在需要从"{dim_config['name']}"维度审查以下章节。

[审查重点]
{focus_points}

{context_str}

[章节内容]
{chapter_content[:8000]}

请仔细审查，找出所有问题。以 JSON 格式输出：
```json
{{
  "dimension": "{dimension.value}",
  "overall_score": 1-100,
  "issues": [
    {{
      "severity": "critical/major/minor",
      "location": "问题所在位置（引用原文）",
      "problem": "问题描述",
      "suggestion": "具体修改建议",
      "example": "修改示例（如果适用）"
    }}
  ],
  "strengths": ["做得好的地方"],
  "summary": "一句话总结"
}}
```

注意：
- critical：严重问题，必须修改
- major：较大问题，建议修改
- minor：小问题，可以优化"""

        try:
            response = await self.llm_service.get_llm_response(
                system_prompt=f"你是一位专注于{dim_config['name']}的严格编辑。请客观、具体地指出问题。",
                conversation_history=[{"role": "user", "content": prompt}],
                temperature=0.3,
                user_id=user_id,
                timeout=120.0
            )
            
            content = response
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                result = json.loads(content[json_start:json_end])
                result["weight"] = dim_config["severity_weight"]
                return result
        except Exception as e:
            logger.warning(f"批评维度 {dimension.value} 失败: {e}")
        
        return {
            "dimension": dimension.value,
            "overall_score": 70,
            "issues": [],
            "strengths": [],
            "summary": "无法完成审查",
            "weight": dim_config["severity_weight"]
        }

    async def full_critique(
        self,
        chapter_content: str,
        dimensions: Optional[List[CritiqueDimension]] = None,
        context: Optional[Dict[str, Any]] = None,
        user_id: int = 0
    ) -> Dict[str, Any]:
        """
        对章节进行全维度批评
        
        Returns:
            包含各维度批评结果和综合评分的字典
        """
        if dimensions is None:
            dimensions = list(CritiqueDimension)
        
        results = {
            "dimension_critiques": {},
            "all_issues": [],
            "weighted_score": 0,
            "critical_count": 0,
            "major_count": 0,
            "minor_count": 0,
            "needs_revision": False,
            "priority_fixes": []
        }
        
        total_weight = 0
        weighted_score_sum = 0
        
        for dimension in dimensions:
            critique = await self.critique_chapter(
                chapter_content=chapter_content,
                dimension=dimension,
                context=context,
                user_id=user_id
            )
            
            results["dimension_critiques"][dimension.value] = critique
            
            # 统计问题
            for issue in critique.get("issues", []):
                issue["dimension"] = dimension.value
                results["all_issues"].append(issue)
                
                severity = issue.get("severity", "minor")
                if severity == "critical":
                    results["critical_count"] += 1
                elif severity == "major":
                    results["major_count"] += 1
                else:
                    results["minor_count"] += 1
            
            # 计算加权分数
            weight = critique.get("weight", 1.0)
            score = critique.get("overall_score", 70)
            weighted_score_sum += score * weight
            total_weight += weight
        
        # 计算综合分数
        if total_weight > 0:
            results["weighted_score"] = round(weighted_score_sum / total_weight, 1)
        
        # 判断是否需要修改
        results["needs_revision"] = (
            results["critical_count"] > 0 or 
            results["major_count"] >= 3 or
            results["weighted_score"] < 60
        )
        
        # 确定优先修复的问题
        priority_issues = [
            issue for issue in results["all_issues"]
            if issue.get("severity") in ["critical", "major"]
        ]
        # 按严重程度排序
        priority_issues.sort(
            key=lambda x: 0 if x.get("severity") == "critical" else 1
        )
        results["priority_fixes"] = priority_issues[:5]  # 最多 5 个优先修复
        
        return results

    async def revise_chapter(
        self,
        chapter_content: str,
        issues: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
        user_id: int = 0
    ) -> str:
        """
        根据批评意见修改章节
        
        Args:
            chapter_content: 原章节内容
            issues: 需要修复的问题列表
        
        Returns:
            修改后的章节内容
        """
        if not issues:
            return chapter_content
        
        # 构建问题列表
        issues_text = ""
        for i, issue in enumerate(issues[:10], 1):  # 最多处理 10 个问题
            issues_text += f"""
问题 {i}：
- 维度：{issue.get('dimension', '未知')}
- 严重程度：{issue.get('severity', 'minor')}
- 位置：{issue.get('location', '未知')}
- 问题：{issue.get('problem', '')}
- 建议：{issue.get('suggestion', '')}
- 示例：{issue.get('example', '无')}
"""
        
        context_str = ""
        if context:
            if context.get("character_profiles"):
                context_str += f"\n[角色设定]\n{context['character_profiles'][:1500]}"
        
        prompt = f"""你是一位资深网文作者，现在需要根据编辑的批评意见修改章节。

[编辑批评意见]
{issues_text}

{context_str}

[原章节内容]
{chapter_content}

请根据批评意见修改章节。要求：
1. 必须修复所有 critical 和 major 问题
2. 尽量修复 minor 问题
3. 保持原有的故事走向和情节
4. 保持原有的字数规模
5. 修改要自然融入，不能有明显的修补痕迹

直接输出修改后的完整章节，不要输出其他内容。"""

        try:
            response = await self.llm_service.get_llm_response(
                system_prompt="你是一位资深网文作者，擅长根据编辑意见修改文章。",
                conversation_history=[{"role": "user", "content": prompt}],
                temperature=0.7,
                user_id=user_id,
                timeout=180.0
            )
            
            return response.strip()
        except Exception as e:
            logger.error(f"修改章节失败: {e}")
            return chapter_content

    async def critique_and_revise_loop(
        self,
        chapter_content: str,
        max_iterations: int = 3,
        target_score: float = 75.0,
        dimensions: Optional[List[CritiqueDimension]] = None,
        context: Optional[Dict[str, Any]] = None,
        user_id: int = 0
    ) -> Dict[str, Any]:
        """
        执行完整的批评-修正循环
        
        Args:
            chapter_content: 初始章节内容
            max_iterations: 最大迭代次数
            target_score: 目标分数（达到后停止迭代）
            dimensions: 批评维度
            context: 上下文信息
        
        Returns:
            包含最终内容、迭代历史、最终评分的字典
        """
        # 默认使用核心三维度
        if dimensions is None:
            dimensions = [
                CritiqueDimension.LOGIC,
                CritiqueDimension.CHARACTER,
                CritiqueDimension.WRITING
            ]
        
        result = {
            "original_content": chapter_content,
            "final_content": chapter_content,
            "iterations": [],
            "final_score": 0,
            "improvement": 0,
            "status": "pending"
        }
        
        current_content = chapter_content
        
        for iteration in range(max_iterations):
            iteration_data = {
                "iteration": iteration + 1,
                "critique": None,
                "revised": False,
                "score_before": 0,
                "score_after": 0
            }
            
            # 批评当前版本
            critique = await self.full_critique(
                chapter_content=current_content,
                dimensions=dimensions,
                context=context,
                user_id=user_id
            )
            
            iteration_data["critique"] = {
                "weighted_score": critique["weighted_score"],
                "critical_count": critique["critical_count"],
                "major_count": critique["major_count"],
                "minor_count": critique["minor_count"],
                "needs_revision": critique["needs_revision"]
            }
            iteration_data["score_before"] = critique["weighted_score"]
            
            # 检查是否达到目标
            if critique["weighted_score"] >= target_score and not critique["needs_revision"]:
                iteration_data["score_after"] = critique["weighted_score"]
                result["iterations"].append(iteration_data)
                result["status"] = "target_reached"
                break
            
            # 如果不需要修改，也停止
            if not critique["needs_revision"]:
                iteration_data["score_after"] = critique["weighted_score"]
                result["iterations"].append(iteration_data)
                result["status"] = "acceptable"
                break
            
            # 修改章节
            revised_content = await self.revise_chapter(
                chapter_content=current_content,
                issues=critique["priority_fixes"],
                context=context,
                user_id=user_id
            )
            
            if revised_content and revised_content != current_content:
                iteration_data["revised"] = True
                current_content = revised_content
                
                # 重新评分
                re_critique = await self.full_critique(
                    chapter_content=current_content,
                    dimensions=dimensions,
                    context=context,
                    user_id=user_id
                )
                iteration_data["score_after"] = re_critique["weighted_score"]
            else:
                iteration_data["score_after"] = critique["weighted_score"]
                result["iterations"].append(iteration_data)
                result["status"] = "revision_failed"
                break
            
            result["iterations"].append(iteration_data)
        
        # 设置最终结果
        result["final_content"] = current_content
        
        if result["iterations"]:
            result["final_score"] = result["iterations"][-1]["score_after"]
            initial_score = result["iterations"][0]["score_before"]
            result["improvement"] = round(result["final_score"] - initial_score, 1)
        
        if result["status"] == "pending":
            result["status"] = "max_iterations_reached"
        
        return result

    async def quick_critique(
        self,
        chapter_content: str,
        user_id: int = 0
    ) -> Dict[str, Any]:
        """
        快速批评（只检查最重要的问题）
        
        用于在生成过程中快速评估质量
        """
        prompt = f"""快速审查以下章节，找出最严重的问题。

[章节内容]
{chapter_content[:6000]}

请快速检查：
1. 是否有明显的逻辑漏洞
2. 是否有角色 OOC
3. 是否有 AI 典型词汇
4. 结尾是否有钩子

以 JSON 格式输出：
```json
{{
  "quick_score": 1-100,
  "critical_issues": ["严重问题列表"],
  "ai_words_found": ["发现的 AI 典型词汇"],
  "has_hook": true/false,
  "pass": true/false
}}
```"""

        try:
            response = await self.llm_service.get_llm_response(
                system_prompt="你是一位快速审稿编辑。请简洁地指出关键问题。",
                conversation_history=[{"role": "user", "content": prompt}],
                temperature=0.2,
                user_id=user_id,
                timeout=60.0
            )
            
            content = response
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(content[json_start:json_end])
        except Exception as e:
            logger.warning(f"快速批评失败: {e}")
        
        return {
            "quick_score": 70,
            "critical_issues": [],
            "ai_words_found": [],
            "has_hook": True,
            "pass": True
        }
