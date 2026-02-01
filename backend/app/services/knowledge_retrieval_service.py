# AIMETA P=知识检索服务_两层RAG检索过滤|R=检索_过滤_注入|NR=不含向量库实现|E=KnowledgeRetrievalService|X=internal|A=检索_过滤_POV裁剪|D=llm_service_vector_store_service|S=none|RD=./README.ai
"""
知识检索服务 (KnowledgeRetrievalService)

融合自 AI_NovelGenerator 的知识检索设计，实现"检索→过滤→注入"的两层RAG：
1. 生成检索关键词 (query generation)
2. 向量检索 topK 相关内容
3. 知识过滤 (冲突检测/价值分级/结构化整理)
4. POV可见性裁剪 (配合有限视角)

这解决了"上下文太长塞不进 prompt"的问题，只注入最相关的过滤后内容。
"""
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from sqlalchemy.orm import Session

from ..models.project_memory import ProjectMemory
from ..models.chapter_blueprint import ChapterBlueprint
from .llm_service import LLMService
from .vector_store_service import VectorStoreService

logger = logging.getLogger(__name__)


@dataclass
class RetrievedKnowledge:
    """检索到的知识片段"""
    content: str
    source: str  # chapter/setting/character/external
    relevance_score: float
    chapter_number: Optional[int] = None


@dataclass
class FilteredContext:
    """过滤后的上下文"""
    plot_fuel: List[str]  # 情节燃料
    character_info: List[str]  # 人物维度
    world_fragments: List[str]  # 世界碎片
    narrative_techniques: List[str]  # 叙事技法
    warnings: List[str]  # 冲突警告
    stats: Optional[Dict[str, Any]] = None


# ==================== 提示词模板 ====================

KNOWLEDGE_QUERY_PROMPT = """\
请基于以下当前写作需求，生成合适的知识库检索关键词：

章节元数据：
- 准备创作：第{chapter_number}章
- 章节主题：{chapter_title}
- 章节定位：{chapter_focus}
- 核心作用：{chapter_function}

写作目标：
- 悬念密度：{suspense_density}
- 伏笔操作：{foreshadowing_ops}
- 认知颠覆等级：{twist_level}

当前摘要：
{brief_summary}

用户指导（可能为空）：
{user_guidance}

生成规则：
1. 关键词组合逻辑：
   - 类型1：[实体]+[属性]（如"量子计算机 故障日志"）
   - 类型2：[事件]+[后果]（如"实验室爆炸 辐射泄漏"）
   - 类型3：[地点]+[特征]（如"地下城 氧气循环系统"）

2. 优先级：
   - 首选用户指导中明确提及的术语
   - 次选当前章节涉及的核心道具/地点
   - 最后补充可能关联的扩展概念

请生成3-5组检索词，按优先级降序排列。
格式：每组用"·"连接2-3个关键词，每组占一行

示例：
科技公司·数据泄露
地下实验室·基因编辑·禁忌实验
"""

KNOWLEDGE_FILTER_PROMPT = """\
对知识库检索内容进行三级过滤：

待过滤内容：
{retrieved_texts}

当前叙事需求：
- 章节号：第{chapter_number}章
- 章节功能：{chapter_function}
- 悬念密度：{suspense_density}
- POV角色：{pov_character}

前文摘要（用于检测重复）：
{global_summary}

过滤流程：

1. 冲突检测：
   - 删除与前文摘要重复度>40%的内容
   - 标记存在世界观矛盾的内容（使用▲前缀）

2. 价值评估：
   - 关键价值点（❗标记）：
     · 提供新的角色关系可能性
     · 包含可转化的隐喻素材
     · 存在至少2个可延伸的细节锚点
   - 次级价值点（·标记）：
     · 补充环境细节
     · 提供技术/流程描述

3. POV可见性过滤：
   - 仅保留POV角色{pov_character}能够知道/感知的信息
   - 移除POV角色不可能知道的秘密或他人内心活动

4. 结构重组：
   按"情节燃料/人物维度/世界碎片/叙事技法"分类

请以JSON格式返回过滤结果：
{{
  "plot_fuel": ["内容1", "内容2"],
  "character_info": ["内容1", "内容2"],
  "world_fragments": ["内容1", "内容2"],
  "narrative_techniques": ["内容1", "内容2"],
  "warnings": ["▲冲突警告1", "▲冲突警告2"]
}}

仅返回JSON，不要解释任何内容。
"""

