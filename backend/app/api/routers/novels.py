# AIMETA P=小说API_项目和章节管理|R=小说CRUD_章节管理|NR=不含内容生成|E=route:GET_POST_/api/novels/*|X=http|A=小说CRUD_章节|D=fastapi,sqlalchemy|S=db|RD=./README.ai
import json
import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Body, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.dependencies import get_current_user
from ...core.config import settings
from ...db.session import get_session
from ...schemas.novel import (
    ActiveInspirationResponse,
    Blueprint,
    BlueprintGenerationResponse,
    BlueprintPatch,
    Chapter as ChapterSchema,
    ConverseRequest,
    ConverseResponse,
    NovelProject as NovelProjectSchema,
    NovelProjectSummary,
    NovelSectionResponse,
    NovelSectionType,
)
from ...schemas.user import UserInDB
from ...services.import_service import ImportService
from ...services.llm_service import LLMService
from ...services.novel_service import NovelService
from ...services.prompt_service import PromptService
from ...services.project_transfer_service import ProjectTransferService
from ...utils.json_utils import (
    fix_json_missing_commas,
    is_json_complete,
    parse_json_safely,
    remove_think_tags,
    sanitize_json_like_text,
    unwrap_markdown_json,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/novels", tags=["Novels"])

JSON_RESPONSE_INSTRUCTION = """
IMPORTANT: 你的回复必须是合法的 JSON 对象，并严格包含以下字段：
{
  "ai_message": "string",
  "ui_control": {
    "type": "single_choice | text_input | info_display",
    "options": [
      {"id": "option_1", "label": "string"}
    ],
    "placeholder": "string"
  },
  "conversation_state": {},
  "is_complete": false
}
不要输出额外的文本或解释。
"""


def _ensure_prompt(prompt: str | None, name: str) -> str:
    if not prompt:
        raise HTTPException(status_code=500, detail=f"未配置名为 {name} 的提示词，请联系管理员")
    return prompt


@router.post("", response_model=NovelProjectSchema, status_code=status.HTTP_201_CREATED)
async def create_novel(
    title: str = Body(...),
    initial_prompt: str = Body(...),
    force_new: bool = Body(False),
    session: AsyncSession = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
) -> NovelProjectSchema:
    """为当前用户创建一个新的小说项目。"""
    novel_service = NovelService(session)

    if force_new:
        await novel_service.abandon_active_inspiration_projects(current_user.id)
    else:
        active = await novel_service.get_active_inspiration_project(current_user.id)
        if active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"message": "active_inspiration_exists", "project_id": active.id},
            )

    project = await novel_service.create_project(current_user.id, title, initial_prompt)
    logger.info("用户 %s 创建项目 %s", current_user.id, project.id)
    return await novel_service.get_project_schema(project.id, current_user.id)


@router.get("/inspiration/active", response_model=ActiveInspirationResponse)
async def get_active_inspiration(
    session: AsyncSession = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
) -> ActiveInspirationResponse:
    """获取当前用户最近一条可继续的灵感记录（可能为空）。"""
    novel_service = NovelService(session)
    project = await novel_service.get_active_inspiration_project(current_user.id)
    if not project:
        return ActiveInspirationResponse(project=None)
    return ActiveInspirationResponse(project=novel_service.build_project_summary(project))


@router.post("/import", response_model=Dict[str, str], status_code=status.HTTP_201_CREATED)
async def import_novel(
    file: UploadFile,
    session: AsyncSession = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
) -> Dict[str, str]:
    """上传并导入小说文件。"""
    import_service = ImportService(session)
    project_id = await import_service.import_novel_from_file(current_user.id, file)
    logger.info("用户 %s 导入项目 %s", current_user.id, project_id)
    return {"id": project_id}


@router.post("/import-project", response_model=Dict[str, str], status_code=status.HTTP_201_CREATED)
async def import_project(
    file: UploadFile,
    session: AsyncSession = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
) -> Dict[str, str]:
    """上传并导入完整项目（JSON 导出文件）。"""
    content_bytes = await file.read()
    try:
        content_text = content_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="文件编码不支持，请使用 UTF-8") from exc

    try:
        payload = json.loads(content_text)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="文件内容不是合法的 JSON") from exc

    transfer_service = ProjectTransferService(session)
    try:
        project_id = await transfer_service.import_project(current_user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    logger.info("用户 %s 导入完整项目 %s", current_user.id, project_id)
    return {"id": project_id}


@router.post("/import-batch", response_model=Dict[str, List[str]], status_code=status.HTTP_201_CREATED)
async def import_projects_batch(
    file: UploadFile,
    session: AsyncSession = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
) -> Dict[str, List[str]]:
    """批量导入项目（JSON 导出包或多个项目列表）。"""
    content_bytes = await file.read()
    try:
        content_text = content_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="文件编码不支持，请使用 UTF-8") from exc

    try:
        payload = json.loads(content_text)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="文件内容不是合法的 JSON") from exc

    transfer_service = ProjectTransferService(session)
    try:
        ids = await transfer_service.import_bundle(current_user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    logger.info("用户 %s 批量导入项目 %s 个", current_user.id, len(ids))
    return {"ids": ids}


@router.get("/export-batch", response_model=Dict[str, Any])
async def export_projects_batch(
    session: AsyncSession = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
) -> Dict[str, Any]:
    """批量导出当前用户全部项目。"""
    transfer_service = ProjectTransferService(session)
    data = await transfer_service.export_bundle(current_user.id)
    logger.info("用户 %s 批量导出项目，共 %s 个", current_user.id, len(data.get("projects", [])))
    return data


@router.get("", response_model=List[NovelProjectSummary])
async def list_novels(
    session: AsyncSession = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
) -> List[NovelProjectSummary]:
    """列出用户的全部小说项目摘要信息。"""
    novel_service = NovelService(session)
    projects = await novel_service.list_projects_for_user(current_user.id)
    logger.info("用户 %s 获取项目列表，共 %s 个", current_user.id, len(projects))
    return projects


@router.get("/{project_id}", response_model=NovelProjectSchema)
async def get_novel(
    project_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
) -> NovelProjectSchema:
    novel_service = NovelService(session)
    logger.info("用户 %s 查询项目 %s", current_user.id, project_id)
    return await novel_service.get_project_schema(project_id, current_user.id)


@router.get("/{project_id}/export", response_model=Dict[str, Any])
async def export_project(
    project_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
) -> Dict[str, object]:
    """导出完整项目（JSON）。"""
    transfer_service = ProjectTransferService(session)
    data = await transfer_service.export_project(project_id, current_user.id)
    logger.info("用户 %s 导出完整项目 %s", current_user.id, project_id)
    return data


@router.get("/{project_id}/sections/{section}", response_model=NovelSectionResponse)
async def get_novel_section(
    project_id: str,
    section: NovelSectionType,
    session: AsyncSession = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
) -> NovelSectionResponse:
    novel_service = NovelService(session)
    logger.info("用户 %s 获取项目 %s 的 %s 区段", current_user.id, project_id, section)
    return await novel_service.get_section_data(project_id, current_user.id, section)


@router.get("/{project_id}/chapters/{chapter_number}", response_model=ChapterSchema)
async def get_chapter(
    project_id: str,
    chapter_number: int,
    session: AsyncSession = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
) -> ChapterSchema:
    novel_service = NovelService(session)
    logger.info("用户 %s 获取项目 %s 第 %s 章", current_user.id, project_id, chapter_number)
    return await novel_service.get_chapter_schema(project_id, current_user.id, chapter_number)


@router.delete("", status_code=status.HTTP_200_OK)
async def delete_novels(
    project_ids: List[str] = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
) -> Dict[str, str]:
    novel_service = NovelService(session)
    await novel_service.delete_projects(project_ids, current_user.id)
    logger.info("用户 %s 删除项目 %s", current_user.id, project_ids)
    return {"status": "success", "message": f"成功删除 {len(project_ids)} 个项目"}


@router.post("/{project_id}/concept/converse", response_model=ConverseResponse)
async def converse_with_concept(
    project_id: str,
    request: ConverseRequest,
    session: AsyncSession = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
) -> ConverseResponse:
    """与概念设计师（LLM）进行对话，引导蓝图筹备。"""
    novel_service = NovelService(session)
    prompt_service = PromptService(session)
    llm_service = LLMService(session)

    project = await novel_service.ensure_project_owner(project_id, current_user.id)
    if project.status in ("concept_complete", "blueprint_ready", "concept_abandoned"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="当前灵感已锁定，无法继续对话")
    if project.status == "draft":
        project.status = "concept_in_progress"
        await session.commit()

    history_records = await novel_service.list_conversations(project_id)
    logger.info(
        "项目 %s 概念对话请求，用户 %s，历史记录 %s 条",
        project_id,
        current_user.id,
        len(history_records),
    )
    conversation_history = [
        {"role": record.role, "content": record.content}
        for record in history_records
    ]
    user_content = json.dumps(request.user_input, ensure_ascii=False)
    conversation_history.append({"role": "user", "content": user_content})

    system_prompt = _ensure_prompt(await prompt_service.get_prompt("concept"), "concept")
    system_prompt = f"{system_prompt}\n{JSON_RESPONSE_INSTRUCTION}"

    llm_response = await llm_service.get_llm_response(
        system_prompt=system_prompt,
        conversation_history=conversation_history,
        temperature=0.8,
        user_id=current_user.id,
        timeout=240.0,
    )
    llm_response = remove_think_tags(llm_response)

    try:
        normalized = unwrap_markdown_json(llm_response)
        sanitized = sanitize_json_like_text(normalized)
        parsed = json.loads(sanitized)
    except json.JSONDecodeError as exc:
        logger.exception(
            "Failed to parse concept converse response: project_id=%s user_id=%s error=%s\nOriginal response: %s\nNormalized: %s\nSanitized: %s",
            project_id,
            current_user.id,
            exc,
            llm_response[:1000],
            normalized[:1000] if 'normalized' in locals() else "N/A",
            sanitized[:1000] if 'sanitized' in locals() else "N/A",
        )
        raise HTTPException(
            status_code=500,
            detail=f"概念对话失败，AI 返回的内容格式不正确。请重试或联系管理员。错误详情: {str(exc)}"
        ) from exc

    await novel_service.append_conversation(project_id, "user", user_content)
    await novel_service.append_conversation(project_id, "assistant", normalized)

    logger.info("项目 %s 概念对话完成，is_complete=%s", project_id, parsed.get("is_complete"))

    if parsed.get("is_complete"):
        parsed["ready_for_blueprint"] = True
        project.status = "concept_complete"
        await session.commit()

    parsed.setdefault("conversation_state", parsed.get("conversation_state", {}))
    return ConverseResponse(**parsed)


@router.post("/{project_id}/blueprint/generate", response_model=BlueprintGenerationResponse)
async def generate_blueprint(
    project_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
) -> BlueprintGenerationResponse:
    """根据完整对话分步生成可执行的小说蓝图（支持断点续传）。

    拆分为多步以避免代理服务截断长响应：
    1. 基本信息 + 世界观
    2. 角色与关系
    3. 章节大纲（分批，每批5章）

    每完成一步都会保存进度，如果中断可以继续。
    """
    novel_service = NovelService(session)
    prompt_service = PromptService(session)
    llm_service = LLMService(session)

    project = await novel_service.ensure_project_owner(project_id, current_user.id)
    if project.status in ("draft", "concept_in_progress"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="灵感未完成，无法生成蓝图")
    if project.status == "concept_abandoned":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="灵感已放弃，无法生成蓝图")

    # ── 检查是否有已保存的进度 ──
    existing_blueprint = await novel_service.get_blueprint(project_id)
    progress: dict = {}
    if existing_blueprint:
        ws = existing_blueprint.get("world_setting") or {}
        if isinstance(ws, dict):
            progress = ws.get("_generation_progress", {})

    completed_step = progress.get("completed_step", 0)
    total_chapters = progress.get("total_chapters", 0)
    generated_chapters = progress.get("generated_chapters", 0)

    if completed_step > 0:
        logger.info("项目 %s 检测到未完成的蓝图生成进度: step=%d, chapters=%d/%d",
                    project_id, completed_step, generated_chapters, total_chapters)
    else:
        logger.info("项目 %s 开始生成蓝图（分步模式）", project_id)

    history_records = await novel_service.list_conversations(project_id)
    if not history_records:
        logger.warning("项目 %s 缺少对话历史，无法生成蓝图", project_id)
        raise HTTPException(status_code=400, detail="缺少对话历史，请先完成概念对话后再生成蓝图")

    formatted_history: List[Dict[str, str]] = []
    for record in history_records:
        role = record.role
        content = record.content
        if not role or not content:
            continue
        try:
            normalized = unwrap_markdown_json(content)
            data = json.loads(normalized)
            if role == "user":
                user_value = data.get("value", data)
                if isinstance(user_value, str):
                    formatted_history.append({"role": "user", "content": user_value})
            elif role == "assistant":
                ai_message = data.get("ai_message") if isinstance(data, dict) else None
                if ai_message:
                    formatted_history.append({"role": "assistant", "content": ai_message})
        except (json.JSONDecodeError, AttributeError):
            continue

    if not formatted_history:
        logger.warning("项目 %s 对话历史格式异常，无法提取有效内容", project_id)
        raise HTTPException(
            status_code=400,
            detail="无法从历史对话中提取有效内容，请检查对话历史格式或重新进行概念对话"
        )

    system_prompt = _ensure_prompt(await prompt_service.get_prompt("screenwriting"), "screenwriting")
    bp_timeout = settings.blueprint_generation_timeout_seconds

    async def _llm_call(step_prompt: str) -> str:
        """发起一次 LLM 调用并返回清洗后的文本。"""
        raw = await llm_service.get_llm_response(
            system_prompt=system_prompt,
            conversation_history=formatted_history + [{"role": "user", "content": step_prompt}],
            temperature=0.3,
            user_id=current_user.id,
            timeout=bp_timeout,
            max_tokens=8192,
        )
        return remove_think_tags(raw)

    def _safe_parse(raw: str, step_name: str) -> dict:
        """安全解析 JSON，失败时给出明确提示。"""
        data = parse_json_safely(raw)
        if data is not None:
            return data if isinstance(data, dict) else {}
        if not is_json_complete(raw):
            logger.error("项目 %s 蓝图[%s]响应被截断: 长度=%d\n末尾: ...%s",
                         project_id, step_name, len(raw), raw[-200:])
            raise HTTPException(
                status_code=500,
                detail=f"蓝图生成（{step_name}）响应被截断（{len(raw)} 字符），请重试继续。"
            )
        logger.error("项目 %s 蓝图[%s]JSON 解析失败:\n%s", project_id, step_name, raw[:500])
        raise HTTPException(
            status_code=500,
            detail=f"蓝图生成（{step_name}）JSON 格式错误，请重试继续。"
        )

    async def _save_progress(bp_data: dict, step: int, total_ch: int = 0, gen_ch: int = 0) -> None:
        """保存蓝图生成进度。"""
        # 在 world_setting 中嵌入进度信息
        ws = bp_data.get("world_setting", {}) or {}
        if not isinstance(ws, dict):
            ws = {}
        ws["_generation_progress"] = {
            "completed_step": step,
            "total_chapters": total_ch,
            "generated_chapters": gen_ch,
        }
        bp_data["world_setting"] = ws
        blueprint = Blueprint(**bp_data)
        await novel_service.replace_blueprint(project_id, blueprint)
        await session.commit()
        logger.info("项目 %s 蓝图进度已保存: step=%d, chapters=%d/%d",
                    project_id, step, gen_ch, total_ch)

    # ── 从已有进度中恢复数据 ──
    step1_data: dict = {}
    step2_data: dict = {}
    all_outlines: list = []

    if completed_step >= 1 and existing_blueprint:
        # 恢复 Step 1 数据
        step1_data = {
            "title": existing_blueprint.get("title", ""),
            "target_audience": existing_blueprint.get("target_audience", ""),
            "genre": existing_blueprint.get("genre", ""),
            "style": existing_blueprint.get("style", ""),
            "tone": existing_blueprint.get("tone", ""),
            "one_sentence_summary": existing_blueprint.get("one_sentence_summary", ""),
            "full_synopsis": existing_blueprint.get("full_synopsis", ""),
            "world_setting": {k: v for k, v in (existing_blueprint.get("world_setting") or {}).items()
                             if k != "_generation_progress"},
        }
        logger.info("项目 %s 从进度恢复 Step 1 数据", project_id)

    if completed_step >= 2 and existing_blueprint:
        # 恢复 Step 2 数据
        step2_data = {
            "characters": existing_blueprint.get("characters", []),
            "relationships": existing_blueprint.get("relationships", []),
        }
        logger.info("项目 %s 从进度恢复 Step 2 数据", project_id)

    if completed_step >= 3 and existing_blueprint:
        # 恢复已生成的章节大纲
        all_outlines = list(existing_blueprint.get("chapter_outline", []))
        logger.info("项目 %s 从进度恢复 %d 章大纲", project_id, len(all_outlines))

    # ── Step 1: 基本信息 + 世界观 ──
    if completed_step < 1:
        logger.info("项目 %s 蓝图 Step 1/3: 基本信息 + 世界观", project_id)
        step1_prompt = (
            "请根据我们之前的对话，生成小说蓝图的【基本信息和世界观】部分。\n"
            "仅返回以下字段的 JSON，不要包含 characters、relationships、chapter_outline：\n\n"
            "```json\n"
            "{\n"
            '  "title": "小说标题",\n'
            '  "target_audience": "目标读者",\n'
            '  "genre": "类型",\n'
            '  "style": "风格",\n'
            '  "tone": "基调",\n'
            '  "one_sentence_summary": "一句话概要",\n'
            '  "full_synopsis": "完整概要（300-500字）",\n'
            '  "world_setting": {\n'
            '    "core_rules": "核心规则",\n'
            '    "key_locations": [{"name": "地点名", "description": "描述"}],\n'
            '    "factions": [{"name": "势力名", "description": "描述"}]\n'
            '  }\n'
            "}\n"
            "```\n"
            "仅返回 JSON，不要解释。"
        )
        step1_data = _safe_parse(await _llm_call(step1_prompt), "基本信息")
        await _save_progress({**step1_data, "characters": [], "relationships": [], "chapter_outline": []}, 1)
    else:
        logger.info("项目 %s 跳过 Step 1（已完成）", project_id)

    # ── Step 2: 角色与关系 ──
    if completed_step < 2:
        logger.info("项目 %s 蓝图 Step 2/3: 角色与关系", project_id)
        step2_prompt = (
            f"当前小说标题：{step1_data.get('title', '')}\n"
            f"类型：{step1_data.get('genre', '')}，风格：{step1_data.get('style', '')}\n"
            f"概要：{step1_data.get('one_sentence_summary', '')}\n\n"
            "请根据我们之前的对话，生成小说蓝图的【角色和人物关系】部分。\n"
            "仅返回以下字段的 JSON：\n\n"
            "```json\n"
            "{\n"
            '  "characters": [\n'
            '    {\n'
            '      "name": "角色名",\n'
            '      "identity": "身份",\n'
            '      "personality": "性格",\n'
            '      "goals": "目标",\n'
            '      "abilities": "能力",\n'
            '      "relationship_to_protagonist": "与主角关系"\n'
            '    }\n'
            '  ],\n'
            '  "relationships": [\n'
            '    {\n'
            '      "character_from": "角色A",\n'
            '      "character_to": "角色B",\n'
            '      "description": "关系描述"\n'
            '    }\n'
            '  ]\n'
            "}\n"
            "```\n"
            "仅返回 JSON，不要解释。"
        )
        step2_data = _safe_parse(await _llm_call(step2_prompt), "角色与关系")
        await _save_progress({
            **step1_data,
            "characters": step2_data.get("characters", []),
            "relationships": step2_data.get("relationships", []),
            "chapter_outline": [],
        }, 2)
    else:
        logger.info("项目 %s 跳过 Step 2（已完成）", project_id)

    # ── Step 3: 章节大纲（分批） ──
    if completed_step < 3 or generated_chapters < total_chapters:
        logger.info("项目 %s 蓝图 Step 3/3: 章节大纲", project_id)

        # 如果还没确定总章节数，先确定
        if total_chapters == 0:
            count_prompt = (
                f"当前小说标题：{step1_data.get('title', '')}\n"
                f"类型：{step1_data.get('genre', '')}，风格：{step1_data.get('style', '')}\n"
                f"概要：{step1_data.get('one_sentence_summary', '')}\n\n"
                "请根据我们之前的对话，确定这本小说的总章节数。\n"
                "仅返回一个 JSON：\n"
                '```json\n{"total_chapters": 数字}\n```\n'
                "仅返回 JSON，不要解释。"
            )
            count_data = _safe_parse(await _llm_call(count_prompt), "章节数量")
            total_chapters = int(count_data.get("total_chapters", 20))
            logger.info("项目 %s 蓝图总章节数: %d", project_id, total_chapters)

        # 分批生成章节大纲，从用户 LLM 配置读取 batch_size
        from ...repositories.llm_config_repository import LLMConfigRepository
        llm_config_repo = LLMConfigRepository(session)
        user_llm_config = await llm_config_repo.get_by_user(current_user.id)
        batch_size = getattr(user_llm_config, "blueprint_batch_size", 5) if user_llm_config else 5
        batch_size = max(1, min(batch_size, 50))  # 限制范围 1-50
        start_chapter = generated_chapters + 1  # 从断点继续

        for batch_start in range(start_chapter, total_chapters + 1, batch_size):
            batch_end = min(batch_start + batch_size - 1, total_chapters)
            logger.info("项目 %s 生成章节大纲: 第%d-%d章 / 共%d章",
                         project_id, batch_start, batch_end, total_chapters)

            outline_prompt = (
                f"当前小说标题：{step1_data.get('title', '')}\n"
                f"类型：{step1_data.get('genre', '')}，风格：{step1_data.get('style', '')}\n"
                f"概要：{step1_data.get('full_synopsis', '')[:500]}\n"
                f"总章节数：{total_chapters}\n\n"
            )
            if all_outlines:
                # 附上前面已生成的最后几章作为参考
                recent = all_outlines[-3:]
                outline_prompt += "已生成的最近章节：\n"
                for ch in recent:
                    outline_prompt += f"- 第{ch.get('chapter_number', '?')}章: {ch.get('title', '')} — {ch.get('summary', '')[:80]}\n"
                outline_prompt += "\n"

            outline_prompt += (
                f"请生成第 {batch_start} 章到第 {batch_end} 章的大纲。\n"
                "仅返回以下格式的 JSON：\n\n"
                "```json\n"
                "{\n"
                '  "chapter_outline": [\n'
                '    {"chapter_number": 数字, "title": "章节标题", "summary": "章节概要"}\n'
                '  ]\n'
                "}\n"
                "```\n"
                "仅返回 JSON，不要解释。"
            )
            batch_data = _safe_parse(await _llm_call(outline_prompt), f"章节大纲({batch_start}-{batch_end})")
            batch_outlines = batch_data.get("chapter_outline", [])
            if isinstance(batch_outlines, list):
                # Defensive: ensure each outline has required fields with defaults
                for outline in batch_outlines:
                    if isinstance(outline, dict):
                        outline.setdefault("chapter_number", 0)
                        outline.setdefault("title", "")
                        outline.setdefault("summary", "")
                all_outlines.extend(batch_outlines)

            # 每批完成后保存进度
            await _save_progress({
                **step1_data,
                "characters": step2_data.get("characters", []),
                "relationships": step2_data.get("relationships", []),
                "chapter_outline": all_outlines,
            }, 3, total_chapters, len(all_outlines))
    else:
        logger.info("项目 %s 跳过 Step 3（已完成）", project_id)

    # ── 合并所有数据并清理进度标记 ──
    final_world_setting = step1_data.get("world_setting", {}) or {}
    if isinstance(final_world_setting, dict):
        final_world_setting.pop("_generation_progress", None)  # 移除进度标记

    blueprint_data = {
        **step1_data,
        "world_setting": final_world_setting,
        "characters": step2_data.get("characters", []),
        "relationships": step2_data.get("relationships", []),
        "chapter_outline": all_outlines,
    }

    logger.info("项目 %s 蓝图生成完成: %d 角色, %d 关系, %d 章节",
                project_id,
                len(blueprint_data.get("characters", [])),
                len(blueprint_data.get("relationships", [])),
                len(all_outlines))

    blueprint = Blueprint(**blueprint_data)
    await novel_service.replace_blueprint(project_id, blueprint)

    project.status = "blueprint_ready"
    if blueprint.title:
        project.title = blueprint.title
    await session.commit()
    if blueprint.title:
        logger.info("项目 %s 更新标题为 %s，并标记为 blueprint_ready", project_id, blueprint.title)

    ai_message = (
        "太棒了！我已经根据我们的对话整理出完整的小说蓝图。请确认是否进入写作阶段，或提出修改意见。"
    )
    return BlueprintGenerationResponse(blueprint=blueprint, ai_message=ai_message)


