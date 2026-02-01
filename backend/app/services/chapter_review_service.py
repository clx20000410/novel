"""
章节回顾机制服务

每隔 N 章触发一次回顾，检查整体节奏、角色发展、伏笔状态，生成中期调整建议。
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from .llm_service import LLMService
from .prompt_service import PromptService

logger = logging.getLogger(__name__)


class ChapterReviewService:
    """章节回顾机制服务"""

    # 默认回顾间隔
    DEFAULT_REVIEW_INTERVAL = 5  # 每 5 章回顾一次

    def __init__(self, db: AsyncSession, llm_service: LLMService, prompt_service: PromptService):
        self.db = db
        self.llm_service = llm_service
        self.prompt_service = prompt_service

    def should_trigger_review(
        self,
        chapter_number: int,
        review_interval: int = DEFAULT_REVIEW_INTERVAL,
        last_review_chapter: Optional[int] = None
    ) -> bool:
        """判断是否应该触发回顾"""
        if chapter_number < review_interval:
            return False
        
        if last_review_chapter is None:
            return chapter_number >= review_interval
        
        return chapter_number - last_review_chapter >= review_interval

    async def conduct_periodic_review(
        self,
        project_id: str,
        start_chapter: int,
        end_chapter: int,
        chapter_summaries: List[Dict[str, Any]],
        character_profiles: str,
        foreshadowing_status: Optional[List[Dict[str, Any]]] = None,
        user_id: int = 0
    ) -> Dict[str, Any]:
        """
        执行周期性回顾
        
        Args:
            project_id: 项目 ID
            start_chapter: 回顾起始章节
            end_chapter: 回顾结束章节
            chapter_summaries: 章节摘要列表
            character_profiles: 角色设定
            foreshadowing_status: 伏笔状态列表
        
        Returns:
            包含各维度分析和调整建议的字典
        """
        result = {
            "review_range": f"第 {start_chapter} - {end_chapter} 章",
            "timestamp": datetime.utcnow().isoformat(),
            "pacing_analysis": {},
            "character_analysis": {},
            "foreshadowing_analysis": {},
            "consistency_check": {},
            "recommendations": [],
            "priority_actions": []
        }
        
        # 构建章节摘要文本
        summaries_text = ""
        for summary in chapter_summaries:
            summaries_text += f"\n第 {summary.get('chapter_number', '?')} 章：{summary.get('title', '')}\n"
            summaries_text += f"摘要：{summary.get('summary', '')}\n"
        
        # 1. 节奏分析
        result["pacing_analysis"] = await self._analyze_pacing(
            summaries_text, start_chapter, end_chapter, user_id
        )
        
        # 2. 角色发展分析
        result["character_analysis"] = await self._analyze_character_development(
            summaries_text, character_profiles, user_id
        )
        
        # 3. 伏笔状态分析
        if foreshadowing_status:
            result["foreshadowing_analysis"] = await self._analyze_foreshadowing(
                foreshadowing_status, end_chapter, user_id
            )
        
        # 4. 一致性检查
        result["consistency_check"] = await self._check_consistency(
            summaries_text, character_profiles, user_id
        )
        
        # 5. 生成综合建议
        result["recommendations"] = self._generate_recommendations(result)
        
        # 6. 确定优先行动
        result["priority_actions"] = self._determine_priority_actions(result)
        
        return result

    async def _analyze_pacing(
        self,
        summaries_text: str,
        start_chapter: int,
        end_chapter: int,
        user_id: int
    ) -> Dict[str, Any]:
        """分析节奏"""
        prompt = f"""分析以下章节的整体节奏。

[章节摘要]
{summaries_text[:4000]}

请分析：
1. 情绪起伏是否合理
2. 高潮和低谷分布是否均衡
3. 是否存在连续多章节奏相同的问题
4. 是否存在节奏过快或过慢的问题

