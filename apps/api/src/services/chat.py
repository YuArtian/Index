"""
Chat service - Claude conversation with streaming + Tool-based RAG.
"""

import json
import uuid
from typing import AsyncGenerator

import anthropic
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..models.conversation import Conversation, Message
from .search import SearchService


class ChatService:
    """Claude chat with streaming SSE and optional RAG tool."""

    def __init__(
        self,
        api_key: str,
        search_service: SearchService,
        session_factory: async_sessionmaker,
    ):
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._search = search_service
        self._session_factory = session_factory

    async def stream_chat(
        self,
        conversation_id: str,
        message: str,
    ) -> AsyncGenerator[str, None]:
        """Stream Claude response as SSE events."""

        # Save user message
        user_msg_id = str(uuid.uuid4())[:8]
        async with self._session_factory() as session:
            session.add(Message(
                id=user_msg_id,
                conversation_id=conversation_id,
                role="user",
                content=message,
            ))
            await session.commit()

        # Load conversation history
        async with self._session_factory() as session:
            result = await session.execute(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at)
            )
            history = result.scalars().all()

        # Build messages for Claude
        messages = [{"role": m.role, "content": m.content} for m in history]

        # Define RAG search tool
        tools = [
            {
                "name": "search_knowledge",
                "description": "搜索知识库中的相关内容。当用户的问题可能与已索引的文档内容相关时使用此工具。",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索查询文本",
                        },
                    },
                    "required": ["query"],
                },
            }
        ]

        try:
            full_response = ""
            input_tokens = 0
            output_tokens = 0

            # First call - Claude may decide to use tools
            response = await self._client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system="你是一个友好的学习助手。如果用户的问题可能与知识库内容相关，请使用 search_knowledge 工具搜索。回答时请使用中文。",
                messages=messages,
                tools=tools,
            )

            input_tokens += response.usage.input_tokens
            output_tokens += response.usage.output_tokens

            # Handle tool use
            while response.stop_reason == "tool_use":
                tool_use_block = next(
                    b for b in response.content if b.type == "tool_use"
                )

                # Execute search
                search_query = tool_use_block.input.get("query", "")
                search_results = await self._search.search(search_query, top_k=5)

                # Send source citations to frontend
                sources = [
                    {"content": r.content[:200], "source": r.source, "score": r.score}
                    for r in search_results
                ]
                yield f"data: {json.dumps({'type': 'source', 'sources': sources}, ensure_ascii=False)}\n\n"

                # Build tool result
                tool_result_content = "\n\n---\n\n".join(
                    f"[来源: {r.source}]\n{r.content}" for r in search_results
                ) if search_results else "知识库中没有找到相关内容。"

                # Continue conversation with tool result
                messages.append({"role": "assistant", "content": response.content})
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use_block.id,
                            "content": tool_result_content,
                        }
                    ],
                })

                response = await self._client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4096,
                    system="你是一个友好的学习助手。如果用户的问题可能与知识库内容相关，请使用 search_knowledge 工具搜索。回答时请使用中文。",
                    messages=messages,
                    tools=tools,
                )

                input_tokens += response.usage.input_tokens
                output_tokens += response.usage.output_tokens

            # Extract text from final response
            for block in response.content:
                if hasattr(block, "text"):
                    full_response += block.text
                    yield f"data: {json.dumps({'type': 'text', 'text': block.text}, ensure_ascii=False)}\n\n"

            # Save assistant message
            assistant_msg_id = str(uuid.uuid4())[:8]
            async with self._session_factory() as session:
                session.add(Message(
                    id=assistant_msg_id,
                    conversation_id=conversation_id,
                    role="assistant",
                    content=full_response,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                ))
                await session.commit()

            # Auto-generate title for first message
            await self._maybe_generate_title(conversation_id, message)

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            logger.error(f"Chat error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    async def _maybe_generate_title(self, conversation_id: str, first_message: str):
        """Auto-generate conversation title from the first user message."""
        async with self._session_factory() as session:
            conv = await session.get(Conversation, conversation_id)
            if conv and not conv.title:
                # Simple strategy: truncate first message
                conv.title = first_message[:50].strip()
                if len(first_message) > 50:
                    conv.title += "..."
                await session.commit()

    # --- Conversation CRUD ---

    async def create_conversation(self) -> Conversation:
        """Create a new conversation."""
        conv_id = str(uuid.uuid4())[:8]
        async with self._session_factory() as session:
            conv = Conversation(id=conv_id)
            session.add(conv)
            await session.commit()
            await session.refresh(conv)
            return conv

    async def list_conversations(self, page: int = 1, size: int = 20) -> dict:
        """List conversations with pagination."""
        from sqlalchemy import func
        offset = (page - 1) * size
        async with self._session_factory() as session:
            result = await session.execute(
                select(Conversation)
                .order_by(Conversation.updated_at.desc())
                .offset(offset)
                .limit(size)
            )
            items = list(result.scalars().all())
            total = await session.scalar(select(func.count(Conversation.id)))
            return {"items": items, "total": total, "page": page, "size": size}

    async def get_conversation(self, conv_id: str) -> dict | None:
        """Get conversation with its messages."""
        async with self._session_factory() as session:
            conv = await session.get(Conversation, conv_id)
            if not conv:
                return None
            result = await session.execute(
                select(Message)
                .where(Message.conversation_id == conv_id)
                .order_by(Message.created_at)
            )
            messages = list(result.scalars().all())
            return {"conversation": conv, "messages": messages}

    async def delete_conversation(self, conv_id: str) -> bool:
        """Delete a conversation and its messages (cascade)."""
        async with self._session_factory() as session:
            conv = await session.get(Conversation, conv_id)
            if not conv:
                return False
            await session.delete(conv)
            await session.commit()
            return True
