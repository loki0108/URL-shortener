from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class URL(Base):
    __tablename__ = "urls"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    short_code: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    original_url: Mapped[str] = mapped_column(String(2048))
    clicks: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )