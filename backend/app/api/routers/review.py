# AIMETA P=审查API_六维审查与一致性|R=审查接口|NR=不含生成逻辑|E=route:POST_/api/review/*|X=http|A=审查|D=fastapi,sqlalchemy|S=db|RD=./README.ai
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.dependencies import get_current_user
from ...db.session import get_session
from ...schemas.user import UserInDB
from ...services.constitution_service import ConstitutionService
from ...services.consistency_service import ConsistencyService
from ...services.llm_service import LLMService
from ...services.novel_service import NovelService
from ...services.prompt_service import PromptService
from ...services.six_dimension_review_service import SixDimensionReviewService
from ...services.writer_persona_service import WriterPersonaService

router = APIRouter(prefix="/api/review", tags=["Review"])


class SixDimensionReviewRequest(BaseModel):
    project_id: str
    chapter_number: int
    chapter_title: Optional[str] = None
    chapter_content: str
    chapter_plan: Optional[str] = None
    previous_summary: Optional[str] = None
    character_profiles: Optional[str] = None
    world_setting: Optional[str] = None


class ConsistencyReviewRequest(BaseModel):
    project_id: str
    chapter_text: str
    include_foreshadowing: bool = True


@router.post("/six-dimension")
async def review_six_dimension(
    request: SixDimensionReviewRequest,
    session: AsyncSession = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
) -> Dict[str, Any]:
    novel_service = NovelService(session)
    await novel_service.ensure_project_owner(request.project_id, current_user.id)

    llm_service = LLMService(session)
    prompt_service = PromptService(session)
    constitution_service = ConstitutionService(session, llm_service, prompt_service)
    persona_service = WriterPersonaService(session, llm_service, prompt_service)
    review_service = SixDimensionReviewService(
        session, llm_service, prompt_service, constitution_service, persona_service
    )

    result = await review_service.review_chapter(
        project_id=request.project_id,
        chapter_number=request.chapter_number,
        chapter_title=request.chapter_title or "",
        chapter_content=request.chapter_content,
        chapter_plan=request.chapter_plan,
        previous_summary=request.previous_summary,
        character_profiles=request.character_profiles,
        world_setting=request.world_setting,
    )
    return {"project_id": request.project_id, "review": result}


@router.post("/consistency")
async def review_consistency(
    request: ConsistencyReviewRequest,
    session: AsyncSession = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
) -> Dict[str, Any]:
    novel_service = NovelService(session)
    await novel_service.ensure_project_owner(request.project_id, current_user.id)

    sync_session = getattr(session, "sync_session", session)
    consistency_service = ConsistencyService(sync_session, LLMService(session))
    result = await consistency_service.check_consistency(
        project_id=request.project_id,
        chapter_text=request.chapter_text,
        user_id=current_user.id,
        include_foreshadowing=request.include_foreshadowing,
    )

    report = {
        "is_consistent": result.is_consistent,
        "summary": result.summary,
        "check_time_ms": result.check_time_ms,
        "violations": [
            {
                "severity": v.severity.value if hasattr(v.severity, "value") else v.severity,
                "category": v.category,
                "description": v.description,
                "location": v.location,
                "suggested_fix": v.suggested_fix,
                "confidence": v.confidence,
            }
            for v in result.violations
        ],
    }

    return {"project_id": request.project_id, "review": report}
