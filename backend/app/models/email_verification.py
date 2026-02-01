# AIMETA P=邮箱验证码_验证码存储|R=验证码存储_过期控制|NR=不含业务逻辑|E=EmailVerificationCode|X=internal|A=验证码模型|D=sqlalchemy|S=db|RD=./README.ai
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base


class EmailVerificationCode(Base):
    """存储邮箱验证码，替代进程内缓存，支持多实例部署。"""

    __tablename__ = "email_verification_codes"

    email: Mapped[str] = mapped_column(String(255), primary_key=True)
    code_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
