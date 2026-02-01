"""
终极写作流程服务

集成所有优化功能的统一写作流程：
- 记忆层架构
- 情绪曲线算法
- 读者模拟器
- 预演-正式两阶段生成
- 自我批评-修正循环
- 章节回顾机制
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from .llm_service import LLMService
from .prompt_service import PromptService
from .memory_layer_service import MemoryLayerService
from .emotion_curve_service import EmotionCurveService, ArcType
from .reader_simulator_service import ReaderSimulatorService, ReaderType
from .preview_generation_service import PreviewGenerationService
from .self_critique_service import SelfCritiqueService, CritiqueDimension
from .chapter_review_service import ChapterReviewService

logger = logging.getLogger(__name__)


class UltimateWritingFlow:
    """终极写作流程服务"""

    def __init__(
        self,
        db: AsyncSession,
        llm_service: LLMService,
        prompt_service: PromptService
    ):
        self.db = db
        self.llm_service = llm_service
        self.prompt_service = prompt_service
        
        # 初始化所有子服务
        self.memory_layer = MemoryLayerService(db, llm_service, prompt_service)
        self.emotion_curve = EmotionCurveService()
        self.reader_simulator = ReaderSimulatorService(db, llm_service, prompt_service)
        self.preview_generator = PreviewGenerationService(db, llm_service, prompt_service)
        self.self_critique = SelfCritiqueService(db, llm_service, prompt_service)
        self.chapter_review = ChapterReviewService(db, llm_service, prompt_service)

    async def generate_chapter_ultimate(
        self,
        project_id: str,
        chapter_number: int,
        total_chapters: int,
        outline: Dict[str, Any],
        blueprint_context: str,
        character_names: List[str],
        character_profiles: str,
        previous_summary: Optional[str] = None,
        arc_type: ArcType = ArcType.STANDARD,
        target_word_count: int = 3000,
        enable_preview: bool = True,
        enable_critique: bool = True,
        enable_reader_simulation: bool = True,
        version_count: int = 1,
        user_id: int = 0
    ) -> Dict[str, Any]:
        """
        终极章节生成流程
        
        Args:
            project_id: 项目 ID
            chapter_number: 章节号
            total_chapters: 总章节数
            outline: 章节大纲
            blueprint_context: 蓝图上下文
            character_names: 角色名列表
            character_profiles: 角色设定
            previous_summary: 前文摘要
            arc_type: 故事弧线类型
            target_word_count: 目标字数
            enable_preview: 是否启用预览阶段
            enable_critique: 是否启用自我批评
            enable_reader_simulation: 是否启用读者模拟
            version_count: 生成版本数
        
        Returns:
            包含生成结果和元数据的字典
        """
        result = {
            "chapter_number": chapter_number,
            "versions": [],
            "best_version_index": 0,
            "metadata": {
                "generation_time": datetime.utcnow().isoformat(),
                "flow_stages": [],
                "emotion_curve": None,
                "memory_context": None,
                "review_triggered": False
            }
        }
        
        try:
            # ===== 阶段 1: 准备上下文 =====
            result["metadata"]["flow_stages"].append("context_preparation")
            
            # 1.1 获取记忆层上下文
            memory_context = await self.memory_layer.get_memory_context(
                project_id, chapter_number, character_names
            )
            result["metadata"]["memory_context"] = memory_context[:500] + "..."
            
            # 1.2 获取情绪曲线指导
            emotion_data = self.emotion_curve.calculate_emotion_target(
                chapter_number, total_chapters, arc_type
            )
            emotion_context = self.emotion_curve.get_emotion_curve_context(
                chapter_number, total_chapters, arc_type
            )
            result["metadata"]["emotion_curve"] = emotion_data
            
            # 1.3 检查是否需要触发周期回顾
            if self.chapter_review.should_trigger_review(chapter_number):
                result["metadata"]["review_triggered"] = True
                # 这里可以触发回顾，但为了不阻塞生成，可以异步处理
                logger.info(f"章节 {chapter_number} 触发周期回顾")
            
            # ===== 阶段 2: 生成多个版本 =====
            result["metadata"]["flow_stages"].append("version_generation")
            
            style_hints = [
                "情绪更细腻，节奏更慢，多写内心戏和感官描写",
                "冲突更强，节奏更快，多写动作和对话",
                "悬念更重，多埋伏笔，结尾钩子更强",
            ]
            
            for version_index in range(version_count):
                version_result = await self._generate_single_version(
                    project_id=project_id,
                    chapter_number=chapter_number,
                    outline=outline,
                    blueprint_context=blueprint_context,
                    memory_context=memory_context,
                    emotion_context=emotion_context,
                    character_profiles=character_profiles,
                    previous_summary=previous_summary,
                    target_word_count=target_word_count,
                    style_hint=style_hints[version_index % len(style_hints)] if version_count > 1 else "",
                    enable_preview=enable_preview,
                    enable_critique=enable_critique,
                    user_id=user_id
                )
                
                version_result["version_index"] = version_index
                result["versions"].append(version_result)
            
            # ===== 阶段 3: 读者模拟评估 =====
            if enable_reader_simulation and result["versions"]:
                result["metadata"]["flow_stages"].append("reader_simulation")
                
                for version in result["versions"]:
                    if version.get("content"):
                        reader_feedback = await self.reader_simulator.simulate_reading_experience(
                            chapter_content=version["content"],
                            chapter_number=chapter_number,
                            reader_types=[ReaderType.THRILL_SEEKER, ReaderType.CRITIC, ReaderType.CASUAL],
                            previous_summary=previous_summary,
                            user_id=user_id
                        )
                        version["reader_feedback"] = reader_feedback
            
            # ===== 阶段 4: 选择最佳版本 =====
            result["metadata"]["flow_stages"].append("version_selection")
            result["best_version_index"] = self._select_best_version(result["versions"])
            
            # ===== 阶段 5: 更新记忆层 =====
            result["metadata"]["flow_stages"].append("memory_update")
            
            best_version = result["versions"][result["best_version_index"]]
            if best_version.get("content"):
                memory_update = await self.memory_layer.update_memory_after_chapter(
                    project_id=project_id,
                    chapter_number=chapter_number,
                    chapter_content=best_version["content"],
                    character_names=character_names,
                    user_id=user_id
                )
                result["metadata"]["memory_update"] = memory_update
            
            result["status"] = "success"
            
        except Exception as e:
            logger.error(f"终极写作流程失败: {e}")
            result["status"] = "failed"
            result["error"] = str(e)
        
        return result

    async def _generate_single_version(
        self,
        project_id: str,
        chapter_number: int,
        outline: Dict[str, Any],
        blueprint_context: str,
        memory_context: str,
        emotion_context: str,
        character_profiles: str,
        previous_summary: Optional[str],
        target_word_count: int,
        style_hint: str,
        enable_preview: bool,
        enable_critique: bool,
        user_id: int
    ) -> Dict[str, Any]:
        """生成单个版本"""
        version_result = {
            "content": "",
            "preview": None,
            "critique": None,
            "final_score": 0,
            "stages_completed": []
        }
        
        context = {
            "character_profiles": character_profiles,
            "previous_summary": previous_summary,
            "emotion_target": emotion_context
        }
        
        if enable_preview:
            # 使用预览-正式两阶段生成
            preview_result = await self.preview_generator.generate_with_preview(
                project_id=project_id,
                chapter_number=chapter_number,
                outline=outline,
                blueprint_context=blueprint_context,
                emotion_context=emotion_context,
                memory_context=memory_context,
                target_word_count=target_word_count,
                style_hint=style_hint,
                auto_approve=True,
                user_id=user_id
            )
            
            version_result["preview"] = preview_result.get("preview")
            version_result["content"] = preview_result.get("full_chapter", "")
            version_result["stages_completed"].append("preview_generation")
        else:
            # 直接生成
            version_result["content"] = await self._direct_generate(
                outline=outline,
                blueprint_context=blueprint_context,
                memory_context=memory_context,
                emotion_context=emotion_context,
                target_word_count=target_word_count,
                style_hint=style_hint,
                user_id=user_id
            )
            version_result["stages_completed"].append("direct_generation")
        
        if enable_critique and version_result["content"]:
            # 执行自我批评-修正循环
            critique_result = await self.self_critique.critique_and_revise_loop(
                chapter_content=version_result["content"],
                max_iterations=2,
                target_score=75.0,
                dimensions=[
                    CritiqueDimension.LOGIC,
                    CritiqueDimension.CHARACTER,
                    CritiqueDimension.WRITING
                ],
                context=context,
                user_id=user_id
            )
            
            version_result["content"] = critique_result.get("final_content", version_result["content"])
            version_result["critique"] = {
                "iterations": len(critique_result.get("iterations", [])),
                "final_score": critique_result.get("final_score", 0),
                "improvement": critique_result.get("improvement", 0),
                "status": critique_result.get("status", "unknown")
            }
            version_result["final_score"] = critique_result.get("final_score", 0)
            version_result["stages_completed"].append("self_critique")
        
        return version_result

    async def _direct_generate(
        self,
        outline: Dict[str, Any],
        blueprint_context: str,
        memory_context: str,
        emotion_context: str,
        target_word_count: int,
        style_hint: str,
        user_id: int
    ) -> str:
        """直接生成章节（不使用预览）"""
        prompt = f"""你是一位资深网文作者，现在需要写一章精彩的小说。

