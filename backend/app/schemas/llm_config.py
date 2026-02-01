# AIMETA P=LLM配置模式_模型配置请求响应|R=LLM配置结构|NR=不含业务逻辑|E=LLMConfigSchema|X=internal|A=Pydantic模式|D=pydantic|S=none|RD=./README.ai
from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, HttpUrl, Field


# API 格式枚举类型
ApiFormatType = Literal["openai_chat", "openai_responses", "anthropic", "google"]


class LLMConfigBase(BaseModel):
    """LLM 配置基础字段"""
    name: str = Field(default="默认配置", max_length=64, description="配置名称")
    api_format: ApiFormatType = Field(default="openai_chat", description="API 接口格式")
    llm_provider_url: Optional[HttpUrl] = Field(default=None, description="自定义 LLM 服务地址")
    llm_provider_api_key: Optional[str] = Field(default=None, description="自定义 LLM API Key")
    llm_provider_model: Optional[str] = Field(default=None, description="自定义模型名称")
    blueprint_batch_size: int = Field(default=5, ge=1, le=50, description="蓝图生成每批章节数")


class LLMConfigCreate(BaseModel):
    """创建 LLM 配置的请求体"""
    name: str = Field(..., max_length=64, description="配置名称")
    api_format: ApiFormatType = Field(default="openai_chat", description="API 接口格式")
    llm_provider_url: Optional[HttpUrl] = Field(default=None, description="自定义 LLM 服务地址")
    llm_provider_api_key: Optional[str] = Field(default=None, description="自定义 LLM API Key")
    llm_provider_model: Optional[str] = Field(default=None, description="自定义模型名称")
    blueprint_batch_size: int = Field(default=5, ge=1, le=50, description="蓝图生成每批章节数")


class LLMConfigUpdate(BaseModel):
    """更新 LLM 配置的请求体"""
    name: Optional[str] = Field(default=None, max_length=64, description="配置名称")
    api_format: Optional[ApiFormatType] = Field(default=None, description="API 接口格式")
    llm_provider_url: Optional[HttpUrl] = Field(default=None, description="自定义 LLM 服务地址")
    llm_provider_api_key: Optional[str] = Field(default=None, description="自定义 LLM API Key")
    llm_provider_model: Optional[str] = Field(default=None, description="自定义模型名称")
    blueprint_batch_size: Optional[int] = Field(default=None, ge=1, le=50, description="蓝图生成每批章节数")


class LLMConfigRead(BaseModel):
    """LLM 配置的响应体"""
    id: int
    user_id: int
    name: str
    is_active: bool
    api_format: str = "openai_chat"
    llm_provider_url: Optional[str] = None
    llm_provider_api_key: Optional[str] = None
    llm_provider_model: Optional[str] = None
    blueprint_batch_size: int = 5
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ModelListRequest(BaseModel):
    """获取模型列表的请求体"""
    api_format: ApiFormatType = Field(default="openai_chat", description="API 接口格式")
    llm_provider_url: Optional[str] = Field(default=None, description="LLM 服务地址")
    llm_provider_api_key: str = Field(..., description="LLM API Key")


class TestConnectionRequest(BaseModel):
    """测试连接的请求体"""
    api_format: ApiFormatType = Field(..., description="API 接口格式")
    llm_provider_url: Optional[str] = Field(default=None, description="LLM 服务地址")
    llm_provider_api_key: str = Field(..., description="LLM API Key")
    llm_provider_model: str = Field(..., description="模型名称")


class TestConnectionResponse(BaseModel):
    """测试连接的响应体"""
    success: bool = Field(..., description="是否成功")
    latency_ms: int = Field(..., description="延迟毫秒数")
    message: str = Field(..., description="结果消息")
