"""Conversations routes — CRUD for chat history."""

from fastapi import APIRouter, HTTPException, Query

from ...services import ChatService

router = APIRouter(prefix="/conversations", tags=["Conversations"])


def init_router(chat_service: ChatService) -> APIRouter:
    """Initialize conversations router with service instance."""

    @router.post("")
    async def create_conversation():
        """Create a new conversation."""
        conv = await chat_service.create_conversation()
        return {"id": conv.id, "title": conv.title, "created_at": conv.created_at.isoformat()}

    @router.get("")
    async def list_conversations(
        page: int = Query(1, ge=1),
        size: int = Query(20, ge=1, le=100),
    ):
        """List all conversations with pagination."""
        result = await chat_service.list_conversations(page=page, size=size)
        return {
            "items": [
                {
                    "id": c.id,
                    "title": c.title,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                    "updated_at": c.updated_at.isoformat() if c.updated_at else None,
                }
                for c in result["items"]
            ],
            "total": result["total"],
            "page": result["page"],
            "size": result["size"],
        }

    @router.get("/{conv_id}")
    async def get_conversation(conv_id: str):
        """Get conversation with messages."""
        data = await chat_service.get_conversation(conv_id)
        if not data:
            raise HTTPException(status_code=404, detail="Conversation not found")
        conv = data["conversation"]
        return {
            "id": conv.id,
            "title": conv.title,
            "created_at": conv.created_at.isoformat() if conv.created_at else None,
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in data["messages"]
            ],
        }

    @router.delete("/{conv_id}")
    async def delete_conversation(conv_id: str):
        """Delete a conversation."""
        success = await chat_service.delete_conversation(conv_id)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"success": True, "message": f"Deleted conversation {conv_id}"}

    return router