@router.post("/{project_id}/blueprint/save", response_model=NovelProjectSchema)
async def save_blueprint(
    project_id: str,
    blueprint_data: Blueprint | None = Body(None),
    session: AsyncSession = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
) -> NovelProjectSchema:
    """保存蓝图信息，可用于手动覆盖自动生成结果。"""
    novel_service = NovelService(session)
    project = await novel_service.ensure_project_owner(project_id, current_user.id)
    if project.status == "concept_abandoned":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="灵感已放弃，无法保存蓝图")

    if blueprint_data:
        await novel_service.replace_blueprint(project_id, blueprint_data)
        project.status = "blueprint_ready"
        if blueprint_data.title:
            project.title = blueprint_data.title
        await session.commit()
        logger.info("项目 %s 手动保存蓝图", project_id)
    else:
        logger.warning("项目 %s 保存蓝图时未提供蓝图数据", project_id)
        raise HTTPException(status_code=400, detail="缺少蓝图数据，请提供有效的蓝图内容")

    return await novel_service.get_project_schema(project_id, current_user.id)


@router.patch("/{project_id}/blueprint", response_model=NovelProjectSchema)
async def patch_blueprint(
    project_id: str,
    payload: BlueprintPatch,
    session: AsyncSession = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
) -> NovelProjectSchema:
    """局部更新蓝图字段，对世界观或角色做微调。"""
    novel_service = NovelService(session)
    project = await novel_service.ensure_project_owner(project_id, current_user.id)

    update_data = payload.model_dump(exclude_unset=True)
    await novel_service.patch_blueprint(project_id, update_data)
    logger.info("项目 %s 局部更新蓝图字段：%s", project_id, list(update_data.keys()))
    return await novel_service.get_project_schema(project_id, current_user.id)
