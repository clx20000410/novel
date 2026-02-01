# AIMETA P=章节扩写服务_字数不足自动扩写|R=字数检测_扩写生成|NR=不含生成逻辑|E=EnrichmentService|X=internal|A=扩写_字数控制|D=llm_service|S=none|RD=./README.ai
"""
章节扩写服务 (EnrichmentService)

融合自 AI_NovelGenerator 的 enrich_chapter_text 设计，提供：
1. 字数检测：检查是否低于目标字数的70%
2. 智能扩写：加戏不加线（只扩写感官、对话潜台词、余波Sequel，不推进主线）
3. 质量控制：确保扩写后的内容与原文风格一致

这对起点风格的网文很实用，可以稳定保持每章2k~4k字。
"""
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from sqlalchemy.orm import Session

from .llm_service import LLMService

logger = logging.getLogger(__name__)


@dataclass
class EnrichmentResult:
    """扩写结果"""
    original_word_count: int
    enriched_word_count: int
    enriched_content: str
    enrichment_ratio: float  # 扩写比例
    enrichment_type: str  # detail/dialogue/sequel


# ==================== 提示词模板 ====================

ENRICH_CHAPTER_PROMPT = """\
以下章节文本较短，请在保持剧情连贯的前提下进行扩写，使其更充实。

## 原始内容：
{chapter_text}

## 目标字数：{target_word_count}字（当前约{current_word_count}字）

## 扩写原则（重要！）：
1. **加戏不加线**：只扩写细节，不推进主线剧情
2. **可扩写内容**：
   - 感官描写（视觉、听觉、触觉、嗅觉、味觉）
   - 对话潜台词（人物内心活动、言外之意）
   - 余波Sequel（事件发生后的情绪反应、思考）
   - 环境氛围（场景细节、天气、光影）
   - 动作细节（肢体语言、微表情）
3. **禁止内容**：
   - 不要引入新的剧情转折
   - 不要添加新的重要角色
   - 不要改变已有的人物关系
   - 不要提前揭示任何伏笔

## 扩写技巧：
- 在对话之间插入人物的内心活动
- 在场景转换时增加环境描写
- 在紧张时刻放慢节奏，增加感官细节
- 在情感高潮后增加余波反应

## 风格要求：
- 保持原文的叙事视角
- 保持原文的语言风格
- 保持原文的节奏感

请返回扩写后的完整章节内容，不要解释修改内容。
"""

ENRICH_DIALOGUE_PROMPT = """\
请扩写以下对话场景，增加人物的内心活动和潜台词：

## 原始对话：
{dialogue_text}

## 人物信息：
{character_info}

## 扩写要求：
1. 在对话之间插入说话者的内心活动
2. 描写人物的微表情和肢体语言
3. 增加对话的言外之意和潜台词
4. 保持对话的原有含义不变

请返回扩写后的对话内容。
"""

ENRICH_SCENE_PROMPT = """\
请扩写以下场景描写，增加感官细节和氛围：

## 原始场景：
{scene_text}

## 场景信息：
- 地点：{location}
- 时间：{time}
- 氛围：{atmosphere}

## 扩写要求：
1. 增加视觉细节（光影、色彩、形状）
2. 增加听觉细节（声音、静默、回响）
3. 增加触觉/嗅觉细节（温度、气味、质感）
4. 通过环境细节暗示人物情绪

请返回扩写后的场景描写。
"""