以 JSON 格式输出：
```json
{{
  "overall_pacing_score": 1-100,
  "emotion_curve": "上升/下降/平稳/波动",
  "high_points": ["高潮章节"],
  "low_points": ["低谷章节"],
  "issues": [
    {{
      "type": "too_fast/too_slow/monotonous/unbalanced",
      "chapters": [章节号],
      "description": "问题描述"
    }}
  ],
  "suggestions": ["节奏调整建议"]
}}
```"""

        try:
            response = await self.llm_service.get_llm_response(
                system_prompt="你是一位资深网文编辑，擅长分析故事节奏。",
                conversation_history=[{"role": "user", "content": prompt}],
                temperature=0.3,
                user_id=user_id,
                timeout=120.0
            )
            
            content = response
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(content[json_start:json_end])
        except Exception as e:
            logger.warning(f"节奏分析失败: {e}")
        
        return {"overall_pacing_score": 70, "issues": [], "suggestions": []}

    async def _analyze_character_development(
        self,
        summaries_text: str,
        character_profiles: str,
        user_id: int
    ) -> Dict[str, Any]:
        """分析角色发展"""
        prompt = f"""分析以下章节中角色的发展情况。

[角色设定]
{character_profiles[:2000]}

[章节摘要]
{summaries_text[:4000]}

请分析：
1. 主要角色的戏份分布
2. 角色成长是否合理
3. 角色关系发展是否自然
4. 是否有角色被"工具人化"

以 JSON 格式输出：
```json
{{
  "character_screentime": {{
    "角色名": {{
      "appearance_count": 出场章节数,
      "importance": "主角/重要配角/次要配角",
      "development": "成长描述"
    }}
  }},
  "relationship_changes": [
    {{
      "characters": ["角色1", "角色2"],
      "change": "关系变化描述"
    }}
  ],
  "issues": [
    {{
      "character": "角色名",
      "issue_type": "underused/overused/inconsistent/tool_character",
      "description": "问题描述"
    }}
  ],
  "suggestions": ["角色发展建议"]
}}
```"""

        try:
            response = await self.llm_service.get_llm_response(
                system_prompt="你是一位资深网文编辑，擅长分析角色塑造。",
                conversation_history=[{"role": "user", "content": prompt}],
                temperature=0.3,
                user_id=user_id,
                timeout=120.0
            )
            
            content = response
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(content[json_start:json_end])
        except Exception as e:
            logger.warning(f"角色发展分析失败: {e}")
        
        return {"character_screentime": {}, "issues": [], "suggestions": []}

    async def _analyze_foreshadowing(
        self,
        foreshadowing_status: List[Dict[str, Any]],
        current_chapter: int,
        user_id: int
    ) -> Dict[str, Any]:
        """分析伏笔状态"""
        # 统计各状态的伏笔
        planted = []
        developing = []
        overdue = []
        
        for fs in foreshadowing_status:
            status = fs.get("status", "planted")
            planted_chapter = fs.get("planted_chapter", 0)
            planned_reveal = fs.get("planned_reveal_chapter")
            
            if status == "planted":
                planted.append(fs)
                # 检查是否超期
                if planned_reveal and current_chapter > planned_reveal:
                    overdue.append(fs)
            elif status == "developing":
                developing.append(fs)
        
        return {
            "total_active": len(planted) + len(developing),
            "planted_count": len(planted),
            "developing_count": len(developing),
            "overdue_count": len(overdue),
            "overdue_foreshadowings": [
                {
                    "description": fs.get("description", ""),
                    "planted_chapter": fs.get("planted_chapter"),
                    "planned_reveal": fs.get("planned_reveal_chapter"),
                    "overdue_by": current_chapter - fs.get("planned_reveal_chapter", current_chapter)
                }
                for fs in overdue
            ],
            "recommendations": self._generate_foreshadowing_recommendations(
                planted, developing, overdue, current_chapter
            )
        }

    def _generate_foreshadowing_recommendations(
        self,
        planted: List,
        developing: List,
        overdue: List,
        current_chapter: int
    ) -> List[str]:
        """生成伏笔相关建议"""
        recommendations = []
        
        total_active = len(planted) + len(developing)
        
        if total_active > 10:
            recommendations.append(f"活跃伏笔过多（{total_active}个），建议在接下来几章揭示部分伏笔")
        
        if overdue:
            recommendations.append(f"有 {len(overdue)} 个伏笔已超期未揭示，需要尽快处理")
            for fs in overdue[:3]:
                recommendations.append(f"  - 超期伏笔：{fs.get('description', '')[:50]}...")
        
        if total_active < 3:
            recommendations.append("活跃伏笔较少，可以考虑埋设新的伏笔")
        
        return recommendations

    async def _check_consistency(
        self,
        summaries_text: str,
        character_profiles: str,
        user_id: int
    ) -> Dict[str, Any]:
        """检查一致性"""
        prompt = f"""检查以下章节的一致性问题。

