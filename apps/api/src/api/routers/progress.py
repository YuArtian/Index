"""Learning progress routes — CRUD for books/courses and chapters."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ...services import ProgressService

router = APIRouter(prefix="/progress", tags=["Progress"])


class CreateItemRequest(BaseModel):
    title: str
    author: str | None = None
    type: str = "book"
    chapters: list[str] | None = None


class UpdateItemRequest(BaseModel):
    title: str | None = None
    author: str | None = None
    status: str | None = None
    notes: str | None = None


class UpdateChapterRequest(BaseModel):
    status: str | None = None
    notes: str | None = None


def init_router(progress_service: ProgressService) -> APIRouter:
    """Initialize progress router with service instance."""

    @router.post("")
    async def create_item(request: CreateItemRequest):
        """Add a learning item (book/course)."""
        item = await progress_service.create_item(
            title=request.title,
            author=request.author,
            type=request.type,
            chapters=request.chapters,
        )
        return {
            "id": item.id,
            "title": item.title,
            "total_chapters": item.total_chapters,
        }

    @router.get("")
    async def list_items(
        page: int = Query(1, ge=1),
        size: int = Query(20, ge=1, le=100),
    ):
        """List learning items with pagination."""
        result = await progress_service.list_items(page=page, size=size)
        return {
            "items": [
                {
                    "id": i.id,
                    "title": i.title,
                    "author": i.author,
                    "type": i.type,
                    "total_chapters": i.total_chapters,
                    "completed_chapters": i.completed_chapters,
                    "status": i.status,
                    "updated_at": i.updated_at.isoformat() if i.updated_at else None,
                }
                for i in result["items"]
            ],
            "total": result["total"],
            "page": result["page"],
            "size": result["size"],
        }

    @router.get("/{item_id}")
    async def get_item(item_id: str):
        """Get a learning item with its chapters."""
        data = await progress_service.get_item(item_id)
        if not data:
            raise HTTPException(status_code=404, detail="Item not found")
        item = data["item"]
        return {
            "id": item.id,
            "title": item.title,
            "author": item.author,
            "type": item.type,
            "total_chapters": item.total_chapters,
            "completed_chapters": item.completed_chapters,
            "status": item.status,
            "notes": item.notes,
            "chapters": [
                {
                    "id": c.id,
                    "title": c.title,
                    "chapter_index": c.chapter_index,
                    "status": c.status,
                    "completed_at": c.completed_at.isoformat() if c.completed_at else None,
                    "notes": c.notes,
                }
                for c in data["chapters"]
            ],
        }

    @router.put("/{item_id}")
    async def update_item(item_id: str, request: UpdateItemRequest):
        """Update a learning item."""
        item = await progress_service.update_item(
            item_id,
            title=request.title,
            author=request.author,
            status=request.status,
            notes=request.notes,
        )
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        return {"id": item.id, "title": item.title, "status": item.status}

    @router.delete("/{item_id}")
    async def delete_item(item_id: str):
        """Delete a learning item."""
        success = await progress_service.delete_item(item_id)
        if not success:
            raise HTTPException(status_code=404, detail="Item not found")
        return {"success": True, "message": f"Deleted item {item_id}"}

    @router.put("/{item_id}/chapters/{chapter_id}")
    async def update_chapter(
        item_id: str,
        chapter_id: str,
        request: UpdateChapterRequest,
    ):
        """Update a chapter's status or notes."""
        chapter = await progress_service.update_chapter(
            item_id=item_id,
            chapter_id=chapter_id,
            status=request.status,
            notes=request.notes,
        )
        if not chapter:
            raise HTTPException(status_code=404, detail="Chapter not found")
        return {
            "id": chapter.id,
            "title": chapter.title,
            "status": chapter.status,
            "completed_at": chapter.completed_at.isoformat() if chapter.completed_at else None,
        }

    return router
