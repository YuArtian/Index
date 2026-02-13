"""Learning progress models — books/courses and their chapters."""

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
    total_chapters: Mapped[int] = mapped_column(default=0)
    completed_chapters: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(default="reading")
    notes: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(TZDateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TZDateTime, server_default=func.now(), onupdate=func.now())

    chapters = relationship("Chapter", back_populates="learning_item", cascade="all, delete-orphan")


class Chapter(Base):
    __tablename__ = "chapters"

    id: Mapped[str] = mapped_column(primary_key=True)
    learning_item_id: Mapped[str] = mapped_column(ForeignKey("learning_items.id", ondelete="CASCADE"), index=True)
    title: Mapped[str]
    chapter_index: Mapped[int]
    status: Mapped[str] = mapped_column(default="pending")
    completed_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    notes: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(TZDateTime, server_default=func.now())

    learning_item = relationship("LearningItem", back_populates="chapters")