class EnrichmentService:
    """
    章节扩写服务
    
    负责检测字数不足并进行智能扩写。
    """
    
    def __init__(
        self,
        db: Session,
        llm_service: LLMService
    ):
        self.db = db
        self.llm_service = llm_service
    
    async def check_and_enrich(
        self,
        chapter_text: str,
        target_word_count: int,
        user_id: int,
        threshold: float = 0.7
    ) -> Optional[EnrichmentResult]:
        """
        检查字数并在需要时进行扩写
        
        Args:
            chapter_text: 章节内容
            target_word_count: 目标字数
            user_id: 用户ID
            threshold: 触发扩写的阈值（默认70%）
            
        Returns:
            如果进行了扩写返回EnrichmentResult，否则返回None
        """
        current_count = self._count_words(chapter_text)
        
        # 检查是否需要扩写
        if current_count >= target_word_count * threshold:
            logger.info(f"字数充足 ({current_count}/{target_word_count})，无需扩写")
            return None
        
        logger.info(f"字数不足 ({current_count}/{target_word_count})，开始扩写")
        
        # 执行扩写
        enriched = await self._enrich_chapter(
            chapter_text=chapter_text,
            target_word_count=target_word_count,
            current_word_count=current_count,
            user_id=user_id
        )
        
        if not enriched:
            return None
        
        enriched_count = self._count_words(enriched)
        
        return EnrichmentResult(
            original_word_count=current_count,
            enriched_word_count=enriched_count,
            enriched_content=enriched,
            enrichment_ratio=enriched_count / current_count if current_count > 0 else 1.0,
            enrichment_type="detail"
        )
    
    async def enrich_to_target(
        self,
        chapter_text: str,
        target_word_count: int,
        user_id: int,
        max_iterations: int = 3
    ) -> str:
        """
        迭代扩写直到达到目标字数
        
        Args:
            chapter_text: 章节内容
            target_word_count: 目标字数
            user_id: 用户ID
            max_iterations: 最大迭代次数
            
        Returns:
            扩写后的内容
        """
        current_text = chapter_text
        
        for i in range(max_iterations):
            current_count = self._count_words(current_text)
            
            if current_count >= target_word_count * 0.9:  # 达到90%即可
                break
            
            logger.info(f"扩写迭代 {i+1}: {current_count}/{target_word_count}")
            
            result = await self.check_and_enrich(
                chapter_text=current_text,
                target_word_count=target_word_count,
                user_id=user_id,
                threshold=0.9  # 使用更高的阈值进行迭代
            )
            
            if result:
                current_text = result.enriched_content
            else:
                break
        
        return current_text
    
    async def enrich_dialogue(
        self,
        dialogue_text: str,
        character_info: str,
        user_id: int
    ) -> Optional[str]:
        """
        扩写对话场景
        
        专门针对对话进行扩写，增加潜台词和内心活动。
        """
        prompt = ENRICH_DIALOGUE_PROMPT.format(
            dialogue_text=dialogue_text,
            character_info=character_info
        )
        
        try:
            response = await self.llm_service.generate(
                prompt=prompt,
                user_id=user_id,
                max_tokens=4000,
                temperature=0.6
            )
            return response.strip() if response else None
        except Exception as e:
            logger.error(f"对话扩写失败: {e}")
            return None
    
    async def enrich_scene(
        self,
        scene_text: str,
        location: str,
        time: str,
        atmosphere: str,
        user_id: int
    ) -> Optional[str]:
        """
        扩写场景描写
        
        专门针对场景进行扩写，增加感官细节。
        """
        prompt = ENRICH_SCENE_PROMPT.format(
            scene_text=scene_text,
            location=location,
            time=time,
            atmosphere=atmosphere
        )
        
        try:
            response = await self.llm_service.generate(
                prompt=prompt,
                user_id=user_id,
                max_tokens=3000,
                temperature=0.6
            )
            return response.strip() if response else None
        except Exception as e:
            logger.error(f"场景扩写失败: {e}")
            return None
    
    async def _enrich_chapter(
        self,
        chapter_text: str,
        target_word_count: int,
        current_word_count: int,
        user_id: int
    ) -> Optional[str]:
        """执行章节扩写"""
        prompt = ENRICH_CHAPTER_PROMPT.format(
            chapter_text=chapter_text,
            target_word_count=target_word_count,
            current_word_count=current_word_count
        )
        
        try:
            response = await self.llm_service.generate(
                prompt=prompt,
                user_id=user_id,
                max_tokens=8000,
                temperature=0.6
            )
            return response.strip() if response else None
        except Exception as e:
            logger.error(f"章节扩写失败: {e}")
            return None
    
    def _count_words(self, text: str) -> int:
        """计算中文字数"""
        import re
        # 移除空白字符
        text = re.sub(r'\s+', '', text)
        # 计算字符数（中文一个字符算一个字）
        return len(text)
    
    def get_enrichment_suggestions(
        self,
        chapter_text: str,
        target_word_count: int
    ) -> Dict[str, Any]:
        """
        获取扩写建议
        
        分析章节内容，给出具体的扩写建议。
        """
        current_count = self._count_words(chapter_text)
        needed = target_word_count - current_count
        
        suggestions = {
            "current_word_count": current_count,
            "target_word_count": target_word_count,
            "needed": max(0, needed),
            "ratio": current_count / target_word_count if target_word_count > 0 else 1.0,
            "recommendations": []
        }
        
        if needed <= 0:
            suggestions["status"] = "sufficient"
            return suggestions
        
        suggestions["status"] = "needs_enrichment"
        
        # 分析内容，给出建议
        if "说" in chapter_text or "道" in chapter_text or '"' in chapter_text:
            suggestions["recommendations"].append({
                "type": "dialogue",
                "description": "检测到对话场景，建议增加人物内心活动和潜台词",
                "estimated_words": min(needed // 2, 500)
            })
        
        # 检测场景描写
        scene_keywords = ["走进", "来到", "站在", "坐在", "看着"]
        if any(kw in chapter_text for kw in scene_keywords):
            suggestions["recommendations"].append({
                "type": "scene",
                "description": "检测到场景转换，建议增加环境细节描写",
                "estimated_words": min(needed // 3, 300)
            })
        
        # 检测动作场景
        action_keywords = ["打", "踢", "跑", "跳", "攻击", "防御"]
        if any(kw in chapter_text for kw in action_keywords):
            suggestions["recommendations"].append({
                "type": "action",
                "description": "检测到动作场景，建议增加动作细节和感官描写",
                "estimated_words": min(needed // 3, 400)
            })
        
        # 通用建议
        suggestions["recommendations"].append({
            "type": "general",
            "description": "建议在情节转折处增加人物的情绪反应和思考",
            "estimated_words": min(needed // 4, 300)
        })
        
        return suggestions
