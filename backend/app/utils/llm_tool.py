# -*- coding: utf-8 -*-
# AIMETA P=LLM工具_大模型调用辅助|R=请求构建_响应解析|NR=不含业务逻辑|E=LLMTool|X=internal|A=工具类|D=httpx|S=net|RD=./README.ai
"""多格式 LLM 工具封装，支持 OpenAI Chat/Responses、Anthropic、Google API。"""

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator, Dict, List, Optional, Any, Literal

import httpx
from openai import AsyncOpenAI


ApiFormatType = Literal["openai_chat", "openai_responses", "anthropic", "google"]


@dataclass
class ChatMessage:
    role: str
    content: str

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


class BaseLLMClient(ABC):
    """LLM 客户端基类，定义统一接口。"""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    async def stream_chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: float | httpx.Timeout | None = None,
        **kwargs,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式调用 LLM API，逐块 yield {"content": ..., "finish_reason": ...}。"""
        pass


class OpenAIChatClient(BaseLLMClient):
    """OpenAI Chat Completions API 客户端（/v1/chat/completions）。"""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise ValueError("缺少 OPENAI_API_KEY 配置，请在数据库或环境变量中补全。")

        resolved_base_url = (
            base_url
            or os.environ.get("OPENAI_API_BASE_URL")
            or os.environ.get("OPENAI_BASE_URL")
            or os.environ.get("OPENAI_API_BASE")
        )
        super().__init__(key, resolved_base_url)
        self._client = AsyncOpenAI(api_key=key, base_url=resolved_base_url)

    async def stream_chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        response_format: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: float | httpx.Timeout | None = None,
        **kwargs,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式调用 Chat Completions API。"""

        request_body: Dict[str, Any] = {
            "model": model or os.environ.get("MODEL", "gpt-4o"),
            "messages": [msg.to_dict() for msg in messages],
            "stream": True,
        }

        if response_format:
            request_body["response_format"] = {"type": response_format}

        if temperature is not None:
            request_body["temperature"] = temperature
        if top_p is not None:
            request_body["top_p"] = top_p
        if max_tokens is not None:
            request_body["max_tokens"] = max_tokens

        stream = await self._client.chat.completions.create(**request_body, timeout=timeout)

        async for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                choice = chunk.choices[0]
                delta = choice.delta
                content = delta.content if delta else ""
                finish_reason = choice.finish_reason

                if content:
                    yield {"content": content, "finish_reason": None}

                if finish_reason:
                    yield {"content": "", "finish_reason": finish_reason}


