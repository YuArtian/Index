"""
FastAPI application factory.

Uses lifespan context manager (replaces deprecated @app.on_event).
Initializes all providers, services, and routers.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from ..config import settings
from ..database import async_session, init_db, close_db
from ..providers.embedding import create_embedding_provider
from ..providers.storage import create_storage_provider
from ..services import KnowledgeService, SearchService, ChatService, ProgressService, GraphService
from .routers import knowledge, chat, conversations, progress, graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown."""
    # Startup
    await init_db()
    logger.info("Database connected")
    logger.info(f"Embedding: {settings.embedding.provider} / {settings.embedding.model}")

    # Neo4j
    graph_service: GraphService = app.state.graph_service
    try:
        await graph_service.verify_connection()
        await graph_service.setup_constraints()
        logger.info(f"Neo4j connected: {settings.neo4j.uri}")
    except Exception as e:
        logger.warning(f"Neo4j unavailable: {e} (graph features disabled)")

    logger.info("API docs: http://localhost:8000/docs")
    yield
    # Shutdown
    await graph_service.close()
    await close_db()
    logger.info("Database disconnected")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Index",
        description="Personal Learning Assistant",
        version="0.3.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Providers
    embedding_provider = create_embedding_provider(
        provider=settings.embedding.provider,
        api_key=settings.embedding.api_key,
        base_url=settings.embedding.base_url,
        model=settings.embedding.model,
    )

    storage_provider = create_storage_provider(
        provider="pgvector",
        session_factory=async_session,
    )

    # Services
    graph_service = GraphService(
        uri=settings.neo4j.uri,
        user=settings.neo4j.user,
        password=settings.neo4j.password,
        anthropic_api_key=settings.anthropic_api_key,
    )
    # Store on app.state so lifespan can access it
    app.state.graph_service = graph_service

    knowledge_service = KnowledgeService(
        embedding_provider=embedding_provider,
        storage_provider=storage_provider,
        session_factory=async_session,
        default_chunk_size=settings.chunk_size,
        default_chunk_overlap=settings.chunk_overlap,
        graph_service=graph_service,
    )

    search_service = SearchService(
        embedding_provider=embedding_provider,
        storage_provider=storage_provider,
    )

    chat_service = ChatService(
        api_key=settings.anthropic_api_key,
        search_service=search_service,
        session_factory=async_session,
    )

    progress_service = ProgressService(
        session_factory=async_session,
    )

    # Routers
    app.include_router(knowledge.init_router(knowledge_service, search_service, settings.anthropic_api_key, settings.data_dir))
    app.include_router(chat.init_router(chat_service))
    app.include_router(conversations.init_router(chat_service))
    app.include_router(progress.init_router(progress_service, knowledge_service))
    app.include_router(graph.init_router(graph_service))

    return app
