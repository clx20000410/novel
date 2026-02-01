# AIMETA P=LLM配置模型_模型配置存储|R=LLM配置表|NR=不含配置逻辑|E=LLMConfig|X=internal|A=ORM模型|D=sqlalchemy|S=none|RD=./README.ai
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship


from ..db.base import Base


class LLMConfig(Base):
    """用户自定义的 LLM 接入配置，支持多配置管理。"""

    __tablename__ = "llm_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, default="默认配置")
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    api_format: Mapped[str] = mapped_column(String(32), nullable=False, default="openai_chat")
    llm_provider_url: Mapped[str | None] = mapped_column(Text())
    llm_provider_api_key: Mapped[str | None] = mapped_column(Text())
    llm_provider_model: Mapped[str | None] = mapped_column(Text())
    blueprint_batch_size: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="llm_configs")