[蓝图上下文]
{blueprint_context[:3000]}

[记忆层上下文]
{memory_context[:2000]}

[情绪曲线指导]
{emotion_context}

[本章大纲]
标题：{outline.get('title', '')}
摘要：{outline.get('summary', '')}

[风格提示]
{style_hint or '无特殊要求'}

[目标字数]
{target_word_count} 字左右

写作要求：
1. 使用镜头语言，多写动作、对话、感官描写
2. 禁止总结性结尾，禁止"他知道..."、"他明白..."等全知视角
3. 禁止使用"值得注意的是"、"总而言之"等 AI 典型词汇
4. 章节结尾必须有钩子，吸引读者继续阅读
5. 严格遵循情绪曲线指导的节奏要求

直接输出章节正文。"""

        try:
            response = await self.llm_service.get_llm_response(
                system_prompt="你是一位资深网文作者，文笔流畅，擅长写出让读者欲罢不能的章节。",
                conversation_history=[{"role": "user", "content": prompt}],
                temperature=0.8,
                user_id=user_id,
                timeout=180.0
            )
            return response.strip()
        except Exception as e:
            logger.error(f"直接生成章节失败: {e}")
            return ""

    def _select_best_version(self, versions: List[Dict[str, Any]]) -> int:
        """选择最佳版本"""
        if not versions:
            return 0
        
        best_index = 0
        best_score = -1
        
        for i, version in enumerate(versions):
            # 综合评分 = 自我批评分数 * 0.4 + 读者模拟分数 * 0.6
            critique_score = version.get("final_score", 0)
            
            reader_feedback = version.get("reader_feedback", {})
            reader_score = reader_feedback.get("overall_score", 50)
            
            # 钩子强度加分
            hook_data = reader_feedback.get("hook_strength", {})
            hook_bonus = 0
            if isinstance(hook_data, dict):
                hook_strength = hook_data.get("hook_strength", 5)
                hook_bonus = (hook_strength - 5) * 2  # 钩子强度每高于 5 分加 2 分
            
            total_score = critique_score * 0.4 + reader_score * 0.6 + hook_bonus
            
            if total_score > best_score:
                best_score = total_score
                best_index = i
        
        return best_index

    async def conduct_periodic_review_if_needed(
        self,
        project_id: str,
        chapter_number: int,
        chapter_summaries: List[Dict[str, Any]],
        character_profiles: str,
        foreshadowing_status: Optional[List[Dict[str, Any]]] = None,
        review_interval: int = 5,
        last_review_chapter: Optional[int] = None,
        user_id: int = 0
    ) -> Optional[Dict[str, Any]]:
        """如果需要，执行周期回顾"""
        if not self.chapter_review.should_trigger_review(
            chapter_number, review_interval, last_review_chapter
        ):
            return None
        
        start_chapter = (last_review_chapter or 0) + 1
        end_chapter = chapter_number
        
        # 过滤相关章节的摘要
        relevant_summaries = [
            s for s in chapter_summaries
            if start_chapter <= s.get("chapter_number", 0) <= end_chapter
        ]
        
        review_result = await self.chapter_review.conduct_periodic_review(
            project_id=project_id,
            start_chapter=start_chapter,
            end_chapter=end_chapter,
            chapter_summaries=relevant_summaries,
            character_profiles=character_profiles,
            foreshadowing_status=foreshadowing_status,
            user_id=user_id
        )
        
        return review_result

    def get_flow_status_summary(self, result: Dict[str, Any]) -> str:
        """生成流程状态摘要"""
        lines = [
            f"# 章节 {result.get('chapter_number', '?')} 生成报告",
            "",
            f"## 状态：{result.get('status', 'unknown')}",
            f"## 生成版本数：{len(result.get('versions', []))}",
            f"## 最佳版本：第 {result.get('best_version_index', 0) + 1} 版",
            "",
            "## 流程阶段",
        ]
        
        stages = result.get("metadata", {}).get("flow_stages", [])
        stage_names = {
            "context_preparation": "上下文准备",
            "version_generation": "版本生成",
            "reader_simulation": "读者模拟",
            "version_selection": "版本选择",
            "memory_update": "记忆更新"
        }
        
        for stage in stages:
            lines.append(f"- ✅ {stage_names.get(stage, stage)}")
        
        # 情绪曲线信息
        emotion_curve = result.get("metadata", {}).get("emotion_curve", {})
        if emotion_curve:
            lines.append("")
            lines.append("## 情绪曲线")
            lines.append(f"- 阶段：{emotion_curve.get('phase_name', 'N/A')}")
            lines.append(f"- 目标强度：{emotion_curve.get('emotion_target', 'N/A')}/100")
        
        # 版本评分
        versions = result.get("versions", [])
        if versions:
            lines.append("")
            lines.append("## 版本评分")
            for i, v in enumerate(versions):
                marker = "⭐" if i == result.get("best_version_index", 0) else "  "
                critique_score = v.get("final_score", 0)
                reader_score = v.get("reader_feedback", {}).get("overall_score", 0)
                lines.append(f"{marker} 版本 {i+1}：批评 {critique_score}/100，读者 {reader_score}/100")
        
        return "\n".join(lines)