[角色设定]
{character_profiles[:1500]}

[章节摘要]
{summaries_text[:4000]}

请检查：
1. 时间线是否自洽
2. 角色行为是否一致
3. 设定是否前后矛盾
4. 是否有遗漏的剧情线

以 JSON 格式输出：
```json
{{
  "consistency_score": 1-100,
  "timeline_issues": ["时间线问题"],
  "character_issues": ["角色一致性问题"],
  "setting_issues": ["设定矛盾"],
  "plot_holes": ["剧情漏洞"],
  "suggestions": ["修复建议"]
}}
```"""

        try:
            response = await self.llm_service.get_llm_response(
                system_prompt="你是一位细心的网文编辑，擅长发现一致性问题。",
                conversation_history=[{"role": "user", "content": prompt}],
                temperature=0.3,
                user_id=user_id,
                timeout=120.0
            )
            
            content = response
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(content[json_start:json_end])
        except Exception as e:
            logger.warning(f"一致性检查失败: {e}")
        
        return {"consistency_score": 80, "timeline_issues": [], "suggestions": []}

    def _generate_recommendations(self, result: Dict[str, Any]) -> List[str]:
        """生成综合建议"""
        recommendations = []
        
        # 节奏建议
        pacing = result.get("pacing_analysis", {})
        if pacing.get("overall_pacing_score", 100) < 70:
            recommendations.extend(pacing.get("suggestions", []))
        
        # 角色建议
        character = result.get("character_analysis", {})
        recommendations.extend(character.get("suggestions", []))
        
        # 伏笔建议
        foreshadowing = result.get("foreshadowing_analysis", {})
        recommendations.extend(foreshadowing.get("recommendations", []))
        
        # 一致性建议
        consistency = result.get("consistency_check", {})
        recommendations.extend(consistency.get("suggestions", []))
        
        return recommendations[:10]  # 最多 10 条建议

    def _determine_priority_actions(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """确定优先行动"""
        actions = []
        
        # 检查超期伏笔
        foreshadowing = result.get("foreshadowing_analysis", {})
        if foreshadowing.get("overdue_count", 0) > 0:
            actions.append({
                "priority": "high",
                "type": "foreshadowing",
                "action": "揭示超期伏笔",
                "details": foreshadowing.get("overdue_foreshadowings", [])[:3]
            })
        
        # 检查一致性问题
        consistency = result.get("consistency_check", {})
        if consistency.get("consistency_score", 100) < 60:
            actions.append({
                "priority": "high",
                "type": "consistency",
                "action": "修复一致性问题",
                "details": consistency.get("plot_holes", [])[:3]
            })
        
        # 检查节奏问题
        pacing = result.get("pacing_analysis", {})
        pacing_issues = pacing.get("issues", [])
        critical_pacing = [i for i in pacing_issues if i.get("type") == "monotonous"]
        if critical_pacing:
            actions.append({
                "priority": "medium",
                "type": "pacing",
                "action": "调整节奏",
                "details": critical_pacing[:2]
            })
        
        # 检查角色问题
        character = result.get("character_analysis", {})
        character_issues = character.get("issues", [])
        tool_characters = [i for i in character_issues if i.get("issue_type") == "tool_character"]
        if tool_characters:
            actions.append({
                "priority": "medium",
                "type": "character",
                "action": "丰富工具人角色",
                "details": tool_characters[:2]
            })
        
        # 按优先级排序
        priority_order = {"high": 0, "medium": 1, "low": 2}
        actions.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 2))
        
        return actions[:5]  # 最多 5 个优先行动

    async def generate_adjustment_plan(
        self,
        review_result: Dict[str, Any],
        upcoming_outlines: List[Dict[str, Any]],
        user_id: int = 0
    ) -> Dict[str, Any]:
        """
        根据回顾结果生成调整计划
        
        Args:
            review_result: 回顾结果
            upcoming_outlines: 接下来几章的大纲
        
        Returns:
            调整计划
        """
        prompt = f"""根据以下回顾结果，为接下来的章节生成调整计划。

