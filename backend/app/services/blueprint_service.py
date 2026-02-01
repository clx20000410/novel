# AIMETA P=章节蓝图服务_蓝图元数据管理|R=蓝图CRUD_元数据生成|NR=不含生成逻辑|E=BlueprintService|X=internal|A=蓝图管理_元数据生成|D=llm_service|S=none|RD=./README.ai
"""
章节蓝图服务 (BlueprintService)

融合自 AI_NovelGenerator 的章节蓝图设计，提供：
1. 章节蓝图元数据的CRUD操作
2. 从大纲自动生成蓝图元数据
3. 蓝图模板管理
4. 节奏曲线规划

这些元数据用于指导 L2 Director 生成章节任务，实现"慢节奏 + 跨章起承转合"。
"""
import logging
from typing import Optional, Dict, Any, List
import json

from sqlalchemy.orm import Session

from ..models.chapter_blueprint import (
    ChapterBlueprint, 
    BlueprintTemplate,
    SuspenseDensity,
    ForeshadowingOp,
    ChapterFunction
)
from ..models.novel import ChapterOutline, NovelProject
from .llm_service import LLMService

logger = logging.getLogger(__name__)


# ==================== 提示词模板 ====================

GENERATE_BLUEPRINT_PROMPT = """\
基于以下章节大纲，生成详细的章节蓝图元数据：

## 小说信息：
- 类型：{genre}
- 风格：{style}
- 总章节数：{total_chapters}

## 当前章节大纲：
- 章节号：第{chapter_number}章
- 标题：{title}
- 摘要：{summary}

## 前后章节信息：
- 前一章：{prev_chapter}
- 后一章：{next_chapter}

## 请生成以下元数据：

1. **悬念密度** (suspense_density)：
   - compact: 紧凑，高密度悬念，适合高潮章节
   - gradual: 渐进，逐步铺垫，适合过渡章节
   - explosive: 爆发，集中释放，适合转折章节
   - relaxed: 舒缓，低密度，适合缓冲章节

2. **伏笔操作** (foreshadowing_ops)：
   - plant: 埋设新伏笔
   - reinforce: 强化已有伏笔
   - payoff: 回收伏笔
   - none: 无操作
   （可多选，用逗号分隔）

3. **认知颠覆等级** (cognitive_twist_level)：1-5级

4. **章节功能** (chapter_function)：
   - progression: 推进主线
   - turning: 剧情转折
   - revelation: 揭示信息
   - buildup: 铺垫
   - climax: 高潮
   - resolution: 收束
   - interlude: 过渡

5. **章节定位** (chapter_focus)：角色/事件/主题等

6. **悬念类型** (suspense_type)：信息差/道德困境/时间压力等

7. **情感弧线** (emotional_arc)：如"怀疑→恐惧→决绝"

请以JSON格式返回：
{{
  "suspense_density": "gradual",
  "foreshadowing_ops": "plant,reinforce",
  "cognitive_twist_level": 2,
  "chapter_function": "progression",
  "chapter_focus": "主角成长",
  "suspense_type": "信息差",
  "emotional_arc": "平静→好奇→震惊",
  "brief_summary": "一句话概括本章"
}}

仅返回JSON，不要解释任何内容。
"""

GENERATE_BATCH_BLUEPRINT_PROMPT = """\
基于以下小说架构，为所有章节生成蓝图元数据：

## 小说信息：
- 类型：{genre}
- 风格：{style}
- 总章节数：{total_chapters}
- 故事概要：{synopsis}

## 章节大纲列表：
{outlines}

## 节奏规划要求：
1. 每3-5章构成一个悬念单元，包含完整的小高潮
2. 单元之间设置"认知过山车"（连续2章紧张→1章缓冲）
3. 关键转折章需预留多视角铺垫
4. 伏笔操作要形成完整的"埋设→强化→回收"链条

请为每章生成蓝图元数据，以JSON数组格式返回：
[
  {{
    "chapter_number": 1,
    "suspense_density": "gradual",
    "foreshadowing_ops": "plant",
    "cognitive_twist_level": 1,
    "chapter_function": "buildup",
    "chapter_focus": "...",
    "suspense_type": "...",
    "emotional_arc": "...",
    "brief_summary": "..."
  }},
  ...
]

仅返回JSON数组，不要解释任何内容。
"""


