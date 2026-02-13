"""Chunk model — stores content + vector embedding."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from ..database import Base

TZDateTime = DateTime(timezone=True)


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(primary_key=True)
    content: Mapped[str]
    embedding = mapped_column(Vector(1024))
    doc_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    source: Mapped[str | None]
    chunk_index: Mapped[int | None]
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(TZDateTime, server_default=func.now())

    document = relationship("Document", back_populates="chunks")
