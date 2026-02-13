"""Document model — parent table for chunks, tracks file processing status."""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

TZDateTime = DateTime(timezone=True)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(primary_key=True)
    filename: Mapped[str]
    source: Mapped[str | None]
    content_type: Mapped[str | None]
    status: Mapped[str] = mapped_column(default="uploading")
    error_message: Mapped[str | None]
    chunk_count: Mapped[int] = mapped_column(default=0)
    file_size: Mapped[int | None]
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(TZDateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TZDateTime, server_default=func.now(), onupdate=func.now())

    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
