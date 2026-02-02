# AIMETA P=LLM服务_大模型调用封装|R=API调用_流式生成|NR=不含业务逻辑|E=LLMService|X=internal|A=服务类|D=openai,httpx|S=net|RD=./README.ai
import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException, status
from openai import APIConnectionError, APIError, APIStatusError, APITimeoutError, AsyncOpenAI, InternalServerError

from ..core.config import settings
from ..repositories.llm_config_repository import LLMConfigRepository
from ..repositories.system_config_repository import SystemConfigRepository
from ..repositories.user_repository import UserRepository
from ..services.admin_setting_service import AdminSettingService
from ..services.prompt_service import PromptService
from ..services.usage_service import UsageService
from ..utils.llm_tool import ChatMessage, LLMClient, create_llm_client

logger = logging.getLogger(__name__)

try:  # pragma: no cover - 运行环境未安装时兼容
    from ollama import AsyncClient as OllamaAsyncClient
except ImportError:  # pragma: no cover - Ollama 为可选依赖
    OllamaAsyncClient = None


class LLMService:
    """封装与大模型交互的所有逻辑，包括配额控制与配置选择。"""

    def __init__(self, session):
        self.session = session
        self.llm_repo = LLMConfigRepository(session)
        self.system_config_repo = SystemConfigRepository(session)
        self.user_repo = UserRepository(session)
        self.admin_setting_service = AdminSettingService(session)
        self.usage_service = UsageService(session)
        self._embedding_dimensions: Dict[str, int] = {}

    async def get_llm_response(
        self,
        system_prompt: str,
        conversation_history: List[Dict[str, str]],
        *,
        temperature: float = 0.7,
        user_id: Optional[int] = None,
        timeout: float = 3600.0,
        response_format: Optional[str] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
    ) -> str:
        messages = [{"role": "system", "content": system_prompt}, *conversation_history]
        return await self._stream_and_collect(
            messages,
            temperature=temperature,
            user_id=user_id,
            timeout=timeout,
            response_format=response_format,
            max_tokens=max_tokens,
            top_p=top_p,
        )

    async def generate(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        user_id: Optional[int] = None,
        timeout: float = 3600.0,
        max_tokens: Optional[int] = None,
        response_format: Optional[str] = None,
        top_p: Optional[float] = None,
    ) -> str:
        """兼容旧版接口的文本生成入口，统一走 get_llm_response。"""
        return await self.get_llm_response(
            system_prompt=system_prompt or "你是一位专业写作助手。",
            conversation_history=[{"role": "user", "content": prompt}],
            temperature=temperature,
            user_id=user_id,
            timeout=timeout,
            response_format=response_format,
            max_tokens=max_tokens,
            top_p=top_p,
        )

    async def get_summary(
        self,
        chapter_content: str,
        *,
        temperature: float = 0.2,
        user_id: Optional[int] = None,
        timeout: float = 3600.0,
        system_prompt: Optional[str] = None,
    ) -> str:
        if not system_prompt:
            prompt_service = PromptService(self.session)
            system_prompt = await prompt_service.get_prompt("extraction")
        if not system_prompt:
            logger.error("未配置名为 'extraction' 的摘要提示词，无法生成章节摘要")
            raise HTTPException(status_code=500, detail="未配置摘要提示词，请联系管理员配置 'extraction' 提示词")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": chapter_content},
        ]
        return await self._stream_and_collect(messages, temperature=temperature, user_id=user_id, timeout=timeout)

    async def _stream_and_collect(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: float,
        user_id: Optional[int],
        timeout: float,
        response_format: Optional[str] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
    ) -> str:
        config = await self._resolve_llm_config(user_id)
        api_format = config.get("api_format", "openai_responses")
        client = create_llm_client(api_format, api_key=config["api_key"], base_url=config.get("base_url"))

        chat_messages = [ChatMessage(role=msg["role"], content=msg["content"]) for msg in messages]

        def _is_connect_timeout(exc: BaseException) -> bool:
            current: BaseException | None = exc
            visited: set[int] = set()
            while current is not None and id(current) not in visited:
                visited.add(id(current))
                if isinstance(current, httpx.ConnectTimeout):
                    return True
                current = current.__cause__ or current.__context__
            return False

        read_timeout_seconds = min(float(timeout), settings.llm_stream_read_timeout_seconds)
        logger.info(
            "Streaming LLM response: model=%s user_id=%s messages=%d timeout=%.1fs connect_timeout=%.1fs read_timeout=%.1fs retries=%d base_url=%s",
            config.get("model"),
            user_id,
            len(messages),
            float(timeout),
            settings.llm_stream_connect_timeout_seconds,
            read_timeout_seconds,
            settings.llm_stream_max_retries,
            client.base_url or "<default>",
        )

        full_response = ""
        finish_reason = None
        retryable_exceptions = (
            httpx.RemoteProtocolError,
            httpx.ReadTimeout,
            httpx.ConnectTimeout,
            APIConnectionError,
            APITimeoutError,
            TimeoutError,
        )
        total_attempts = max(1, settings.llm_stream_max_retries + 1)
        request_timeout = httpx.Timeout(
            read_timeout_seconds,
            connect=settings.llm_stream_connect_timeout_seconds,
        )

        for attempt in range(1, total_attempts + 1):
            full_response = ""
            finish_reason = None
            try:
                async with asyncio.timeout(timeout):
                    async for part in client.stream_chat(
                        messages=chat_messages,
                        model=config.get("model"),
                        temperature=temperature,
                        timeout=request_timeout,
                        response_format=response_format,
                        max_tokens=max_tokens,
                        top_p=top_p,
                    ):
                        if part.get("content"):
                            full_response += part["content"]
                        if part.get("finish_reason"):
                            finish_reason = part["finish_reason"]

                # 检查空响应，支持重试
                if not full_response and attempt < total_attempts:
                    backoff_seconds = min(1.0 * (2 ** (attempt - 1)), 8.0)
                    logger.warning(
                        "LLM returned empty response, retrying: attempt=%d/%d model=%s user_id=%s finish_reason=%s backoff=%.2fs",
                        attempt,
                        total_attempts,
                        config.get("model"),
                        user_id,
                        finish_reason,
                        backoff_seconds,
                    )
                    await asyncio.sleep(backoff_seconds)
                    continue

                break
            except InternalServerError as exc:
                detail = "AI 服务内部错误，请稍后重试"
                response = getattr(exc, "response", None)
                if response is not None:
                    try:
                        payload = response.json()
                        error_data = payload.get("error", {}) if isinstance(payload, dict) else {}
                        detail = error_data.get("message_zh") or error_data.get("message") or detail
                    except Exception:
                        detail = str(exc) or detail
                else:
                    detail = str(exc) or detail

                # InternalServerError (500) 支持重试
                if attempt < total_attempts:
                    backoff_seconds = min(1.0 * (2 ** (attempt - 1)), 8.0)
                    logger.warning(
                        "LLM stream internal error, retrying: attempt=%d/%d model=%s user_id=%s detail=%s backoff=%.2fs",
                        attempt,
                        total_attempts,
                        config.get("model"),
                        user_id,
                        detail,
                        backoff_seconds,
                        exc_info=exc,
                    )
                    await asyncio.sleep(backoff_seconds)
                    continue

                logger.error(
                    "LLM stream internal error: model=%s user_id=%s detail=%s",
                    config.get("model"),
                    user_id,
                    detail,
                    exc_info=exc,
                )
                raise HTTPException(status_code=503, detail=detail)
            except APIStatusError as exc:
                detail = "AI 服务返回错误，请检查模型配置"
                response = getattr(exc, "response", None)
                if response is not None:
                    try:
                        payload = response.json()
                        error_data = payload.get("error", {}) if isinstance(payload, dict) else {}
                        detail = error_data.get("message_zh") or error_data.get("message") or detail
                    except Exception:
                        content_type = (response.headers.get("content-type") or "").lower()
                        text = (response.text or "").strip()
                        is_html = (
                            "text/html" in content_type
                            or text.lower().startswith("<!doctype html")
                            or text.lower().startswith("<html")
                        )
                        if is_html:
                            ray_id = None
                            lower_text = text.lower()
                            if "cloudflare ray id" in lower_text:
                                import re

                                match = re.search(r"cloudflare ray id:\\s*<strong[^>]*>([^<]+)", text, re.I)
                                if match:
                                    ray_id = match.group(1).strip()

                            if exc.status_code == 502:
                                detail = "AI 服务网关返回 502 Bad Gateway（上游不可用），请稍后重试或更换 Base URL"
                            else:
                                detail = f"AI 服务网关返回 {exc.status_code} 错误，请稍后重试或更换 Base URL"

                            if ray_id:
                                detail = f"{detail}（Ray ID: {ray_id}）"
                        else:
                            detail = str(exc) or detail
                else:
                    detail = str(exc) or detail

                if exc.status_code == 404:
                    detail = "AI 服务接口不存在，请确认 Base URL 支持 /v1/responses"
                elif exc.status_code in {401, 403}:
                    detail = "AI 服务认证失败，请检查 API Key 是否正确"
                elif exc.status_code == 400:
                    detail = "AI 服务请求参数不兼容，请检查模型/接口兼容性"
                elif exc.status_code == 429:
                    detail = "AI 服务请求频率限制，请稍后重试"

                # 所有 5xx 错误和 429 (rate limit) 都支持重试
                if (exc.status_code >= 500 or exc.status_code == 429) and attempt < total_attempts:
                    backoff_seconds = min(1.0 * (2 ** (attempt - 1)), 8.0)
                    logger.warning(
                        "LLM stream status error, retrying: attempt=%d/%d status=%s model=%s user_id=%s detail=%s backoff=%.2fs",
                        attempt,
                        total_attempts,
                        exc.status_code,
                        config.get("model"),
                        user_id,
                        detail,
                        backoff_seconds,
                        exc_info=exc,
                    )
                    await asyncio.sleep(backoff_seconds)
                    continue

                logger.error(
                    "LLM stream status error: status=%s model=%s user_id=%s detail=%s",
                    exc.status_code,
                    config.get("model"),
                    user_id,
                    detail,
                    exc_info=exc,
                )
                raise HTTPException(status_code=503, detail=detail) from exc
            except APIError as exc:
                # APIError 也支持重试
                if attempt < total_attempts:
                    backoff_seconds = min(1.0 * (2 ** (attempt - 1)), 8.0)
                    logger.warning(
                        "LLM stream API error, retrying: attempt=%d/%d model=%s user_id=%s detail=%s backoff=%.2fs",
                        attempt,
                        total_attempts,
                        config.get("model"),
                        user_id,
                        str(exc) or "unknown",
                        backoff_seconds,
                        exc_info=exc,
                    )
                    await asyncio.sleep(backoff_seconds)
                    continue

                logger.error(
                    "LLM stream API error: model=%s user_id=%s detail=%s",
                    config.get("model"),
                    user_id,
                    str(exc) or "unknown",
                    exc_info=exc,
                )
                raise HTTPException(status_code=503, detail="AI 服务返回异常，请稍后重试") from exc
            except httpx.HTTPStatusError as exc:
                # 处理 httpx 客户端（如 AnthropicClient、GoogleClient）抛出的 HTTP 错误
                status_code = exc.response.status_code
                detail = f"AI 服务返回 {status_code} 错误"
                try:
                    payload = exc.response.json()
                    if isinstance(payload, dict):
                        # Anthropic 错误格式
                        error_data = payload.get("error", {})
                        if isinstance(error_data, dict):
                            detail = error_data.get("message") or detail
                        # Google 错误格式
                        elif "error" in payload and isinstance(payload["error"], dict):
                            detail = payload["error"].get("message") or detail
                except Exception:
                    detail = str(exc) or detail

                if status_code == 401:
                    detail = "AI 服务认证失败，请检查 API Key 是否正确"
                elif status_code == 403:
                    detail = "AI 服务拒绝访问，请检查 API Key 权限"
                elif status_code == 404:
                    detail = "AI 服务接口不存在，请检查 Base URL 和模型名称"
                elif status_code == 429:
                    detail = "AI 服务请求频率限制，请稍后重试"
                elif status_code >= 500:
                    detail = f"AI 服务内部错误 ({status_code})，请稍后重试或更换服务"

                # 5xx 错误和 429 (rate limit) 支持重试
                if (status_code >= 500 or status_code == 429) and attempt < total_attempts:
                    backoff_seconds = min(1.0 * (2 ** (attempt - 1)), 8.0)
                    logger.warning(
                        "LLM stream HTTP error, retrying: attempt=%d/%d status=%s model=%s user_id=%s detail=%s backoff=%.2fs",
                        attempt,
                        total_attempts,
                        status_code,
                        config.get("model"),
                        user_id,
                        detail,
                        backoff_seconds,
                        exc_info=exc,
                    )
                    await asyncio.sleep(backoff_seconds)
                    continue

                logger.error(
                    "LLM stream HTTP error: status=%s model=%s user_id=%s detail=%s",
                    status_code,
                    config.get("model"),
                    user_id,
                    detail,
                    exc_info=exc,
                )
                raise HTTPException(status_code=503, detail=detail) from exc
            except retryable_exceptions as exc:
                partial_chars = len(full_response)
                if isinstance(exc, httpx.RemoteProtocolError):
                    detail = "AI 服务连接被意外中断，请稍后重试"
                elif isinstance(exc, httpx.ConnectTimeout) or _is_connect_timeout(exc):
                    detail = "AI 服务连接超时，请检查服务地址或网络代理"
                elif isinstance(exc, httpx.ReadTimeout):
                    detail = (
                        f"AI 服务超过 {read_timeout_seconds:.0f} 秒无输出（已生成 {partial_chars} 字符），"
                        "请提高 LLM_STREAM_READ_TIMEOUT_SECONDS 或更换更稳定的服务/模型"
                    )
                elif isinstance(exc, TimeoutError):
                    detail = (
                        f"AI 生成超过 {float(timeout):.0f} 秒未完成（已生成 {partial_chars} 字符），"
                        "请提高超时、减少输入长度或更换更快的模型"
                    )
                elif isinstance(exc, APITimeoutError):
                    detail = "AI 服务响应超时，请稍后重试"
                else:
                    detail = "无法连接到 AI 服务，请稍后重试"

                should_retry = attempt < total_attempts
                if isinstance(exc, TimeoutError) and partial_chars > 0:
                    should_retry = False

                if should_retry:
                    backoff_seconds = min(0.5 * (2 ** (attempt - 1)), 4.0)
                    logger.warning(
                        "LLM stream failed, retrying: attempt=%d/%d model=%s user_id=%s detail=%s partial_chars=%d backoff=%.2fs",
                        attempt,
                        total_attempts,
                        config.get("model"),
                        user_id,
                        detail,
                        partial_chars,
                        backoff_seconds,
                        exc_info=exc,
                    )
                    await asyncio.sleep(backoff_seconds)
                    continue

                logger.error(
                    "LLM stream failed: model=%s user_id=%s detail=%s partial_chars=%d",
                    config.get("model"),
                    user_id,
                    detail,
                    partial_chars,
                    exc_info=exc,
                )
                raise HTTPException(status_code=503, detail=detail) from exc

        logger.debug(
            "LLM response collected: model=%s user_id=%s finish_reason=%s preview=%s",
            config.get("model"),
            user_id,
            finish_reason,
            full_response[:500],
        )

        if finish_reason == "length":
            logger.warning(
                "LLM response truncated: model=%s user_id=%s response_length=%d",
                config.get("model"),
                user_id,
                len(full_response),
            )
            raise HTTPException(
                status_code=500,
                detail=f"AI 响应因长度限制被截断（已生成 {len(full_response)} 字符），请缩短输入内容或调整模型参数"
            )

        if not full_response:
            logger.error(
                "LLM returned empty response: model=%s user_id=%s finish_reason=%s",
                config.get("model"),
                user_id,
                finish_reason,
            )
            raise HTTPException(
                status_code=500,
                detail=f"AI 未返回有效内容（结束原因: {finish_reason or '未知'}），请稍后重试或联系管理员"
            )

        await self.usage_service.increment("api_request_count")
        logger.info(
            "LLM response success: model=%s user_id=%s chars=%d",
            config.get("model"),
            user_id,
            len(full_response),
        )
        return full_response

    async def _resolve_llm_config(self, user_id: Optional[int]) -> Dict[str, Optional[str]]:
        if user_id:
            config = await self.llm_repo.get_by_user(user_id)
            if config and config.llm_provider_api_key:
                return {
                    "api_key": config.llm_provider_api_key,
                    "base_url": config.llm_provider_url,
                    "model": config.llm_provider_model,
                    "api_format": getattr(config, "api_format", "openai_responses"),
                }

        # 检查每日使用次数限制
        if user_id:
            await self._enforce_daily_limit(user_id)

        api_key = await self._get_config_value("llm.api_key")
        base_url = await self._get_config_value("llm.base_url")
        model = await self._get_config_value("llm.model")
        api_format = await self._get_config_value("llm.api_format") or "openai_responses"

        if not api_key:
            logger.error("未配置默认 LLM API Key，且用户 %s 未设置自定义 API Key", user_id)
            raise HTTPException(
                status_code=500,
                detail="未配置默认 LLM API Key，请联系管理员配置系统默认 API Key 或在个人设置中配置自定义 API Key"
            )

        return {"api_key": api_key, "base_url": base_url, "model": model, "api_format": api_format}

    async def get_embedding(
        self,
        text: str,
        *,
        user_id: Optional[int] = None,
        model: Optional[str] = None,
    ) -> List[float]:
        """生成文本向量，用于章节 RAG 检索，支持 openai 与 ollama 双提供方。"""
        provider = await self._get_config_value("embedding.provider") or "openai"
        default_model = (
            await self._get_config_value("ollama.embedding_model") or "nomic-embed-text:latest"
            if provider == "ollama"
            else await self._get_config_value("embedding.model") or "text-embedding-3-large"
        )
        target_model = model or default_model

        if provider == "ollama":
            if OllamaAsyncClient is None:
                logger.error("未安装 ollama 依赖，无法调用本地嵌入模型。")
                raise HTTPException(status_code=500, detail="缺少 Ollama 依赖，请先安装 ollama 包。")

            base_url = (
                await self._get_config_value("ollama.embedding_base_url")
                or await self._get_config_value("embedding.base_url")
            )
            client = OllamaAsyncClient(host=base_url)
            try:
                response = await client.embeddings(model=target_model, prompt=text)
            except Exception as exc:  # pragma: no cover - 本地服务调用失败
                logger.error(
                    "Ollama 嵌入请求失败: model=%s base_url=%s error=%s",
                    target_model,
                    base_url,
                    exc,
                    exc_info=True,
                )
                return []
            embedding: Optional[List[float]]
            if isinstance(response, dict):
                embedding = response.get("embedding")
            else:
                embedding = getattr(response, "embedding", None)
            if not embedding:
                logger.warning("Ollama 返回空向量: model=%s", target_model)
                return []
            if not isinstance(embedding, list):
                embedding = list(embedding)
        else:
            config = await self._resolve_llm_config(user_id)
            api_key = await self._get_config_value("embedding.api_key") or config["api_key"]
            base_url = await self._get_config_value("embedding.base_url") or config.get("base_url")
            client = AsyncOpenAI(api_key=api_key, base_url=base_url)
            try:
                response = await client.embeddings.create(
                    input=text,
                    model=target_model,
                )
            except Exception as exc:  # pragma: no cover - 网络或鉴权失败
                logger.error(
                    "OpenAI 嵌入请求失败: model=%s base_url=%s user_id=%s error=%s",
                    target_model,
                    base_url,
                    user_id,
                    exc,
                    exc_info=True,
                )
                return []
            if not response.data:
                logger.warning("OpenAI 嵌入请求返回空数据: model=%s user_id=%s", target_model, user_id)
                return []
            embedding = response.data[0].embedding

        if not isinstance(embedding, list):
            embedding = list(embedding)

        dimension = len(embedding)
        if not dimension:
            vector_size_str = await self._get_config_value("embedding.model_vector_size")
            if vector_size_str:
                dimension = int(vector_size_str)
        if dimension:
            self._embedding_dimensions[target_model] = dimension
        return embedding

    async def get_embedding_dimension(self, model: Optional[str] = None) -> Optional[int]:
        """获取嵌入向量维度，优先返回缓存结果，其次读取配置。"""
        provider = await self._get_config_value("embedding.provider") or "openai"
        default_model = (
            await self._get_config_value("ollama.embedding_model") or "nomic-embed-text:latest"
            if provider == "ollama"
            else await self._get_config_value("embedding.model") or "text-embedding-3-large"
        )
        target_model = model or default_model
        if target_model in self._embedding_dimensions:
            return self._embedding_dimensions[target_model]
        vector_size_str = await self._get_config_value("embedding.model_vector_size")
        return int(vector_size_str) if vector_size_str else None

    async def _enforce_daily_limit(self, user_id: int) -> None:
        limit_str = await self.admin_setting_service.get("daily_request_limit", "100")
        limit = int(limit_str or 10)
        used = await self.user_repo.get_daily_request(user_id)
        if used >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="今日请求次数已达上限，请明日再试或设置自定义 API Key。",
            )
        await self.user_repo.increment_daily_request(user_id)
        await self.session.commit()

    async def _get_config_value(self, key: str) -> Optional[str]:
        record = await self.system_config_repo.get_by_key(key)
        if record:
            return record.value
        # 兼容环境变量，首次迁移时无需立即写入数据库
        env_key = key.upper().replace(".", "_")
        return os.getenv(env_key)