SUMMARIZE_RECENT_CHAPTERS_PROMPT = """\
作为一名专业的小说编辑，请基于已完成的前几章内容生成当前章节的写作摘要。

前文内容：
{combined_text}

当前章节信息：
第{chapter_number}章《{chapter_title}》：
├── 本章定位：{chapter_focus}
├── 核心作用：{chapter_function}
├── 悬念密度：{suspense_density}
├── 伏笔操作：{foreshadowing_ops}
├── 认知颠覆：{twist_level}
└── 本章简述：{brief_summary}

请完成以下任务：
1. 用最多500字，写一个简洁明了的「当前章节写作摘要」
2. 突出与本章相关的前文要点
3. 标注需要延续的伏笔和人物状态

请按如下格式输出：
当前章节摘要: <这里写当前章节摘要>
"""


class KnowledgeRetrievalService:
    """
    知识检索服务
    
    实现两层RAG：检索→过滤→注入
    """
    
    def __init__(
        self,
        db: Session,
        llm_service: LLMService,
        vector_store_service: Optional[VectorStoreService] = None
    ):
        self.db = db
        self.llm_service = llm_service
        self.vector_store_service = vector_store_service
    
    async def retrieve_and_filter(
        self,
        project_id: str,
        chapter_number: int,
        user_id: int,
        pov_character: Optional[str] = None,
        user_guidance: Optional[str] = None,
        top_k: int = 5
    ) -> FilteredContext:
        """
        检索并过滤知识
        
        Args:
            project_id: 项目ID
            chapter_number: 章节号
            user_id: 用户ID
            pov_character: POV角色（用于可见性过滤）
            user_guidance: 用户指导
            top_k: 检索数量
            
        Returns:
            FilteredContext
        """
        # 1. 获取章节蓝图信息
        blueprint = self._get_chapter_blueprint(project_id, chapter_number)
        
        # 2. 生成检索关键词
        queries = await self._generate_search_queries(
            blueprint=blueprint,
            user_guidance=user_guidance,
            user_id=user_id
        )
        
        # 3. 执行向量检索
        retrieved = await self._retrieve_from_vector_store(
            project_id=project_id,
            queries=queries,
            top_k=top_k,
            user_id=user_id,
        )
        
        # 4. 获取前文摘要
        memory = self.db.query(ProjectMemory).filter(
            ProjectMemory.project_id == project_id
        ).first()
        global_summary = memory.global_summary if memory else ""
        
        # 5. 过滤和结构化
        filtered = await self._filter_knowledge(
            retrieved=retrieved,
            blueprint=blueprint,
            global_summary=global_summary,
            pov_character=pov_character,
            user_id=user_id
        )

        filtered_counts = {
            "plot_fuel": len(filtered.plot_fuel),
            "character_info": len(filtered.character_info),
            "world_fragments": len(filtered.world_fragments),
            "narrative_techniques": len(filtered.narrative_techniques),
            "warnings": len(filtered.warnings),
        }
        hit_chapters = sorted({r.chapter_number for r in retrieved if r.chapter_number})
        filtered.stats = {
            "query_count": len(queries),
            "retrieved_count": len(retrieved),
            "top_k": top_k,
            "hit_chapters": hit_chapters,
            "filtered_counts": filtered_counts,
            "total_filtered": sum(filtered_counts.values()),
            "pov_character": pov_character,
        }

        return filtered
    
    async def get_chapter_context(
        self,
        project_id: str,
        chapter_number: int,
        user_id: int,
        include_recent_chapters: int = 3,
        pov_character: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取章节写作上下文
        
        整合多个来源的信息，为章节生成提供完整上下文。
        """
        context = {}
        
        # 1. 获取项目记忆
        memory = self.db.query(ProjectMemory).filter(
            ProjectMemory.project_id == project_id
        ).first()
        
        if memory:
            context["global_summary"] = memory.global_summary
            context["plot_arcs"] = memory.plot_arcs
        
        # 2. 获取章节蓝图
        blueprint = self._get_chapter_blueprint(project_id, chapter_number)
        if blueprint:
            context["blueprint"] = {
                "chapter_focus": blueprint.chapter_focus,
                "chapter_function": blueprint.chapter_function,
                "suspense_density": blueprint.suspense_density,
                "foreshadowing_ops": blueprint.foreshadowing_ops,
                "twist_level": blueprint.cognitive_twist_level,
                "brief_summary": blueprint.brief_summary,
                "mission_constraints": blueprint.mission_constraints
            }
        
        # 3. 获取前几章内容摘要
        if include_recent_chapters > 0:
            recent_summaries = await self._get_recent_chapter_summaries(
                project_id=project_id,
                current_chapter=chapter_number,
                count=include_recent_chapters
            )
            context["recent_chapters"] = recent_summaries
        
        # 4. 检索相关知识
        if self.vector_store_service:
            filtered = await self.retrieve_and_filter(
                project_id=project_id,
                chapter_number=chapter_number,
                user_id=user_id,
                pov_character=pov_character
            )
            context["filtered_knowledge"] = {
                "plot_fuel": filtered.plot_fuel,
                "character_info": filtered.character_info,
                "world_fragments": filtered.world_fragments,
                "narrative_techniques": filtered.narrative_techniques,
                "warnings": filtered.warnings
            }
        
        # 5. 获取角色状态
        character_state = await self._get_character_state(project_id)
        if character_state:
            context["character_state"] = character_state
        
        return context
    
    async def generate_chapter_summary(
        self,
        project_id: str,
        chapter_number: int,
        user_id: int
    ) -> Optional[str]:
        """
        生成当前章节的写作摘要
        
        基于前文内容和章节蓝图，生成针对性的写作摘要。
        """
        # 获取章节蓝图
        blueprint = self._get_chapter_blueprint(project_id, chapter_number)
        if not blueprint:
            return None
        
        # 获取前几章内容
        recent_chapters = await self._get_recent_chapter_content(
            project_id=project_id,
            current_chapter=chapter_number,
            count=3
        )
        
        combined_text = "\n\n---\n\n".join([
            f"第{ch['number']}章：\n{ch['content'][:2000]}..."
            for ch in recent_chapters
        ])
        
        prompt = SUMMARIZE_RECENT_CHAPTERS_PROMPT.format(
            combined_text=combined_text,
            chapter_number=chapter_number,
            chapter_title=blueprint.brief_summary or f"第{chapter_number}章",
            chapter_focus=blueprint.chapter_focus or "",
            chapter_function=blueprint.chapter_function or "",
            suspense_density=blueprint.suspense_density or "",
            foreshadowing_ops=blueprint.foreshadowing_ops or "",
            twist_level=blueprint.cognitive_twist_level or 1,
            brief_summary=blueprint.brief_summary or ""
        )
        
        try:
            response = await self.llm_service.generate(
                prompt=prompt,
                user_id=user_id,
                max_tokens=1000,
                temperature=0.3
            )
            return response.strip() if response else None
        except Exception as e:
            logger.error(f"生成章节摘要失败: {e}")
            return None
    
    def _get_chapter_blueprint(
        self,
        project_id: str,
        chapter_number: int
    ) -> Optional[ChapterBlueprint]:
        """获取章节蓝图"""
        return self.db.query(ChapterBlueprint).filter(
            ChapterBlueprint.project_id == project_id,
            ChapterBlueprint.chapter_number == chapter_number
        ).first()
    
    async def _generate_search_queries(
        self,
        blueprint: Optional[ChapterBlueprint],
        user_guidance: Optional[str],
        user_id: int
    ) -> List[str]:
        """生成检索关键词"""
        if not blueprint:
            return []
        
        prompt = KNOWLEDGE_QUERY_PROMPT.format(
            chapter_number=blueprint.chapter_number,
            chapter_title=blueprint.brief_summary or "",
            chapter_focus=blueprint.chapter_focus or "",
            chapter_function=blueprint.chapter_function or "",
            suspense_density=blueprint.suspense_density or "",
            foreshadowing_ops=blueprint.foreshadowing_ops or "",
            twist_level=blueprint.cognitive_twist_level or 1,
            brief_summary=blueprint.brief_summary or "",
            user_guidance=user_guidance or ""
        )
        
        try:
            response = await self.llm_service.generate(
                prompt=prompt,
                user_id=user_id,
                max_tokens=500,
                temperature=0.5
            )
            
            if response:
                # 解析关键词
                queries = [
                    line.strip().replace("·", " ")
                    for line in response.strip().split("\n")
                    if line.strip()
                ]
                return queries[:5]
        except Exception as e:
            logger.error(f"生成检索关键词失败: {e}")
        
        return []
    
    async def _retrieve_from_vector_store(
        self,
        project_id: str,
        queries: List[str],
        top_k: int,
        user_id: int,
    ) -> List[RetrievedKnowledge]:
        """从向量库检索"""
        if not self.vector_store_service or not queries:
            return []
        
        retrieved = []
        for query in queries:
            try:
                if hasattr(self.vector_store_service, "search"):
                    results = await self.vector_store_service.search(
                        project_id=project_id,
                        query=query,
                        top_k=top_k
                    )
                else:
                    embedding = await self.llm_service.get_embedding(query, user_id=user_id)
                    if not embedding:
                        continue
                    chunks = await self.vector_store_service.query_chunks(
                        project_id=project_id,
                        embedding=embedding,
                        top_k=top_k,
                    )
                    results = [
                        {
                            "content": chunk.content,
                            "source": "chapter",
                            "chapter_number": chunk.chapter_number,
                            "score": 1.0 - chunk.score,
                        }
                        for chunk in chunks
                    ]
                for r in results:
                    retrieved.append(RetrievedKnowledge(
                        content=r.get("content", ""),
                        source=r.get("source", "unknown"),
                        relevance_score=r.get("score", 0.0),
                        chapter_number=r.get("chapter_number")
                    ))
            except Exception as e:
                logger.error(f"向量检索失败: {e}")
        
        # 去重
        seen = set()
        unique = []
        for r in retrieved:
            if r.content not in seen:
                seen.add(r.content)
                unique.append(r)
        
        return unique
    
    async def _filter_knowledge(
        self,
        retrieved: List[RetrievedKnowledge],
        blueprint: Optional[ChapterBlueprint],
        global_summary: str,
        pov_character: Optional[str],
        user_id: int
    ) -> FilteredContext:
        """过滤知识"""
        if not retrieved:
            return FilteredContext(
                plot_fuel=[],
                character_info=[],
                world_fragments=[],
                narrative_techniques=[],
                warnings=[]
            )
        
        # 格式化检索内容
        retrieved_texts = "\n\n".join([
            f"[来源: {r.source}, 相关度: {r.relevance_score:.2f}]\n{r.content}"
            for r in retrieved[:10]
        ])
        
        prompt = KNOWLEDGE_FILTER_PROMPT.format(
            retrieved_texts=retrieved_texts,
            chapter_number=blueprint.chapter_number if blueprint else 0,
            chapter_function=blueprint.chapter_function if blueprint else "",
            suspense_density=blueprint.suspense_density if blueprint else "",
            pov_character=pov_character or "主角",
            global_summary=global_summary[:2000] if global_summary else ""
        )
        
        try:
            response = await self.llm_service.generate(
                prompt=prompt,
                user_id=user_id,
                max_tokens=2000,
                temperature=0.3
            )
            
            if response:
                import json
                response = response.strip()
                if response.startswith("```"):
                    response = response.split("```")[1]
                    if response.startswith("json"):
                        response = response[4:]
                
                data = json.loads(response)
                return FilteredContext(
                    plot_fuel=data.get("plot_fuel", []),
                    character_info=data.get("character_info", []),
                    world_fragments=data.get("world_fragments", []),
                    narrative_techniques=data.get("narrative_techniques", []),
                    warnings=data.get("warnings", [])
                )
        except Exception as e:
            logger.error(f"过滤知识失败: {e}")
        
        return FilteredContext(
            plot_fuel=[],
            character_info=[],
            world_fragments=[],
            narrative_techniques=[],
            warnings=[]
        )
    
    async def _get_recent_chapter_summaries(
        self,
        project_id: str,
        current_chapter: int,
        count: int
    ) -> List[Dict[str, Any]]:
        """获取前几章摘要"""
        from ..models.project_memory import ChapterSnapshot
        
        snapshots = self.db.query(ChapterSnapshot).filter(
            ChapterSnapshot.project_id == project_id,
            ChapterSnapshot.chapter_number < current_chapter
        ).order_by(ChapterSnapshot.chapter_number.desc()).limit(count).all()
        
        return [
            {
                "chapter_number": s.chapter_number,
                "summary": s.chapter_summary
            }
            for s in reversed(snapshots)
        ]
    
    async def _get_recent_chapter_content(
        self,
        project_id: str,
        current_chapter: int,
        count: int
    ) -> List[Dict[str, Any]]:
        """获取前几章内容"""
        from ..models.novel import Chapter, ChapterVersion
        
        chapters = self.db.query(Chapter).filter(
            Chapter.project_id == project_id,
            Chapter.chapter_number < current_chapter
        ).order_by(Chapter.chapter_number.desc()).limit(count).all()
        
        result = []
        for ch in reversed(chapters):
            content = ""
            if ch.selected_version:
                content = ch.selected_version.content
            elif ch.versions:
                content = ch.versions[-1].content
            
            result.append({
                "number": ch.chapter_number,
                "content": content
            })
        
        return result
    
    async def _get_character_state(self, project_id: str) -> Optional[str]:
        """获取角色状态"""
        from ..models.memory_layer import CharacterState
        
        states = self.db.query(CharacterState).filter(
            CharacterState.project_id == project_id,
            CharacterState.character_name == "__all__"
        ).order_by(CharacterState.chapter_number.desc()).first()
        
        if states and states.extra:
            return states.extra.get("raw_state_text")
        
        return None
