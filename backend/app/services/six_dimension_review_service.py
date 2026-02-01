"""
六维度审查服务

提供全面的章节审查功能，包括：
1. 宪法合规检查
2. 内部一致性检查
3. 跨章一致性检查
4. 计划合规检查
5. 风格合规检查
6. 冲突检测
"""
from typing import Optional, Dict, Any, List
import json

from sqlalchemy.ext.asyncio import AsyncSession

from .constitution_service import ConstitutionService
from .writer_persona_service import WriterPersonaService
from .llm_service import LLMService
from .prompt_service import PromptService


class SixDimensionReviewService:
    """六维度审查服务"""

    def __init__(
        self,
        db: AsyncSession,
        llm_service: LLMService,
        prompt_service: PromptService,
        constitution_service: ConstitutionService,
        writer_persona_service: WriterPersonaService
    ):
        self.db = db
        self.llm_service = llm_service
        self.prompt_service = prompt_service
        self.constitution_service = constitution_service
        self.writer_persona_service = writer_persona_service

    async def review_chapter(
        self,
        project_id: str,
        chapter_number: int,
        chapter_title: str,
        chapter_content: str,
        chapter_plan: Optional[str] = None,
        previous_summary: Optional[str] = None,
        character_profiles: Optional[str] = None,
        world_setting: Optional[str] = None
    ) -> Dict[str, Any]:
        """执行六维度审查"""
        
        # 获取宪法和人格
        constitution = await self.constitution_service.get_constitution(project_id)
        persona = await self.writer_persona_service.get_active_persona(project_id)
        
        # 获取审查提示词
        prompt_template = await self.prompt_service.get_prompt("six_dimension_review")
        if not prompt_template:
            return self._create_default_result("未找到六维度审查提示词")
        
        # 构建提示词
        prompt = prompt_template
        prompt = prompt.replace("{{chapter_number}}", str(chapter_number))
        prompt = prompt.replace("{{chapter_title}}", chapter_title or "")
        prompt = prompt.replace("{{chapter_content}}", chapter_content)
        prompt = prompt.replace(
            "{{constitution}}", 
            self.constitution_service.get_constitution_context(constitution)
        )
        prompt = prompt.replace(
            "{{writer_persona}}", 
            self.writer_persona_service.get_persona_context(persona)
        )
        prompt = prompt.replace("{{chapter_plan}}", chapter_plan or "（无章节计划）")
        prompt = prompt.replace("{{previous_summary}}", previous_summary or "（无前文摘要）")
        prompt = prompt.replace("{{character_profiles}}", character_profiles or "（无角色档案）")
        prompt = prompt.replace("{{world_setting}}", world_setting or "（无世界设定）")
        
        # 调用 LLM 进行审查
        response = await self.llm_service.generate(
            prompt=prompt,
            system_prompt="你是一位资深的小说编辑，负责对章节进行全面的六维度审查。请以 JSON 格式输出审查结果。"
        )
        
        # 解析结果
        try:
            content = response or ""
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                result = json.loads(content[json_start:json_end])
                return result
        except json.JSONDecodeError:
            pass
        
        return self._create_default_result("审查完成，但结果解析失败")

    async def quick_review(
        self,
        project_id: str,
        chapter_content: str
    ) -> Dict[str, Any]:
        """快速审查（仅检查关键维度）"""
        
        results = {
            "overall_score": 100,
            "quick_checks": []
        }
        
        # 1. 宪法合规快速检查
        constitution = await self.constitution_service.get_constitution(project_id)
        if constitution and constitution.forbidden_content:
            for forbidden in constitution.forbidden_content:
                if forbidden.lower() in chapter_content.lower():
                    results["quick_checks"].append({
                        "dimension": "constitution",
                        "severity": "critical",
                        "description": f"检测到禁忌内容：{forbidden}"
                    })
                    results["overall_score"] -= 20
        
        # 2. 风格合规快速检查
        style_result = await self.writer_persona_service.check_style_compliance(
            project_id, chapter_content
        )
        if not style_result["compliance"]:
            for issue in style_result["issues"]:
                if issue["severity"] == "warning":
                    results["quick_checks"].append({
                        "dimension": "style",
                        "severity": "warning",
                        "description": issue["description"]
                    })
                    results["overall_score"] -= 5
        
        # 3. 基本一致性检查（检测明显的矛盾）
        # 这里可以添加更多的快速检查逻辑
        
        results["overall_score"] = max(0, results["overall_score"])
        results["passed"] = results["overall_score"] >= 60
        
        return results

    def _create_default_result(self, summary: str) -> Dict[str, Any]:
        """创建默认结果"""
        return {
            "overall_score": 80,
            "dimensions": {
                "constitution_compliance": {"score": 100, "issues": []},
                "internal_consistency": {"score": 100, "issues": []},
                "cross_chapter_consistency": {"score": 100, "issues": []},
                "plan_compliance": {"score": 100, "issues": []},
                "style_compliance": {"score": 100, "issues": []},
                "conflict_detection": {"score": 100, "issues": []}
            },
            "critical_issues_count": 0,
            "warning_issues_count": 0,
            "info_issues_count": 0,
            "summary": summary,
            "priority_fixes": [],
            "recommendations": []
        }

    def aggregate_issues(self, review_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """聚合所有维度的问题"""
        all_issues = []
        
        dimensions = review_result.get("dimensions", {})
        for dim_name, dim_data in dimensions.items():
            for issue in dim_data.get("issues", []):
                issue["dimension"] = dim_name
                all_issues.append(issue)
        
        # 按严重性排序
        severity_order = {"critical": 0, "warning": 1, "info": 2}
        all_issues.sort(key=lambda x: severity_order.get(x.get("severity", "info"), 3))
        
        return all_issues

    def get_priority_fixes(self, review_result: Dict[str, Any], max_count: int = 5) -> List[str]:
        """获取优先修复项"""
        all_issues = self.aggregate_issues(review_result)
        
        priority_fixes = []
        for issue in all_issues:
            if issue.get("severity") in ["critical", "warning"]:
                fix = issue.get("suggestion") or issue.get("description", "")
                if fix and fix not in priority_fixes:
                    priority_fixes.append(fix)
                    if len(priority_fixes) >= max_count:
                        break
        
        return priority_fixes
