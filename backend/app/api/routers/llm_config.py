# AIMETA P=LLM配置API_模型配置管理|R=LLM配置CRUD|NR=不含模型调用|E=route:GET_POST_/api/llm-configs/*|X=http|A=配置CRUD|D=fastapi,sqlalchemy|S=db|RD=./README.ai
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.dependencies import get_current_user
from ...db.session import get_session
from ...schemas.llm_config import (
    LLMConfigCreate,
    LLMConfigUpdate,
    LLMConfigRead,
    ModelListRequest,
    TestConnectionRequest,
    TestConnectionResponse,
)
from ...schemas.user import UserInDB
from ...services.llm_config_service import LLMConfigService


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/llm-configs", tags=["LLM Configuration"])


def get_llm_config_service(session: AsyncSession = Depends(get_session)) -> LLMConfigService:
    return LLMConfigService(session)


# ==================== 静态路由必须在动态路由之前 ====================

@router.get("", response_model=List[LLMConfigRead])
async def list_llm_configs(
    service: LLMConfigService = Depends(get_llm_config_service),
    current_user: UserInDB = Depends(get_current_user),
) -> List[LLMConfigRead]:
    """获取用户的所有 LLM 配置列表"""
    configs = await service.list_configs(current_user.id)
    logger.info("用户 %s 获取 LLM 配置列表，共 %d 条", current_user.id, len(configs))
    return configs


@router.post("", response_model=LLMConfigRead, status_code=status.HTTP_201_CREATED)
async def create_llm_config(
    payload: LLMConfigCreate,
    service: LLMConfigService = Depends(get_llm_config_service),
    current_user: UserInDB = Depends(get_current_user),
) -> LLMConfigRead:
    """创建新的 LLM 配置"""
    logger.info("用户 %s 创建 LLM 配置: %s", current_user.id, payload.name)
    return await service.create_config(current_user.id, payload)


@router.get("/active", response_model=LLMConfigRead)
async def get_active_llm_config(
    service: LLMConfigService = Depends(get_llm_config_service),
    current_user: UserInDB = Depends(get_current_user),
) -> LLMConfigRead:
    """获取当前激活的 LLM 配置"""
    config = await service.get_active_config(current_user.id)
    if not config:
        logger.warning("用户 %s 尚未设置激活的 LLM 配置", current_user.id)
        raise HTTPException(status_code=404, detail="尚未设置激活的配置")
    logger.info("用户 %s 获取激活的 LLM 配置", current_user.id)
    return config


@router.post("/models", response_model=List[str])
async def list_models(
    payload: ModelListRequest,
    service: LLMConfigService = Depends(get_llm_config_service),
    current_user: UserInDB = Depends(get_current_user),
) -> List[str]:
    """获取可用的模型列表"""
    try:
        models = await service.get_available_models(
            api_key=payload.llm_provider_api_key,
            base_url=payload.llm_provider_url,
            api_format=payload.api_format,
        )
        logger.info("用户 %s 获取模型列表，返回 %d 个模型", current_user.id, len(models))
        return models
    except Exception as e:
        logger.error("用户 %s 获取模型列表失败: %s", current_user.id, str(e))
        # 返回空列表而不是抛出异常，因为这只是提示功能
        return []


@router.post("/test", response_model=TestConnectionResponse)
async def test_connection(
    payload: TestConnectionRequest,
    service: LLMConfigService = Depends(get_llm_config_service),
    current_user: UserInDB = Depends(get_current_user),
) -> TestConnectionResponse:
    """测试 LLM 连接"""
    logger.info(
        "用户 %s 测试连接: api_format=%s model=%s",
        current_user.id, payload.api_format, payload.llm_provider_model
    )
    result = await service.test_connection(
        api_format=payload.api_format,
        api_key=payload.llm_provider_api_key,
        base_url=payload.llm_provider_url,
        model=payload.llm_provider_model,
    )
    return TestConnectionResponse(**result)


# ==================== 动态路由（带路径参数）====================

@router.get("/{config_id}", response_model=LLMConfigRead)
async def get_llm_config(
    config_id: int,
    service: LLMConfigService = Depends(get_llm_config_service),
    current_user: UserInDB = Depends(get_current_user),
) -> LLMConfigRead:
    """根据 ID 获取单个 LLM 配置"""
    config = await service.get_config_by_id(current_user.id, config_id)
    if not config:
        logger.warning("用户 %s 获取 LLM 配置失败，未找到 ID=%s", current_user.id, config_id)
        raise HTTPException(status_code=404, detail="未找到配置")
    logger.info("用户 %s 获取 LLM 配置 ID=%s", current_user.id, config_id)
    return config


@router.put("/{config_id}", response_model=LLMConfigRead)
async def update_llm_config(
    config_id: int,
    payload: LLMConfigUpdate,
    service: LLMConfigService = Depends(get_llm_config_service),
    current_user: UserInDB = Depends(get_current_user),
) -> LLMConfigRead:
    """更新 LLM 配置"""
    config = await service.update_config(current_user.id, config_id, payload)
    if not config:
        logger.warning("用户 %s 更新 LLM 配置失败，未找到 ID=%s", current_user.id, config_id)
        raise HTTPException(status_code=404, detail="未找到配置")
    logger.info("用户 %s 更新 LLM 配置 ID=%s", current_user.id, config_id)
    return config


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_llm_config(
    config_id: int,
    service: LLMConfigService = Depends(get_llm_config_service),
    current_user: UserInDB = Depends(get_current_user),
) -> None:
    """删除 LLM 配置"""
    deleted = await service.delete_config(current_user.id, config_id)
    if not deleted:
        logger.warning("用户 %s 删除 LLM 配置失败，未找到 ID=%s", current_user.id, config_id)
        raise HTTPException(status_code=404, detail="未找到配置")
    logger.info("用户 %s 删除 LLM 配置 ID=%s", current_user.id, config_id)


@router.put("/{config_id}/activate", response_model=LLMConfigRead)
async def activate_llm_config(
    config_id: int,
    service: LLMConfigService = Depends(get_llm_config_service),
    current_user: UserInDB = Depends(get_current_user),
) -> LLMConfigRead:
    """激活指定的 LLM 配置"""
    config = await service.activate_config(current_user.id, config_id)
    if not config:
        logger.warning("用户 %s 激活 LLM 配置失败，未找到 ID=%s", current_user.id, config_id)
        raise HTTPException(status_code=404, detail="未找到配置")
    logger.info("用户 %s 激活 LLM 配置 ID=%s", current_user.id, config_id)
    return config
