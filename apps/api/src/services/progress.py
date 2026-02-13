"""
Learning progress service - CRUD for books/courses and chapters.
"""

import uuid
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..models.learning_item import LearningItem, Chapter


class ProgressService:
    """Service for managing learning progress."""

    def __init__(self, session_factory: async_sessionmaker):
        self._session_factory = session_factory

    async def create_item(
        self,
        title: str,
        author: str | None = None,
        type: str = "book",
        chapters: list[str] | None = None,
    ) -> LearningItem:
        """Create a learning item with optional chapters."""
        item_id = str(uuid.uuid4())[:8]
        async with self._session_factory() as session:
            item = LearningItem(
                id=item_id,
                title=title,
                author=author,
                type=type,
                total_chapters=len(chapters) if chapters else 0,
            )
            session.add(item)

            if chapters:
                for i, ch_title in enumerate(chapters):
                    session.add(Chapter(
                        id=str(uuid.uuid4())[:8],
                        learning_item_id=item_id,
                        title=ch_title,
                        chapter_index=i,
                    ))

            await session.commit()
            await session.refresh(item)
            logger.info(f"Created learning item: {title}")
            return item

    async def list_items(self, page: int = 1, size: int = 20) -> dict:
        """List learning items with pagination."""
        offset = (page - 1) * size
        async with self._session_factory() as session:
            result = await session.execute(
                select(LearningItem)
                .order_by(LearningItem.updated_at.desc())
                .offset(offset)
                .limit(size)
            )
            items = list(result.scalars().all())
            total = await session.scalar(select(func.count(LearningItem.id)))
            return {"items": items, "total": total, "page": page, "size": size}

    async def get_item(self, item_id: str) -> dict | None:
        """Get a learning item with its chapters."""
        async with self._session_factory() as session:
            item = await session.get(LearningItem, item_id)
            if not item:
                return None
            result = await session.execute(
                select(Chapter)
                .where(Chapter.learning_item_id == item_id)
                .order_by(Chapter.chapter_index)
            )
            chapters = list(result.scalars().all())
            return {"item": item, "chapters": chapters}

    async def update_item(self, item_id: str, **kwargs) -> LearningItem | None:
        """Update a learning item's fields."""
        async with self._session_factory() as session:
            item = await session.get(LearningItem, item_id)
            if not item:
                return None
            for key, value in kwargs.items():
                if hasattr(item, key) and value is not None:
                    setattr(item, key, value)
            await session.commit()
            await session.refresh(item)
            return item

    async def delete_item(self, item_id: str) -> bool:
        """Delete a learning item and its chapters."""
        async with self._session_factory() as session:
            item = await session.get(LearningItem, item_id)
            if not item:
                return False
            await session.delete(item)
            await session.commit()
            return True

    async def update_chapter(
        self,
        item_id: str,
        chapter_id: str,
        status: str | None = None,
        notes: str | None = None,
    ) -> Chapter | None:
        """Update a chapter's status or notes."""
        async with self._session_factory() as session:
            chapter = await session.get(Chapter, chapter_id)
            if not chapter or chapter.learning_item_id != item_id:
                return None

            if status:
                chapter.status = status
                if status == "completed":
                    chapter.completed_at = datetime.now(timezone.utc)
            if notes is not None:
                chapter.notes = notes

            # Recalculate completed count
            result = await session.execute(
                select(func.count(Chapter.id))
                .where(Chapter.learning_item_id == item_id)
                .where(Chapter.status == "completed")
            )
            completed = result.scalar() or 0

            item = await session.get(LearningItem, item_id)
            item.completed_chapters = completed

            # Auto-update item status
            if completed == item.total_chapters and item.total_chapters > 0:
                item.status = "completed"
            elif completed > 0:
                item.status = "reading"

            await session.commit()
            await session.refresh(chapter)
            return chapter