[回顾结果]
- 节奏评分：{review_result.get('pacing_analysis', {}).get('overall_pacing_score', 'N/A')}
- 一致性评分：{review_result.get('consistency_check', {}).get('consistency_score', 'N/A')}
- 优先行动：{json.dumps(review_result.get('priority_actions', []), ensure_ascii=False)}
- 综合建议：{json.dumps(review_result.get('recommendations', []), ensure_ascii=False)}

[接下来的大纲]
{json.dumps(upcoming_outlines[:5], ensure_ascii=False, indent=2)}

请生成调整计划，以 JSON 格式输出：
```json
{{
  "chapter_adjustments": [
    {{
      "chapter_number": 章节号,
      "original_focus": "原本的重点",
      "adjusted_focus": "调整后的重点",
      "additions": ["需要添加的元素"],
      "removals": ["需要移除或弱化的元素"]
    }}
  ],
  "global_adjustments": ["全局调整建议"],
  "foreshadowing_plan": {{
    "to_reveal": ["需要揭示的伏笔"],
    "to_develop": ["需要发展的伏笔"],
    "to_plant": ["可以埋设的新伏笔"]
  }},
  "character_focus": {{
    "increase_screentime": ["需要增加戏份的角色"],
    "develop_relationship": ["需要发展的关系"]
  }}
}}
```"""

        try:
            response = await self.llm_service.get_llm_response(
                system_prompt="你是一位资深网文策划，擅长根据反馈调整创作计划。",
                conversation_history=[{"role": "user", "content": prompt}],
                temperature=0.5,
                user_id=user_id,
                timeout=120.0
            )
            
            content = response
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(content[json_start:json_end])
        except Exception as e:
            logger.warning(f"生成调整计划失败: {e}")
        
        return {
            "chapter_adjustments": [],
            "global_adjustments": review_result.get("recommendations", []),
            "foreshadowing_plan": {},
            "character_focus": {}
        }

    def get_review_context(self, review_result: Dict[str, Any]) -> str:
        """生成回顾上下文（用于注入到写作提示词）"""
        lines = [
            "# 周期回顾摘要\n",
            f"## 回顾范围：{review_result.get('review_range', 'N/A')}",
            "",
        ]
        
        # 节奏分析
        pacing = review_result.get("pacing_analysis", {})
        if pacing:
            lines.append(f"## 节奏评分：{pacing.get('overall_pacing_score', 'N/A')}/100")
            if pacing.get("issues"):
                lines.append("### 节奏问题")
                for issue in pacing["issues"][:3]:
                    lines.append(f"- {issue.get('description', '')}")
        
        # 优先行动
        priority_actions = review_result.get("priority_actions", [])
        if priority_actions:
            lines.append("")
            lines.append("## 优先行动")
            for action in priority_actions[:3]:
                lines.append(f"- [{action.get('priority', 'medium')}] {action.get('action', '')}")
        
        # 综合建议
        recommendations = review_result.get("recommendations", [])
        if recommendations:
            lines.append("")
            lines.append("## 综合建议")
            for rec in recommendations[:5]:
                lines.append(f"- {rec}")
        
        return "\n".join(lines)
