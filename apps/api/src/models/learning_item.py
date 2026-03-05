"""Learning progress model — tracks reading progress as a percentage."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

TZDateTime = DateTime(timezone=True)


class LearningItem(Base):
    __tablename__ = "learning_items"

    id: Mapped[str] = mapped_column(primary_key=True)
    title: Mapped[str]
    author: Mapped[str | None]
    type: Mapped[str] = mapped_column(default="book")
    progress: Mapped[int] = mapped_column(default=0)  # 0-100 percentage
    status: Mapped[str] = mapped_column(default="reading")  # reading / completed
    notes: Mapped[str | None]
    document_id: Mapped[str | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(TZDateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TZDateTime, server_default=func.now(), onupdate=func.now())

    document = relationship("Document", lazy="selectin")
