"""
Learning progress service - CRUD for reading items with percentage progress.
"""

import uuid

from loguru import logger
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..models.learning_item import LearningItem


class ProgressService:
    """Service for managing learning progress."""

    def __init__(self, session_factory: async_sessionmaker):
        self._session_factory = session_factory

    async def create_item(
        self,
        title: str,
        author: str | None = None,
        type: str = "book",
        document_id: str | None = None,
    ) -> LearningItem:
        """Create a learning item."""
        item_id = str(uuid.uuid4())
        async with self._session_factory() as session:
            item = LearningItem(
                id=item_id,
                title=title,
                author=author,
                type=type,
                document_id=document_id,
            )
            session.add(item)
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

    async def get_item(self, item_id: str) -> LearningItem | None:
        """Get a learning item."""
        async with self._session_factory() as session:
            return await session.get(LearningItem, item_id)

    async def update_item(self, item_id: str, **kwargs) -> LearningItem | None:
        """Update a learning item's fields."""
        async with self._session_factory() as session:
            item = await session.get(LearningItem, item_id)
            if not item:
                return None
            for key, value in kwargs.items():
                if hasattr(item, key) and value is not None:
                    setattr(item, key, value)
            # Auto-update status based on progress
            if item.progress >= 100:
                item.progress = 100
                item.status = "completed"
            elif item.progress > 0:
                item.status = "reading"
            await session.commit()
            await session.refresh(item)
            return item

    async def delete_item(self, item_id: str) -> str | None:
        """Delete a learning item. Returns document_id if linked, None if not found."""
        async with self._session_factory() as session:
            item = await session.get(LearningItem, item_id)
            if not item:
                return None
            document_id = item.document_id
            await session.delete(item)
            await session.commit()
            return document_id or ""
