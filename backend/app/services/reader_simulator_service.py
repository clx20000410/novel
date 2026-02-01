"""
读者模拟器服务

模拟不同类型读者的阅读体验，提供爽点检测、弃书风险评估、追读欲望分析。
"""
from typing import Optional, Dict, Any, List
from enum import Enum
import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from .llm_service import LLMService
from .prompt_service import PromptService

logger = logging.getLogger(__name__)


class ReaderType(str, Enum):
    """读者类型"""
    CASUAL = "casual"  # 休闲读者：追求轻松愉快
    HARDCORE = "hardcore"  # 硬核读者：追求逻辑严密
    EMOTIONAL = "emotional"  # 情感读者：追求情感共鸣
    THRILL_SEEKER = "thrill_seeker"  # 爽点读者：追求爽感
    CRITIC = "critic"  # 挑剔读者：追求文笔质量


class ReaderSimulatorService:
    """读者模拟器服务"""

    # 读者类型特征
    READER_PROFILES = {
        ReaderType.CASUAL: {
            "name": "休闲读者",
            "description": "下班后想放松一下，不想动脑子",
            "preferences": ["轻松幽默", "节奏明快", "不要太复杂"],
            "dislikes": ["大段描写", "复杂设定", "虐心剧情"],
            "abandon_triggers": ["太无聊", "看不懂", "太压抑"],
            "thrill_sensitivity": 0.6,  # 对爽点的敏感度
            "patience": 0.4,  # 耐心程度
        },
        ReaderType.HARDCORE: {
            "name": "硬核读者",
            "description": "喜欢严密的逻辑和完整的世界观",
            "preferences": ["逻辑自洽", "设定完整", "伏笔回收"],
            "dislikes": ["逻辑漏洞", "降智剧情", "开挂无敌"],
            "abandon_triggers": ["逻辑崩坏", "人设崩塌", "烂尾迹象"],
            "thrill_sensitivity": 0.4,
            "patience": 0.8,
        },
        ReaderType.EMOTIONAL: {
            "name": "情感读者",
            "description": "喜欢有深度的情感描写和角色成长",
            "preferences": ["情感细腻", "角色成长", "关系发展"],
            "dislikes": ["感情线敷衍", "角色工具人", "无情感波动"],
            "abandon_triggers": ["感情线崩", "角色OOC", "太冷血"],
            "thrill_sensitivity": 0.5,
            "patience": 0.7,
        },
        ReaderType.THRILL_SEEKER: {
            "name": "爽点读者",
            "description": "就是来找爽的，要打脸要装逼",
            "preferences": ["打脸", "装逼", "升级", "获得宝物"],
            "dislikes": ["太慢", "太虐", "主角太弱"],
            "abandon_triggers": ["连续三章没爽点", "主角被虐太惨", "节奏太慢"],
            "thrill_sensitivity": 1.0,
            "patience": 0.3,
        },
        ReaderType.CRITIC: {
            "name": "挑剔读者",
            "description": "对文笔和叙事技巧有较高要求",
            "preferences": ["文笔优美", "叙事技巧", "意境深远"],
            "dislikes": ["口水话", "重复啰嗦", "AI味"],
            "abandon_triggers": ["文笔太差", "太多废话", "明显AI生成"],
            "thrill_sensitivity": 0.3,
            "patience": 0.6,
        },
    }

    def __init__(self, db: AsyncSession, llm_service: LLMService, prompt_service: PromptService):
        self.db = db
        self.llm_service = llm_service
        self.prompt_service = prompt_service

    async def simulate_reading_experience(
        self,
        chapter_content: str,
        chapter_number: int,
        reader_types: Optional[List[ReaderType]] = None,
        previous_summary: Optional[str] = None,
        user_id: int = 0
    ) -> Dict[str, Any]:
        """
        模拟阅读体验
        
        Returns:
            包含各类读者反馈的综合报告
        """
        if reader_types is None:
            reader_types = list(ReaderType)
        
        results = {
            "overall_score": 0,
            "reader_feedbacks": {},
            "thrill_points": [],
            "abandon_risks": [],
            "hook_strength": 0,
            "recommendations": []
        }
        
        # 1. 检测爽点
        thrill_points = await self._detect_thrill_points(chapter_content, user_id)
        results["thrill_points"] = thrill_points
        
        # 2. 模拟各类读者反馈
        total_score = 0
        for reader_type in reader_types:
            feedback = await self._simulate_single_reader(
                chapter_content, chapter_number, reader_type, 
                thrill_points, previous_summary, user_id
            )
            results["reader_feedbacks"][reader_type.value] = feedback
            total_score += feedback.get("satisfaction", 50)
        
        results["overall_score"] = round(total_score / len(reader_types), 1)
        
        # 3. 评估弃书风险
        results["abandon_risks"] = self._evaluate_abandon_risks(results["reader_feedbacks"])
        
        # 4. 评估追读欲望（钩子强度）
        results["hook_strength"] = await self._evaluate_hook_strength(chapter_content, user_id)
        
        # 5. 生成综合建议
        results["recommendations"] = self._generate_recommendations(results)
        
        return results

    async def _detect_thrill_points(
        self, 
        chapter_content: str, 
        user_id: int
    ) -> List[Dict[str, Any]]:
        """检测章节中的爽点"""
        prompt = f"""分析以下章节内容，找出所有"爽点"（让读者感到兴奋、满足、痛快的情节点）。

[章节内容]
{chapter_content[:8000]}

爽点类型包括但不限于：
- 打脸：主角或正派打脸反派/小人
- 装逼：主角展现实力或智慧
- 升级：主角获得能力提升
- 获宝：主角获得宝物/资源
- 逆袭：主角从劣势翻盘
- 复仇：主角成功复仇
- 认可：主角获得他人认可/尊重
- 浪漫：感情线的甜蜜时刻
- 揭秘：重要秘密被揭示
- 团聚：重要角色重逢

请以 JSON 格式输出：
```json
{{
  "thrill_points": [
    {{
      "type": "爽点类型",
      "description": "简短描述",
      "intensity": 1-10,
      "position": "章节前部/中部/后部",
      "quote": "原文片段（20字以内）"
    }}
  ]
}}
```"""

        try:
            response = await self.llm_service.get_llm_response(
                system_prompt="你是一个专业的网文分析师，擅长识别读者爽点。请严格按照 JSON 格式输出。",
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
                return result.get("thrill_points", [])
        except Exception as e:
            logger.warning(f"检测爽点失败: {e}")
        
        return []

    async def _simulate_single_reader(
        self,
        chapter_content: str,
        chapter_number: int,
        reader_type: ReaderType,
        thrill_points: List[Dict[str, Any]],
        previous_summary: Optional[str],
        user_id: int
    ) -> Dict[str, Any]:
        """模拟单个类型读者的阅读体验"""
        profile = self.READER_PROFILES[reader_type]
        
        # 计算爽点满足度
        thrill_score = self._calculate_thrill_score(thrill_points, profile["thrill_sensitivity"])
        
        prompt = f"""你现在扮演一个"{profile['name']}"。

[读者画像]
- 描述：{profile['description']}
- 喜欢：{', '.join(profile['preferences'])}
- 讨厌：{', '.join(profile['dislikes'])}
- 弃书触发点：{', '.join(profile['abandon_triggers'])}

[上一章摘要]
{previous_summary or '这是第一章'}

[本章内容]
{chapter_content[:6000]}

[本章爽点数量]
{len(thrill_points)} 个

请以这个读者的视角评价本章，以 JSON 格式输出：
```json
{{
  "satisfaction": 1-100,
  "emotions": ["阅读时的情绪变化"],
  "highlights": ["本章亮点"],
  "complaints": ["本章槽点"],
  "would_continue": true/false,
  "abandon_risk": 1-10,
  "comment": "一句话评价（口语化）"
}}
```"""

        try:
            response = await self.llm_service.get_llm_response(
                system_prompt=f"你是一个{profile['name']}，正在阅读网络小说。请以真实读者的口吻回答。",
                conversation_history=[{"role": "user", "content": prompt}],
                temperature=0.7,
                user_id=user_id,
                timeout=120.0
            )
            
            content = response
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                result = json.loads(content[json_start:json_end])
                result["thrill_score"] = thrill_score
                result["reader_type"] = reader_type.value
                return result
        except Exception as e:
            logger.warning(f"模拟{profile['name']}失败: {e}")
        
        # 返回默认值
        return {
            "satisfaction": 50,
            "emotions": [],
            "highlights": [],
            "complaints": [],
            "would_continue": True,
            "abandon_risk": 5,
            "comment": "无法评价",
            "thrill_score": thrill_score,
            "reader_type": reader_type.value
        }

    def _calculate_thrill_score(
        self, 
        thrill_points: List[Dict[str, Any]], 
        sensitivity: float
    ) -> float:
        """计算爽点得分"""
        if not thrill_points:
            return 0
        
        total_intensity = sum(tp.get("intensity", 5) for tp in thrill_points)
        base_score = min(100, total_intensity * 10)
        
        return round(base_score * sensitivity, 1)

    def _evaluate_abandon_risks(
        self, 
        reader_feedbacks: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """评估弃书风险"""
        risks = []
        
        for reader_type, feedback in reader_feedbacks.items():
            abandon_risk = feedback.get("abandon_risk", 5)
            if abandon_risk >= 7:
                profile = self.READER_PROFILES.get(ReaderType(reader_type), {})
                risks.append({
                    "reader_type": reader_type,
                    "risk_level": abandon_risk,
                    "triggers": profile.get("abandon_triggers", []),
                    "complaints": feedback.get("complaints", [])
                })
        
        return sorted(risks, key=lambda x: x["risk_level"], reverse=True)

    async def _evaluate_hook_strength(
        self, 
        chapter_content: str, 
        user_id: int
    ) -> Dict[str, Any]:
        """评估章节结尾的钩子强度"""
        # 提取章节结尾（最后 500 字）
        ending = chapter_content[-500:] if len(chapter_content) > 500 else chapter_content
        
        prompt = f"""分析以下章节结尾的"钩子"强度（让读者想继续看下一章的吸引力）。

[章节结尾]
{ending}

请以 JSON 格式输出：
```json
{{
  "hook_strength": 1-10,
  "hook_type": "悬念/冲突/期待/情感/无",
  "hook_description": "钩子描述",
  "improvement_suggestion": "如何增强钩子"
}}
```"""

        try:
            response = await self.llm_service.get_llm_response(
                system_prompt="你是一个专业的网文编辑，擅长分析章节钩子。",
                conversation_history=[{"role": "user", "content": prompt}],
                temperature=0.3,
                user_id=user_id,
                timeout=60.0
            )
            
            content = response
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(content[json_start:json_end])
        except Exception as e:
            logger.warning(f"评估钩子强度失败: {e}")
        
        return {
            "hook_strength": 5,
            "hook_type": "未知",
            "hook_description": "",
            "improvement_suggestion": ""
        }

    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """生成综合建议"""
        recommendations = []
        
        # 基于整体得分
        overall_score = results.get("overall_score", 50)
        if overall_score < 60:
            recommendations.append("整体满意度偏低，需要重点优化")
        
        # 基于爽点数量
        thrill_count = len(results.get("thrill_points", []))
        if thrill_count == 0:
            recommendations.append("本章缺少爽点，建议增加至少 1-2 个爽点")
        elif thrill_count < 2:
            recommendations.append("爽点数量偏少，可以适当增加")
        
        # 基于弃书风险
        abandon_risks = results.get("abandon_risks", [])
        if abandon_risks:
            high_risk = abandon_risks[0]
            recommendations.append(
                f"警告：{high_risk['reader_type']} 读者弃书风险较高，"
                f"主要槽点：{', '.join(high_risk.get('complaints', [])[:2])}"
            )
        
        # 基于钩子强度
        hook_data = results.get("hook_strength", {})
        if isinstance(hook_data, dict):
            hook_strength = hook_data.get("hook_strength", 5)
            if hook_strength < 6:
                recommendations.append(
                    f"章节结尾钩子较弱（{hook_strength}/10），"
                    f"建议：{hook_data.get('improvement_suggestion', '增加悬念')}"
                )
        
        # 收集各类读者的共同槽点
        all_complaints = []
        for feedback in results.get("reader_feedbacks", {}).values():
            all_complaints.extend(feedback.get("complaints", []))
        
        if all_complaints:
            # 找出出现频率最高的槽点
            from collections import Counter
            common_complaints = Counter(all_complaints).most_common(2)
            for complaint, count in common_complaints:
                if count >= 2:
                    recommendations.append(f"多类读者共同槽点：{complaint}")
        
        return recommendations[:5]  # 最多返回 5 条建议

    async def get_reader_simulation_context(
        self,
        chapter_content: str,
        chapter_number: int,
        user_id: int
    ) -> str:
        """生成读者模拟上下文（用于写作参考）"""
        # 快速模拟（只用爽点读者和挑剔读者）
        results = await self.simulate_reading_experience(
            chapter_content=chapter_content,
            chapter_number=chapter_number,
            reader_types=[ReaderType.THRILL_SEEKER, ReaderType.CRITIC],
            user_id=user_id
        )
        
        lines = [
            "# 读者模拟反馈\n",
            f"## 整体得分：{results['overall_score']}/100",
            "",
            "## 爽点检测",
            f"- 发现 {len(results['thrill_points'])} 个爽点",
        ]
        
        for tp in results["thrill_points"][:3]:
            lines.append(f"  - [{tp.get('type')}] {tp.get('description')} (强度 {tp.get('intensity')}/10)")
        
        lines.append("")
        lines.append("## 读者反馈")
        
        for reader_type, feedback in results["reader_feedbacks"].items():
            lines.append(f"### {reader_type}")
            lines.append(f"- 满意度：{feedback.get('satisfaction')}/100")
            lines.append(f"- 评价：{feedback.get('comment')}")
        
        if results["recommendations"]:
            lines.append("")
            lines.append("## 改进建议")
            for rec in results["recommendations"]:
                lines.append(f"- {rec}")
        
        return "\n".join(lines)
