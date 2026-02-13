"""Chat route — Claude SSE streaming + RAG."""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ...services import ChatService

router = APIRouter(tags=["Chat"])


class ChatRequest(BaseModel):
    conversation_id: str
    message: str


def init_router(chat_service: ChatService) -> APIRouter:
    """Initialize chat router with service instance."""

    @router.post("/chat")
    async def chat(request: ChatRequest):
        """Claude conversation with SSE streaming + Tool-based RAG."""
        return StreamingResponse(
            chat_service.stream_chat(
                conversation_id=request.conversation_id,
                message=request.message,
            ),
            media_type="text/event-stream",
        )

    return router
