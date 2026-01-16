"""
FastAPI application factory.
"""

from fastapi import FastAPI

from ..config import config
from ..providers.embedding import create_embedding_provider
from ..providers.storage import create_storage_provider
from ..services import KnowledgeService, SearchService
from .routes import create_router


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application
    """
    # Create FastAPI app
    app = FastAPI(
        title="Index",
        description="Local Knowledge Base with Semantic Search",
        version="0.2.0",
    )

    # Create providers
    embedding_provider = create_embedding_provider(
        provider=config.embedding.provider,
        api_key=config.embedding.api_key,
        base_url=config.embedding.base_url,
        model=config.embedding.model,
    )

    storage_provider = create_storage_provider(
        provider=config.storage.provider,
        path=config.storage.path,
        collection_name=config.storage.collection_name,
    )

    # Create services
    knowledge_service = KnowledgeService(
        embedding_provider=embedding_provider,
        storage_provider=storage_provider,
        default_chunk_size=config.chunk_size,
        default_chunk_overlap=config.chunk_overlap,
    )

    search_service = SearchService(
        embedding_provider=embedding_provider,
        storage_provider=storage_provider,
    )

    # Create and include router
    router = create_router(
        knowledge_service=knowledge_service,
        search_service=search_service,
    )
    app.include_router(router)

    # Startup event
    @app.on_event("startup")
    async def startup_event():
        print("=" * 60)
        print("Index - Local Knowledge Base")
        print("=" * 60)
        print(f"Embedding provider: {config.embedding.provider}")
        print(f"Embedding model: {config.embedding.model}")
        print(f"Storage provider: {config.storage.provider}")
        print(f"Storage path: {config.storage.path}")
        print(f"API docs: http://localhost:8000/docs")
        print("=" * 60)

    return app