class BlueprintService:
    """
    章节蓝图服务
    
    负责章节蓝图元数据的管理和生成。
    """
    
    def __init__(
        self,
        db: Session,
        llm_service: LLMService
    ):
        self.db = db
        self.llm_service = llm_service
    
    # ==================== CRUD 操作 ====================
    
    def get_blueprint(
        self,
        project_id: str,
        chapter_number: int
    ) -> Optional[ChapterBlueprint]:
        """获取章节蓝图"""
        return self.db.query(ChapterBlueprint).filter(
            ChapterBlueprint.project_id == project_id,
            ChapterBlueprint.chapter_number == chapter_number
        ).first()
    
    def get_all_blueprints(
        self,
        project_id: str
    ) -> List[ChapterBlueprint]:
        """获取项目所有章节蓝图"""
        return self.db.query(ChapterBlueprint).filter(
            ChapterBlueprint.project_id == project_id
        ).order_by(ChapterBlueprint.chapter_number).all()
    
    def create_blueprint(
        self,
        project_id: str,
        chapter_number: int,
        **kwargs
    ) -> ChapterBlueprint:
        """创建章节蓝图"""
        blueprint = ChapterBlueprint(
            project_id=project_id,
            chapter_number=chapter_number,
            **kwargs
        )
        self.db.add(blueprint)
        self.db.flush()
        return blueprint
    
    def update_blueprint(
        self,
        blueprint: ChapterBlueprint,
        **kwargs
    ) -> ChapterBlueprint:
        """更新章节蓝图"""
        for key, value in kwargs.items():
            if hasattr(blueprint, key):
                setattr(blueprint, key, value)
        self.db.flush()
        return blueprint
    
    def delete_blueprint(
        self,
        project_id: str,
        chapter_number: int
    ) -> bool:
        """删除章节蓝图"""
        blueprint = self.get_blueprint(project_id, chapter_number)
        if blueprint:
            self.db.delete(blueprint)
            self.db.flush()
            return True
        return False
    
    # ==================== 自动生成 ====================
    
    async def generate_blueprint_from_outline(
        self,
        project_id: str,
        chapter_number: int,
        user_id: int
    ) -> Optional[ChapterBlueprint]:
        """
        从大纲自动生成章节蓝图
        """
        # 获取项目信息
        project = self.db.query(NovelProject).filter(
            NovelProject.id == project_id
        ).first()
        
        if not project or not project.blueprint:
            logger.error(f"项目不存在或无蓝图: {project_id}")
            return None
        
        # 获取章节大纲
        outline = self.db.query(ChapterOutline).filter(
            ChapterOutline.project_id == project_id,
            ChapterOutline.chapter_number == chapter_number
        ).first()
        
        if not outline:
            logger.error(f"章节大纲不存在: {project_id}/{chapter_number}")
            return None
        
        # 获取前后章节信息
        prev_outline = self.db.query(ChapterOutline).filter(
            ChapterOutline.project_id == project_id,
            ChapterOutline.chapter_number == chapter_number - 1
        ).first()
        
        next_outline = self.db.query(ChapterOutline).filter(
            ChapterOutline.project_id == project_id,
            ChapterOutline.chapter_number == chapter_number + 1
        ).first()
        
        # 计算总章节数
        total_chapters = self.db.query(ChapterOutline).filter(
            ChapterOutline.project_id == project_id
        ).count()
        
        # 生成蓝图
        prompt = GENERATE_BLUEPRINT_PROMPT.format(
            genre=project.blueprint.genre or "",
            style=project.blueprint.style or "",
            total_chapters=total_chapters,
            chapter_number=chapter_number,
            title=outline.title,
            summary=outline.summary or "",
            prev_chapter=f"第{prev_outline.chapter_number}章: {prev_outline.title}" if prev_outline else "无",
            next_chapter=f"第{next_outline.chapter_number}章: {next_outline.title}" if next_outline else "无"
        )
        
        try:
            response = await self.llm_service.generate(
                prompt=prompt,
                user_id=user_id,
                max_tokens=1000,
                temperature=0.5
            )
            
            if response:
                data = self._parse_json_response(response)
                if data:
                    # 创建或更新蓝图
                    blueprint = self.get_blueprint(project_id, chapter_number)
                    if blueprint:
                        return self.update_blueprint(blueprint, **data)
                    else:
                        return self.create_blueprint(project_id, chapter_number, **data)
        
        except Exception as e:
            logger.error(f"生成章节蓝图失败: {e}")
        
        return None
    
    async def generate_all_blueprints(
        self,
        project_id: str,
        user_id: int
    ) -> List[ChapterBlueprint]:
        """
        为项目所有章节生成蓝图
        """
        # 获取项目信息
        project = self.db.query(NovelProject).filter(
            NovelProject.id == project_id
        ).first()
        
        if not project or not project.blueprint:
            logger.error(f"项目不存在或无蓝图: {project_id}")
            return []
        
        # 获取所有章节大纲
        outlines = self.db.query(ChapterOutline).filter(
            ChapterOutline.project_id == project_id
        ).order_by(ChapterOutline.chapter_number).all()
        
        if not outlines:
            return []
        
        # 格式化大纲列表
        outlines_text = "\n".join([
            f"第{o.chapter_number}章 - {o.title}: {o.summary or '无摘要'}"
            for o in outlines
        ])
        
        prompt = GENERATE_BATCH_BLUEPRINT_PROMPT.format(
            genre=project.blueprint.genre or "",
            style=project.blueprint.style or "",
            total_chapters=len(outlines),
            synopsis=project.blueprint.full_synopsis or "",
            outlines=outlines_text
        )
        
        try:
            response = await self.llm_service.generate(
                prompt=prompt,
                user_id=user_id,
                max_tokens=8000,
                temperature=0.5
            )
            
            if response:
                data_list = self._parse_json_response(response)
                if isinstance(data_list, list):
                    blueprints = []
                    for data in data_list:
                        chapter_number = data.pop("chapter_number", None)
                        if chapter_number:
                            blueprint = self.get_blueprint(project_id, chapter_number)
                            if blueprint:
                                blueprint = self.update_blueprint(blueprint, **data)
                            else:
                                blueprint = self.create_blueprint(
                                    project_id, chapter_number, **data
                                )
                            blueprints.append(blueprint)
                    
                    self.db.commit()
                    return blueprints
        
        except Exception as e:
            logger.error(f"批量生成章节蓝图失败: {e}")
            self.db.rollback()
        
        return []
    
    # ==================== 模板管理 ====================
    
    def get_template(self, template_id: int) -> Optional[BlueprintTemplate]:
        """获取蓝图模板"""
        return self.db.query(BlueprintTemplate).filter(
            BlueprintTemplate.id == template_id
        ).first()
    
    def get_system_templates(self) -> List[BlueprintTemplate]:
        """获取系统预设模板"""
        return self.db.query(BlueprintTemplate).filter(
            BlueprintTemplate.template_type == "system"
        ).all()
    
    def get_user_templates(self, user_id: int) -> List[BlueprintTemplate]:
        """获取用户自定义模板"""
        return self.db.query(BlueprintTemplate).filter(
            BlueprintTemplate.user_id == user_id,
            BlueprintTemplate.template_type == "user"
        ).all()
    
    def create_template(
        self,
        name: str,
        config: Dict,
        description: str = "",
        user_id: Optional[int] = None
    ) -> BlueprintTemplate:
        """创建蓝图模板"""
        template = BlueprintTemplate(
            name=name,
            description=description,
            template_type="user" if user_id else "system",
            user_id=user_id,
            config=config
        )
        self.db.add(template)
        self.db.flush()
        return template
    
    def apply_template(
        self,
        project_id: str,
        chapter_number: int,
        template_id: int
    ) -> Optional[ChapterBlueprint]:
        """应用模板到章节"""
        template = self.get_template(template_id)
        if not template:
            return None
        
        blueprint = self.get_blueprint(project_id, chapter_number)
        if blueprint:
            return self.update_blueprint(blueprint, **template.config)
        else:
            return self.create_blueprint(project_id, chapter_number, **template.config)
    
    # ==================== 节奏分析 ====================
    
    def analyze_pacing(self, project_id: str) -> Dict[str, Any]:
        """
        分析项目的节奏分布
        """
        blueprints = self.get_all_blueprints(project_id)
        
        if not blueprints:
            return {"error": "无章节蓝图"}
        
        analysis = {
            "total_chapters": len(blueprints),
            "suspense_distribution": {},
            "function_distribution": {},
            "twist_curve": [],
            "foreshadowing_flow": {
                "plant": [],
                "reinforce": [],
                "payoff": []
            },
            "recommendations": []
        }
        
        # 统计分布
        for bp in blueprints:
            # 悬念密度分布
            density = bp.suspense_density or "unknown"
            analysis["suspense_distribution"][density] = \
                analysis["suspense_distribution"].get(density, 0) + 1
            
            # 章节功能分布
            function = bp.chapter_function or "unknown"
            analysis["function_distribution"][function] = \
                analysis["function_distribution"].get(function, 0) + 1
            
            # 认知颠覆曲线
            analysis["twist_curve"].append({
                "chapter": bp.chapter_number,
                "level": bp.cognitive_twist_level or 1
            })
            
            # 伏笔流向
            if bp.foreshadowing_ops:
                ops = bp.foreshadowing_ops.split(",")
                for op in ops:
                    op = op.strip()
                    if op in analysis["foreshadowing_flow"]:
                        analysis["foreshadowing_flow"][op].append(bp.chapter_number)
        
        # 生成建议
        analysis["recommendations"] = self._generate_pacing_recommendations(analysis)
        
        return analysis
    
    def _generate_pacing_recommendations(self, analysis: Dict) -> List[str]:
        """生成节奏建议"""
        recommendations = []
        
        # 检查悬念密度分布
        suspense_dist = analysis["suspense_distribution"]
        if suspense_dist.get("relaxed", 0) < analysis["total_chapters"] * 0.1:
            recommendations.append("建议增加一些舒缓章节，给读者喘息空间")
        
        if suspense_dist.get("explosive", 0) > analysis["total_chapters"] * 0.3:
            recommendations.append("爆发章节过多，可能导致读者疲劳")
        
        # 检查伏笔流向
        foreshadowing = analysis["foreshadowing_flow"]
        if len(foreshadowing["plant"]) > len(foreshadowing["payoff"]) * 2:
            recommendations.append("埋设的伏笔过多，注意及时回收")
        
        # 检查认知颠覆曲线
        twist_curve = analysis["twist_curve"]
        high_twists = [t for t in twist_curve if t["level"] >= 4]
        if len(high_twists) > analysis["total_chapters"] * 0.2:
            recommendations.append("高强度反转过多，可能降低冲击力")
        
        return recommendations
    
    def _parse_json_response(self, response: str) -> Any:
        """解析JSON响应"""
        try:
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            return None
    
    def init_system_templates(self):
        """初始化系统预设模板"""
        templates = [
            {
                "name": "高潮章节",
                "description": "适用于剧情高潮，高悬念密度，伏笔回收",
                "config": {
                    "suspense_density": SuspenseDensity.EXPLOSIVE.value,
                    "foreshadowing_ops": "payoff",
                    "cognitive_twist_level": 4,
                    "chapter_function": ChapterFunction.CLIMAX.value
                }
            },
            {
                "name": "铺垫章节",
                "description": "适用于铺垫，渐进悬念，埋设伏笔",
                "config": {
                    "suspense_density": SuspenseDensity.GRADUAL.value,
                    "foreshadowing_ops": "plant",
                    "cognitive_twist_level": 1,
                    "chapter_function": ChapterFunction.BUILDUP.value
                }
            },
            {
                "name": "过渡章节",
                "description": "适用于章节间过渡，舒缓节奏",
                "config": {
                    "suspense_density": SuspenseDensity.RELAXED.value,
                    "foreshadowing_ops": "none",
                    "cognitive_twist_level": 1,
                    "chapter_function": ChapterFunction.INTERLUDE.value
                }
            },
            {
                "name": "转折章节",
                "description": "适用于剧情转折，强化伏笔，中等反转",
                "config": {
                    "suspense_density": SuspenseDensity.COMPACT.value,
                    "foreshadowing_ops": "reinforce",
                    "cognitive_twist_level": 3,
                    "chapter_function": ChapterFunction.TURNING.value
                }
            }
        ]
        
        for t in templates:
            existing = self.db.query(BlueprintTemplate).filter(
                BlueprintTemplate.name == t["name"],
                BlueprintTemplate.template_type == "system"
            ).first()
            
            if not existing:
                self.create_template(
                    name=t["name"],
                    description=t["description"],
                    config=t["config"]
                )
        
        self.db.commit()
