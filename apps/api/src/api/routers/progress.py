"""Learning progress routes — CRUD for reading items with percentage progress."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ...services import ProgressService, KnowledgeService

router = APIRouter(prefix="/progress", tags=["Progress"])


class CreateItemRequest(BaseModel):
    title: str
    author: str | None = None
    type: str = "book"
    document_id: str | None = None


class UpdateItemRequest(BaseModel):
    title: str | None = None
    author: str | None = None
    progress: int | None = Field(None, ge=0, le=100)
    status: str | None = None
    notes: str | None = None


def init_router(progress_service: ProgressService, knowledge_service: KnowledgeService | None = None) -> APIRouter:
    """Initialize progress router with service instance."""

    @router.post("")
    async def create_item(request: CreateItemRequest):
        """Add a learning item."""
        item = await progress_service.create_item(
            title=request.title,
            author=request.author,
            type=request.type,
            document_id=request.document_id,
        )
        return {"id": item.id, "title": item.title}

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
                    "progress": i.progress,
                    "status": i.status,
                    "document_id": i.document_id,
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
        """Get a learning item."""
        item = await progress_service.get_item(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        return {
            "id": item.id,
            "title": item.title,
            "author": item.author,
            "type": item.type,
            "progress": item.progress,
            "status": item.status,
            "notes": item.notes,
            "document_id": item.document_id,
            "filename": item.document.filename if item.document else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
        }

    @router.put("/{item_id}")
    async def update_item(item_id: str, request: UpdateItemRequest):
        """Update a learning item."""
        item = await progress_service.update_item(
            item_id,
            title=request.title,
            author=request.author,
            progress=request.progress,
            status=request.status,
            notes=request.notes,
        )
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        return {"id": item.id, "title": item.title, "progress": item.progress, "status": item.status}

    @router.delete("/{item_id}")
    async def delete_item(item_id: str):
        """Delete a learning item and its associated document + file."""
        document_id = await progress_service.delete_item(item_id)
        if document_id is None:
            raise HTTPException(status_code=404, detail="Item not found")
        if document_id and knowledge_service:
            await knowledge_service.delete_document(document_id)
        return {"success": True, "message": f"Deleted item {item_id}"}

    return router
