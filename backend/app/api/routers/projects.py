# AIMETA P=项目资源API_宪法人格记忆等|R=项目资源管理|NR=不含生成逻辑|E=route:GET_PUT_/api/projects/*|X=http|A=资源接口|D=fastapi,sqlalchemy|S=db|RD=./README.ai
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.dependencies import get_current_user
from ...db.session import get_session
from ...models.novel import Chapter
from ...schemas.user import UserInDB
from ...services.constitution_service import ConstitutionService
from ...services.faction_service import FactionService
from ...services.llm_service import LLMService
from ...services.memory_layer_service import MemoryLayerService
from ...services.novel_service import NovelService
from ...services.prompt_service import PromptService
from ...services.writer_persona_service import WriterPersonaService
from ...models.project_memory import ProjectMemory

router = APIRouter(prefix="/api/projects", tags=["Projects"])


class PersonaPayload(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    style_tags: Optional[List[str]] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    preferences: Optional[List[str]] = None
    avoidances: Optional[List[str]] = None
    sample_sentences: Optional[List[str]] = None
    narrative_voice: Optional[str] = None
    language_style: Optional[str] = None
    pacing_style: Optional[str] = None
    emotional_tone: Optional[str] = None
    dialogue_style: Optional[str] = None
    description_style: Optional[str] = None
    personal_quirks: Optional[List[str]] = None
    is_active: Optional[bool] = None
    extra: Optional[Dict[str, Any]] = None


class ProjectMemoryPayload(BaseModel):
    global_summary: Optional[str] = None
    plot_arcs: Optional[Dict[str, Any]] = None
    story_timeline_summary: Optional[str] = None


class FactionPayload(BaseModel):
    id: Optional[int] = None
    name: str
    faction_type: Optional[str] = None
    description: Optional[str] = None
    power_level: Optional[str] = None
    territory: Optional[str] = None
    resources: Optional[List[str]] = None
    leader: Optional[str] = None
    hierarchy: Optional[Dict[str, Any]] = None
    member_count: Optional[str] = None
    goals: Optional[List[str]] = None
    current_status: Optional[str] = None
    recent_events: Optional[List[str]] = None
    culture: Optional[str] = None
    rules: Optional[List[str]] = None
    traditions: Optional[List[str]] = None
    extra: Optional[Dict[str, Any]] = None


def _model_to_dict(instance: Any) -> Optional[Dict[str, Any]]:
    if instance is None:
        return None
    return {k: v for k, v in vars(instance).items() if not k.startswith("_")}


@router.get("/{project_id}/constitution")
async def get_constitution(
    project_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
) -> Dict[str, Any]:
    novel_service = NovelService(session)
    await novel_service.ensure_project_owner(project_id, current_user.id)

    constitution_service = ConstitutionService(session, LLMService(session), PromptService(session))
    constitution = await constitution_service.get_constitution(project_id)
    return {"project_id": project_id, "constitution": _model_to_dict(constitution)}


@router.put("/{project_id}/constitution")
async def put_constitution(
    project_id: str,
    payload: Dict[str, Any] = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
) -> Dict[str, Any]:
    novel_service = NovelService(session)
    await novel_service.ensure_project_owner(project_id, current_user.id)

    constitution_service = ConstitutionService(session, LLMService(session), PromptService(session))
    constitution = await constitution_service.create_or_update_constitution(project_id, payload)
    return {"project_id": project_id, "constitution": _model_to_dict(constitution)}


@router.get("/{project_id}/persona")
async def get_persona(
    project_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
) -> Dict[str, Any]:
    novel_service = NovelService(session)
    await novel_service.ensure_project_owner(project_id, current_user.id)

    persona_service = WriterPersonaService(session, LLMService(session), PromptService(session))
    persona = await persona_service.get_active_persona(project_id)
    return {"project_id": project_id, "persona": _model_to_dict(persona)}


@router.put("/{project_id}/persona")
async def put_persona(
    project_id: str,
    payload: PersonaPayload,
    session: AsyncSession = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
) -> Dict[str, Any]:
    novel_service = NovelService(session)
    await novel_service.ensure_project_owner(project_id, current_user.id)

    persona_service = WriterPersonaService(session, LLMService(session), PromptService(session))
    payload_dict = payload.model_dump(exclude_unset=True)
    persona_id = payload_dict.pop("id", None)

    if persona_id:
        existing_persona = await persona_service.get_persona_by_id(persona_id)
        if not existing_persona or existing_persona.project_id != project_id:
            raise HTTPException(status_code=404, detail="Writer 人格不存在")
        persona = await persona_service.update_persona(persona_id, payload_dict)
    else:
        persona = await persona_service.create_persona(project_id, payload_dict)

    if payload.is_active:
        await persona_service.set_active_persona(project_id, persona.id)

    return {"project_id": project_id, "persona": _model_to_dict(persona)}


@router.get("/{project_id}/memory")
async def get_project_memory(
    project_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
) -> Dict[str, Any]:
    novel_service = NovelService(session)
    await novel_service.ensure_project_owner(project_id, current_user.id)

    result = await session.execute(
        select(ProjectMemory).where(ProjectMemory.project_id == project_id)
    )
    memory = result.scalars().first()
    return {"project_id": project_id, "memory": _model_to_dict(memory)}


@router.put("/{project_id}/memory")
async def put_project_memory(
    project_id: str,
    payload: ProjectMemoryPayload,
    session: AsyncSession = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
) -> Dict[str, Any]:
    novel_service = NovelService(session)
    await novel_service.ensure_project_owner(project_id, current_user.id)

    result = await session.execute(
        select(ProjectMemory).where(ProjectMemory.project_id == project_id)
    )
    memory = result.scalars().first()
    if not memory:
        memory = ProjectMemory(project_id=project_id)
        session.add(memory)

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        if hasattr(memory, key):
            setattr(memory, key, value)

    await session.commit()
    await session.refresh(memory)
    return {"project_id": project_id, "memory": _model_to_dict(memory)}


@router.get("/{project_id}/characters/state")
async def get_character_states(
    project_id: str,
    chapter_number: Optional[int] = None,
    session: AsyncSession = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
) -> Dict[str, Any]:
    novel_service = NovelService(session)
    await novel_service.ensure_project_owner(project_id, current_user.id)

    if chapter_number is None:
        result = await session.execute(
            select(Chapter.chapter_number).where(Chapter.project_id == project_id)
        )
        chapter_numbers = [row[0] for row in result.all()]
        chapter_number = max(chapter_numbers) if chapter_numbers else 0

    memory_service = MemoryLayerService(session, LLMService(session), PromptService(session))
    states = await memory_service.get_all_character_states(project_id, chapter_number)
    return {
        "project_id": project_id,
        "chapter_number": chapter_number,
        "states": [_model_to_dict(state) for state in states],
    }


@router.get("/{project_id}/factions")
async def get_factions(
    project_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
) -> Dict[str, Any]:
    novel_service = NovelService(session)
    await novel_service.ensure_project_owner(project_id, current_user.id)

    faction_service = FactionService(session, PromptService(session))
    factions = await faction_service.get_factions_by_project(project_id)
    return {"project_id": project_id, "factions": [_model_to_dict(faction) for faction in factions]}


@router.put("/{project_id}/factions")
async def put_factions(
    project_id: str,
    payload: List[FactionPayload] = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
) -> Dict[str, Any]:
    novel_service = NovelService(session)
    await novel_service.ensure_project_owner(project_id, current_user.id)

    faction_service = FactionService(session, PromptService(session))
    saved = []
    for faction_payload in payload:
        data = faction_payload.model_dump(exclude_unset=True)
        faction_id = data.pop("id", None)
        if faction_id:
            existing = await faction_service.get_faction(faction_id)
            if not existing or existing.project_id != project_id:
                continue
            faction = await faction_service.update_faction(faction_id, data)
            if faction:
                saved.append(faction)
        else:
            saved.append(await faction_service.create_faction(project_id, data))

    return {"project_id": project_id, "factions": [_model_to_dict(faction) for faction in saved]}
