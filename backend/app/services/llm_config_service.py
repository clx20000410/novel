# AIMETA P=LLM配置服务_模型配置业务逻辑|R=配置管理_模型选择|NR=不含模型调用|E=LLMConfigService|X=internal|A=服务类|D=sqlalchemy|S=db|RD=./README.ai
import time
from typing import Optional, List
import logging
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import AsyncSession
from openai import AsyncOpenAI

from ..models import LLMConfig
from ..repositories.llm_config_repository import LLMConfigRepository
from ..repositories.system_config_repository import SystemConfigRepository
from ..schemas.llm_config import LLMConfigCreate, LLMConfigUpdate, LLMConfigRead
from ..utils.llm_tool import ChatMessage, create_llm_client, ApiFormatType


logger = logging.getLogger(__name__)


class LLMConfigService:
    """用户自定义 LLM 配置服务，支持多配置管理。"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = LLMConfigRepository(session)
        self.system_config_repo = SystemConfigRepository(session)

    def _identify_provider(self, base_url: Optional[str]) -> str:
        """根据 base_url 识别 LLM 提供商"""
        if not base_url:
            return "openai"

        url_lower = base_url.lower()
        parsed = urlparse(url_lower)
        host = parsed.netloc or parsed.path

        # 识别常见提供商
        if "openai.com" in host or "api.openai.com" in host:
            return "openai"
        elif "anthropic.com" in host or "api.anthropic.com" in host:
            return "anthropic"
        elif "generativelanguage.googleapis.com" in host or "google" in host:
            return "google"
        elif "azure" in host:
            return "azure"
        elif "cohere" in host:
            return "cohere"
        elif "together" in host or "together.ai" in host:
            return "together"
        elif "deepseek" in host:
            return "deepseek"
        elif "moonshot" in host:
            return "moonshot"
        elif "zhipu" in host or "bigmodel.cn" in host:
            return "zhipu"
        elif "baidu" in host or "qianfan" in host:
            return "baidu"
        else:
            # 默认使用 OpenAI-like API
            return "openai-like"

    def _build_url(self, base_url: Optional[str], default_url: str, path_suffix: str) -> str:
        """统一的 URL 构建逻辑，避免路径重复"""
        if base_url:
            url = base_url.rstrip('/')
            # 如果 URL 已经包含路径后缀，则直接使用
            if not url.endswith(path_suffix):
                url += path_suffix
        else:
            url = default_url
        return url

    # ==================== 多配置管理接口 ====================

    async def list_configs(self, user_id: int) -> List[LLMConfigRead]:
        """获取用户的所有配置列表"""
        configs = await self.repo.list_by_user(user_id)
        return [LLMConfigRead.model_validate(c) for c in configs]

    async def get_config_by_id(self, user_id: int, config_id: int) -> Optional[LLMConfigRead]:
        """根据 ID 获取单个配置"""
        config = await self.repo.get_by_id(config_id, user_id)
        return LLMConfigRead.model_validate(config) if config else None

    async def create_config(self, user_id: int, payload: LLMConfigCreate) -> LLMConfigRead:
        """创建新配置"""
        data = payload.model_dump(exclude_unset=True)
        if "llm_provider_url" in data and data["llm_provider_url"] is not None:
            data["llm_provider_url"] = str(data["llm_provider_url"])

        # 检查是否是用户的第一个配置，如果是则自动激活
        existing_count = await self.repo.count_by_user(user_id)
        is_first_config = existing_count == 0

        instance = LLMConfig(
            user_id=user_id,
            is_active=is_first_config,  # 第一个配置自动激活
            **data
        )
        await self.repo.add(instance)
        await self.session.commit()

        # 刷新实例以获取数据库生成的值（id, created_at, updated_at）
        await self.session.refresh(instance)

        logger.info("用户 %s 创建了新的 LLM 配置: %s (is_active=%s)", user_id, instance.name, is_first_config)
        return LLMConfigRead.model_validate(instance)

    async def update_config(self, user_id: int, config_id: int, payload: LLMConfigUpdate) -> Optional[LLMConfigRead]:
        """更新配置"""
        instance = await self.repo.get_by_id(config_id, user_id)
        if not instance:
            return None

        data = payload.model_dump(exclude_unset=True)
        if "llm_provider_url" in data and data["llm_provider_url"] is not None:
            data["llm_provider_url"] = str(data["llm_provider_url"])

        await self.repo.update_fields(instance, **data)
        await self.session.commit()

        # 刷新实例以获取最新的数据库值（updated_at）
        await self.session.refresh(instance)

        logger.info("用户 %s 更新了 LLM 配置 ID=%s", user_id, config_id)
        return LLMConfigRead.model_validate(instance)

    async def delete_config(self, user_id: int, config_id: int) -> bool:
        """删除配置"""
        instance = await self.repo.get_by_id(config_id, user_id)
        if not instance:
            return False

        was_active = instance.is_active
        await self.repo.delete(instance)
        await self.session.commit()

        # 如果删除的是激活配置，自动激活下一个配置
        if was_active:
            remaining_configs = await self.repo.list_by_user(user_id)
            if remaining_configs:
                next_config = remaining_configs[0]
                next_config.is_active = True
                await self.session.commit()
                logger.info("用户 %s 删除了激活配置，自动激活了配置 ID=%s", user_id, next_config.id)

        logger.info("用户 %s 删除了 LLM 配置 ID=%s", user_id, config_id)
        return True

    async def activate_config(self, user_id: int, config_id: int) -> Optional[LLMConfigRead]:
        """激活指定配置（同时取消其他配置的激活状态）"""
        instance = await self.repo.get_by_id(config_id, user_id)
        if not instance:
            return None

        # 先取消所有配置的激活状态
        await self.repo.deactivate_all(user_id)

        # 激活目标配置
        instance.is_active = True
        await self.session.commit()

        # 刷新实例以获取最新的数据库值（包括 updated_at）
        await self.session.refresh(instance)

        logger.info("用户 %s 激活了 LLM 配置 ID=%s", user_id, config_id)
        return LLMConfigRead.model_validate(instance)

    async def get_active_config(self, user_id: int) -> Optional[LLMConfigRead]:
        """获取当前激活的配置"""
        config = await self.repo.get_active_config(user_id)
        return LLMConfigRead.model_validate(config) if config else None

    # ==================== 兼容旧接口 ====================

    async def upsert_config(self, user_id: int, payload: LLMConfigCreate) -> LLMConfigRead:
        """兼容旧接口：创建或更新配置（操作激活配置）"""
        active_config = await self.repo.get_active_config(user_id)
        if active_config:
            # 更新激活配置
            update_payload = LLMConfigUpdate(
                name=payload.name if hasattr(payload, 'name') else None,
                llm_provider_url=payload.llm_provider_url,
                llm_provider_api_key=payload.llm_provider_api_key,
                llm_provider_model=payload.llm_provider_model,
            )
            return await self.update_config(user_id, active_config.id, update_payload)  # type: ignore
        else:
            # 创建新配置
            return await self.create_config(user_id, payload)

    async def get_config(self, user_id: int) -> Optional[LLMConfigRead]:
        """兼容旧接口：获取激活配置"""
        return await self.get_active_config(user_id)

    # ==================== 连接测试 ====================

    async def test_connection(
        self,
        api_format: ApiFormatType,
        api_key: str,
        base_url: Optional[str],
        model: str,
    ) -> dict:
        """测试 LLM 连接

        Args:
            api_format: API 格式类型
            api_key: API 密钥
            base_url: API 基础 URL
            model: 模型名称

        Returns:
            包含 success, latency_ms, message 的字典
        """
        start = time.time()
        try:
            client = create_llm_client(api_format, api_key, base_url)
            messages = [ChatMessage(role="user", content="Hi")]
            response = ""

            async for part in client.stream_chat(
                messages,
                model=model,
                max_tokens=5,
                timeout=15.0,
            ):
                if part.get("content"):
                    response += part["content"]
                if part.get("finish_reason"):
                    break

            latency = round((time.time() - start) * 1000)
            logger.info(
                "连接测试成功: api_format=%s model=%s latency=%dms response_preview=%s",
                api_format, model, latency, response[:50] if response else "(empty)"
            )
            return {
                "success": True,
                "latency_ms": latency,
                "message": f"连接成功 ({latency}ms)"
            }
        except Exception as e:
            latency = round((time.time() - start) * 1000)
            error_msg = str(e)

            # 提取更友好的错误信息
            if "401" in error_msg or "Unauthorized" in error_msg.lower() or "invalid_api_key" in error_msg.lower():
                friendly_msg = "API Key 无效或已过期"
            elif "404" in error_msg or "Not Found" in error_msg:
                friendly_msg = "API 端点不存在，请检查 URL 和模型名称"
            elif "Connection" in error_msg or "connect" in error_msg.lower():
                friendly_msg = "无法连接到服务器，请检查网络和 URL"
            elif "timeout" in error_msg.lower():
                friendly_msg = "连接超时，请稍后重试"
            else:
                friendly_msg = error_msg[:200] if len(error_msg) > 200 else error_msg

            logger.warning(
                "连接测试失败: api_format=%s model=%s latency=%dms error=%s",
                api_format, model, latency, error_msg
            )
            return {
                "success": False,
                "latency_ms": latency,
                "message": friendly_msg
            }

    # ==================== 模型列表获取 ====================

    async def get_available_models(
        self, api_key: str, base_url: Optional[str] = None, api_format: ApiFormatType = "openai_chat"
    ) -> List[str]:
        """使用指定的凭证获取可用的模型列表

        Args:
            api_key: API 密钥
            base_url: API 基础 URL
            api_format: API 格式类型

        Returns:
            模型名称列表
        """
        if not api_key:
            logger.warning("获取模型列表失败：未提供 API Key")
            return []

        logger.info("获取模型列表: api_format=%s base_url=%s", api_format, base_url)

        try:
            # 根据 api_format 选择获取模型列表的方法
            if api_format == "anthropic":
                return await self._get_anthropic_models(api_key, base_url)
            elif api_format == "google":
                return await self._get_google_models(api_key, base_url)
            elif api_format in ("openai_chat", "openai_responses"):
                return await self._get_openai_like_models(api_key, base_url)
            else:
                # 回退到基于 URL 的识别
                provider = self._identify_provider(base_url)
                if provider == "anthropic":
                    return await self._get_anthropic_models(api_key, base_url)
                elif provider == "google":
                    return await self._get_google_models(api_key, base_url)
                elif provider == "azure":
                    return await self._get_azure_models(api_key, base_url)
                elif provider == "cohere":
                    return await self._get_cohere_models(api_key, base_url)
                else:
                    return await self._get_openai_like_models(api_key, base_url)
        except Exception as e:
            error_msg = str(e)
            logger.error("获取模型列表失败: api_format=%s, error=%s", api_format, error_msg, exc_info=True)

            # 提供更友好的错误信息
            if "Connection error" in error_msg or "disconnected" in error_msg.lower():
                logger.warning("连接错误，可能是 API URL 配置错误或网络问题")
            elif "401" in error_msg or "Unauthorized" in error_msg:
                logger.warning("认证失败，请检查 API Key 是否正确")
            elif "404" in error_msg or "Not Found" in error_msg:
                logger.warning("API 端点不存在，请检查 URL 是否正确")

            return []

    async def _get_openai_like_models(self, api_key: str, base_url: Optional[str]) -> List[str]:
        """获取 OpenAI 或 OpenAI-like API 的模型列表"""
        import httpx
        from openai import APIConnectionError, APIError

        try:
            # 创建带有超时和重试配置的客户端
            client = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=httpx.Timeout(30.0, connect=10.0),
                max_retries=2,
            )

            logger.info("尝试获取模型列表: base_url=%s", base_url)
            models_response = await client.models.list()
            model_ids = [model.id for model in models_response.data]
            logger.info("成功获取 %d 个 OpenAI-like 模型", len(model_ids))
            return sorted(model_ids)

        except APIConnectionError as e:
            logger.error("API 连接错误: %s", str(e), exc_info=True)
            # 某些自建服务可能不支持 /v1/models 端点，尝试使用 httpx 直接请求
            return await self._get_models_via_http(api_key, base_url)

        except APIError as e:
            logger.error("API 调用错误: status_code=%s, message=%s", getattr(e, 'status_code', 'unknown'), str(e))
            return await self._get_models_via_http(api_key, base_url)

        except Exception as e:
            logger.error("获取 OpenAI-like 模型列表失败: %s", str(e), exc_info=True)
            return await self._get_models_via_http(api_key, base_url)

    async def _get_models_via_http(self, api_key: str, base_url: Optional[str]) -> List[str]:
        """使用 httpx 直接请求模型列表（备选方案）"""
        import httpx

        try:
            # 构建完整的 URL
            if base_url:
                url = base_url.rstrip('/') + '/models'
            else:
                url = 'https://api.openai.com/v1/models'

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            logger.info("使用 HTTP 直接请求模型列表: url=%s", url)

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)

                logger.info("HTTP 响应状态码: %d", response.status_code)

                if response.status_code == 200:
                    data = response.json()
                    models = data.get('data', [])
                    model_ids = [model.get('id') for model in models if model.get('id')]
                    logger.info("通过 HTTP 成功获取 %d 个模型", len(model_ids))
                    return sorted(model_ids)
                elif response.status_code == 404:
                    logger.warning("模型列表端点不存在 (404)，该服务可能不支持模型列表查询")
                    return []
                elif response.status_code == 401:
                    logger.warning("认证失败 (401)，请检查 API Key 是否正确")
                    return []
                else:
                    logger.warning("HTTP 请求失败: status=%d, body=%s", response.status_code, response.text[:200])
                    return []

        except httpx.TimeoutException:
            logger.error("HTTP 请求超时")
            return []
        except httpx.ConnectError as e:
            logger.error("无法连接到服务器: %s", str(e))
            return []
        except Exception as e:
            logger.error("HTTP 请求失败: %s", str(e), exc_info=True)
            return []

    async def _get_anthropic_models(self, api_key: str, base_url: Optional[str]) -> List[str]:
        """获取 Anthropic 的模型列表"""
        # Anthropic 目前不提供模型列表 API，返回常用模型
        logger.info("返回 Anthropic 预定义模型列表")
        return [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]

    async def _get_google_models(self, api_key: str, base_url: Optional[str]) -> List[str]:
        """获取 Google Gemini 的模型列表"""
        import httpx

        try:
            # 使用统一的 URL 构建方法
            url = self._build_url(
                base_url,
                "https://generativelanguage.googleapis.com/v1beta",
                "/v1beta"
            )
            url += f"/models?key={api_key}"

            logger.info("请求 Google 模型列表: url=%s", url.replace(api_key, "***"))

            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30.0)

                logger.info("HTTP 响应状态码: %d", response.status_code)
                response.raise_for_status()
                data = response.json()

                model_ids = []
                for model in data.get("models", []):
                    model_name = model.get("name", "")
                    # 移除 "models/" 前缀
                    if model_name.startswith("models/"):
                        model_name = model_name[7:]
                    # 只返回生成模型（非 embedding 模型）
                    if "generateContent" in model.get("supportedGenerationMethods", []):
                        model_ids.append(model_name)

                logger.info("成功获取 %d 个 Google 模型", len(model_ids))
                return sorted(model_ids)
        except httpx.HTTPStatusError as e:
            logger.error("Google API HTTP 错误: status=%d, message=%s", e.response.status_code, str(e))
            # 返回常用的 Gemini 模型作为备选
            return [
                "gemini-2.0-flash-exp",
                "gemini-1.5-pro",
                "gemini-1.5-flash",
                "gemini-1.0-pro",
            ]
        except httpx.TimeoutException:
            logger.error("Google API 请求超时")
            return [
                "gemini-2.0-flash-exp",
                "gemini-1.5-pro",
                "gemini-1.5-flash",
                "gemini-1.0-pro",
            ]
        except Exception as e:
            logger.error("获取 Google 模型列表失败: %s", str(e), exc_info=True)
            # 返回常用的 Gemini 模型作为备选
            return [
                "gemini-2.0-flash-exp",
                "gemini-1.5-pro",
                "gemini-1.5-flash",
                "gemini-1.0-pro",
            ]

    async def _get_azure_models(self, api_key: str, base_url: Optional[str]) -> List[str]:
        """获取 Azure OpenAI 的模型列表"""
        # Azure OpenAI 的部署是用户自定义的，无法直接列举
        # 返回常见的 Azure OpenAI 模型名称
        logger.info("返回 Azure OpenAI 预定义模型列表")
        return [
            "gpt-4",
            "gpt-4-32k",
            "gpt-4-turbo",
            "gpt-4o",
            "gpt-35-turbo",
            "gpt-35-turbo-16k",
        ]

    async def _get_cohere_models(self, api_key: str, base_url: Optional[str]) -> List[str]:
        """获取 Cohere 的模型列表"""
        import httpx

        try:
            # 使用统一的 URL 构建方法
            url = self._build_url(
                base_url,
                "https://api.cohere.ai/v1",
                "/v1"
            )
            url += "/models"

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            logger.info("请求 Cohere 模型列表: url=%s", url)

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=30.0)

                logger.info("HTTP 响应状态码: %d", response.status_code)
                response.raise_for_status()
                data = response.json()

                model_ids = [model.get("name") for model in data.get("models", []) if model.get("name")]
                logger.info("成功获取 %d 个 Cohere 模型", len(model_ids))
                return sorted(model_ids)
        except httpx.HTTPStatusError as e:
            logger.error("Cohere API HTTP 错误: status=%d, message=%s", e.response.status_code, str(e))
            return [
                "command-r-plus",
                "command-r",
                "command",
                "command-light",
            ]
        except httpx.TimeoutException:
            logger.error("Cohere API 请求超时")
            return [
                "command-r-plus",
                "command-r",
                "command",
                "command-light",
            ]
        except Exception as e:
            logger.error("获取 Cohere 模型列表失败: %s", str(e), exc_info=True)
            # 返回常用的 Cohere 模型作为备选
            return [
                "command-r-plus",
                "command-r",
                "command",
                "command-light",
            ]