class OpenAIResponsesClient(BaseLLMClient):
    """OpenAI Responses API 客户端（/v1/responses）。"""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise ValueError("缺少 OPENAI_API_KEY 配置，请在数据库或环境变量中补全。")

        resolved_base_url = (
            base_url
            or os.environ.get("OPENAI_API_BASE_URL")
            or os.environ.get("OPENAI_BASE_URL")
            or os.environ.get("OPENAI_API_BASE")
        )
        super().__init__(key, resolved_base_url)
        self._client = AsyncOpenAI(api_key=key, base_url=resolved_base_url)

    async def stream_chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        response_format: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: float | httpx.Timeout | None = None,
        **kwargs,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式调用 Responses API，逐块 yield {"content": ..., "finish_reason": ...}。"""

        # 分离 system/developer 消息作为 instructions，其余作为 input
        instructions_parts: List[str] = []
        input_messages: List[Dict[str, str]] = []

        for msg in messages:
            if msg.role in {"system", "developer"} and not input_messages:
                if msg.content:
                    instructions_parts.append(msg.content)
            else:
                input_messages.append(msg.to_dict())

        request_body: Dict[str, Any] = {
            "model": model or os.environ.get("MODEL", "gpt-4o"),
            "input": input_messages,
            "stream": True,
        }

        if instructions_parts:
            request_body["instructions"] = "\n\n".join(instructions_parts)

        # Responses API 的 response_format 格式
        if response_format:
            request_body["text"] = {"format": {"type": response_format}}

        if temperature is not None:
            request_body["temperature"] = temperature
        if top_p is not None:
            request_body["top_p"] = top_p
        if max_tokens is not None:
            request_body["max_output_tokens"] = max_tokens

        # 调用 Responses API
        stream = await self._client.responses.create(**request_body, timeout=timeout)

        async for event in stream:
            event_type = getattr(event, "type", None)

            # 文本增量事件
            if event_type == "response.output_text.delta":
                delta = getattr(event, "delta", "")
                if delta:
                    yield {"content": delta, "finish_reason": None}

            # 文本完成事件
            elif event_type == "response.output_text.done":
                text = getattr(event, "text", "")
                # 只有在之前没有收到增量时才使用完整文本
                if text:
                    pass  # 增量已经处理过了，这里跳过

            # 响应完成事件
            elif event_type == "response.completed":
                response = getattr(event, "response", None)
                finish_reason = "stop"
                if response:
                    status = getattr(response, "status", None)
                    if status == "incomplete":
                        details = getattr(response, "incomplete_details", None)
                        reason = getattr(details, "reason", None) if details else None
                        if reason == "max_output_tokens":
                            finish_reason = "length"
                        elif reason == "content_filter":
                            finish_reason = "content_filter"
                        else:
                            finish_reason = "incomplete"
                    elif status in {"failed", "cancelled"}:
                        finish_reason = "error"
                yield {"content": "", "finish_reason": finish_reason}

            # 响应失败/取消事件
            elif event_type in {"response.failed", "response.cancelled", "response.incomplete"}:
                yield {"content": "", "finish_reason": "error"}


class AnthropicClient(BaseLLMClient):
    """Anthropic Messages API 客户端（/v1/messages）。

    使用 httpx 直接调用 API，兼容更多中转服务。
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError("缺少 ANTHROPIC_API_KEY 配置，请在数据库或环境变量中补全。")

        resolved_base_url = (
            base_url
            or os.environ.get("ANTHROPIC_BASE_URL")
            or "https://api.anthropic.com"
        )
        super().__init__(key, resolved_base_url)

    async def stream_chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: float | httpx.Timeout | None = None,
        **kwargs,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式调用 Anthropic Messages API（使用 httpx 直接请求）。

        注意：部分代理服务不支持 system 字段，因此本客户端将 system 消息
        嵌入到第一条 user 消息的开头，以确保兼容性。
        """

        # 分离 system 消息
        system_content: Optional[str] = None
        api_messages: List[Dict[str, str]] = []

        for msg in messages:
            if msg.role == "system":
                system_content = msg.content
            else:
                # Anthropic 只支持 user 和 assistant 角色
                role = "user" if msg.role == "user" else "assistant"
                api_messages.append({"role": role, "content": msg.content})

        # 确保消息列表不为空且以 user 消息开始
        if not api_messages:
            api_messages.append({"role": "user", "content": "Hello"})

        # 将 system 内容嵌入到第一条 user 消息中（兼容不支持 system 字段的代理服务）
        if system_content and api_messages:
            first_msg = api_messages[0]
            if first_msg["role"] == "user":
                # 将 system 内容作为前缀嵌入到第一条 user 消息
                first_msg["content"] = f"<system>\n{system_content}\n</system>\n\n{first_msg['content']}"
            else:
                # 如果第一条不是 user 消息，在开头插入一条包含 system 内容的 user 消息
                api_messages.insert(0, {"role": "user", "content": f"<system>\n{system_content}\n</system>\n\nPlease follow the system instructions above."})

        # 构建请求体（不使用 system 字段，以兼容更多代理服务）
        body: Dict[str, Any] = {
            "model": model or os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
            "messages": api_messages,
            "max_tokens": max_tokens or 4096,
            "stream": True,
        }

        if temperature is not None:
            body["temperature"] = temperature
        if top_p is not None:
            body["top_p"] = top_p

        # 构建 URL
        base = self.base_url.rstrip("/") if self.base_url else "https://api.anthropic.com"
        url = f"{base}/v1/messages"

        # 构建请求头
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

        # 处理超时
        if timeout is None:
            request_timeout = 600.0
        elif isinstance(timeout, httpx.Timeout):
            request_timeout = timeout.read or 600.0
        else:
            request_timeout = timeout

        async with httpx.AsyncClient(timeout=request_timeout) as http:
            async with http.stream("POST", url, headers=headers, json=body) as response:
                # 检查响应状态，如果出错则读取完整响应体以获取错误详情
                if response.status_code >= 400:
                    error_body = await response.aread()
                    error_detail = f"HTTP {response.status_code}"
                    try:
                        error_json = json.loads(error_body)
                        if isinstance(error_json, dict):
                            error_data = error_json.get("error", {})
                            if isinstance(error_data, dict):
                                error_detail = error_data.get("message") or error_detail
                            elif isinstance(error_data, str):
                                error_detail = error_data
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        error_detail = error_body.decode("utf-8", errors="replace")[:500]
                    # 创建一个带有已读取内容的响应对象用于异常
                    raise httpx.HTTPStatusError(
                        message=f"Server error '{response.status_code}' for url '{url}': {error_detail}",
                        request=response.request,
                        response=response,
                    )

                async for line in response.aiter_lines():
                    if not line:
                        continue

                    # 解析 SSE 事件
                    if line.startswith("event: "):
                        event_type = line[7:]
                        continue

                    if line.startswith("data: "):
                        data_str = line[6:]
                        if not data_str:
                            continue

                        try:
                            data = json.loads(data_str)
                        except json.JSONDecodeError:
                            continue

                        event_type = data.get("type", "")

                        # 处理内容增量
                        if event_type == "content_block_delta":
                            delta = data.get("delta", {})
                            if delta.get("type") == "text_delta":
                                text = delta.get("text", "")
                                if text:
                                    yield {"content": text, "finish_reason": None}

                        # 处理消息结束
                        elif event_type == "message_delta":
                            delta = data.get("delta", {})
                            stop_reason = delta.get("stop_reason")
                            if stop_reason:
                                # 转换 Anthropic 的 stop_reason 到通用格式
                                finish_reason_map = {
                                    "end_turn": "stop",
                                    "max_tokens": "length",
                                    "stop_sequence": "stop",
                                    "tool_use": "tool_calls",
                                }
                                finish_reason = finish_reason_map.get(stop_reason, "stop")
                                yield {"content": "", "finish_reason": finish_reason}

                        # 处理消息完全结束
                        elif event_type == "message_stop":
                            # 如果之前没有收到 finish_reason，这里补发一个
                            pass


class GoogleClient(BaseLLMClient):
    """Google Generative AI API 客户端（streamGenerateContent）。"""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise ValueError("缺少 GOOGLE_API_KEY 配置，请在数据库或环境变量中补全。")

        resolved_base_url = (
            base_url
            or os.environ.get("GOOGLE_BASE_URL")
            or "https://generativelanguage.googleapis.com/v1beta"
        )
        super().__init__(key, resolved_base_url)

    async def stream_chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: float | httpx.Timeout | None = None,
        **kwargs,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式调用 Google Generative AI API。"""

        target_model = model or os.environ.get("GOOGLE_MODEL", "gemini-1.5-flash")

        # 构建 URL
        base = self.base_url.rstrip("/") if self.base_url else "https://generativelanguage.googleapis.com/v1beta"
        url = f"{base}/models/{target_model}:streamGenerateContent?alt=sse&key={self.api_key}"

        # 转换消息格式
        # Google 的格式: {"contents": [{"role": "user", "parts": [{"text": "..."}]}]}
        system_instruction: Optional[str] = None
        contents: List[Dict[str, Any]] = []

        for msg in messages:
            if msg.role == "system":
                system_instruction = msg.content
            else:
                # Google API 使用 "user" 和 "model" 角色
                role = "user" if msg.role == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.content}]
                })

        # 确保 contents 不为空
        if not contents:
            contents.append({
                "role": "user",
                "parts": [{"text": "Hello"}]
            })

        body: Dict[str, Any] = {"contents": contents}

        if system_instruction:
            body["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        # 添加生成配置
        generation_config: Dict[str, Any] = {}
        if temperature is not None:
            generation_config["temperature"] = temperature
        if top_p is not None:
            generation_config["topP"] = top_p
        if max_tokens is not None:
            generation_config["maxOutputTokens"] = max_tokens

        if generation_config:
            body["generationConfig"] = generation_config

        # 处理超时
        if timeout is None:
            request_timeout = 600.0
        elif isinstance(timeout, httpx.Timeout):
            request_timeout = timeout.read or 600.0
        else:
            request_timeout = timeout

        async with httpx.AsyncClient(timeout=request_timeout) as http:
            async with http.stream("POST", url, json=body) as response:
                # 检查响应状态，如果出错则读取完整响应体以获取错误详情
                if response.status_code >= 400:
                    error_body = await response.aread()
                    error_detail = f"HTTP {response.status_code}"
                    try:
                        error_json = json.loads(error_body)
                        if isinstance(error_json, dict):
                            # Google 错误格式: {"error": {"message": "...", "code": ...}}
                            error_data = error_json.get("error", {})
                            if isinstance(error_data, dict):
                                error_detail = error_data.get("message") or error_detail
                            elif isinstance(error_data, str):
                                error_detail = error_data
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        error_detail = error_body.decode("utf-8", errors="replace")[:500]
                    raise httpx.HTTPStatusError(
                        message=f"Server error '{response.status_code}' for url '{url}': {error_detail}",
                        request=response.request,
                        response=response,
                    )

                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue

                    data_str = line[6:]  # 去掉 "data: " 前缀
                    if not data_str or data_str == "[DONE]":
                        continue

                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    candidates = data.get("candidates", [])
                    if not candidates:
                        continue

                    candidate = candidates[0]
                    content = candidate.get("content", {})
                    parts = content.get("parts", [])

                    for part in parts:
                        text = part.get("text", "")
                        if text:
                            yield {"content": text, "finish_reason": None}

                    # 检查是否完成
                    finish_reason_raw = candidate.get("finishReason")
                    if finish_reason_raw:
                        # 转换 Google 的 finishReason 到通用格式
                        finish_reason_map = {
                            "STOP": "stop",
                            "MAX_TOKENS": "length",
                            "SAFETY": "content_filter",
                            "RECITATION": "content_filter",
                            "OTHER": "stop",
                        }
                        finish_reason = finish_reason_map.get(finish_reason_raw, "stop")
                        yield {"content": "", "finish_reason": finish_reason}


def create_llm_client(
    api_format: ApiFormatType,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> BaseLLMClient:
    """根据 API 格式创建对应的 LLM 客户端。

    Args:
        api_format: API 格式类型
        api_key: API 密钥
        base_url: API 基础 URL

    Returns:
        对应的 LLM 客户端实例
    """
    clients = {
        "openai_chat": OpenAIChatClient,
        "openai_responses": OpenAIResponsesClient,
        "anthropic": AnthropicClient,
        "google": GoogleClient,
    }

    client_class = clients.get(api_format)
    if not client_class:
        raise ValueError(f"不支持的 API 格式: {api_format}")

    return client_class(api_key=api_key, base_url=base_url)


# 为了向后兼容，保留原来的 LLMClient 作为 OpenAIResponsesClient 的别名
LLMClient = OpenAIResponsesClient
