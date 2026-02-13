"""
Search service - handles semantic search operations.

Updated: storage.search() is now async.
"""

from dataclasses import dataclass

from ..providers.embedding import EmbeddingProvider
from ..providers.storage import StorageProvider


@dataclass
class SearchResultItem:
    """Search result item with all details."""

    content: str
    source: str
    score: float
    metadata: dict


class SearchService:
    """Service for semantic search operations."""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        storage_provider: StorageProvider,
    ):
        self._embedding = embedding_provider
        self._storage = storage_provider

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: dict | None = None,
    ) -> list[SearchResultItem]:
        """Search for similar documents."""
        if not query or not query.strip():
            return []

        query_embedding = await self._embedding.embed(query.strip())

        results = await self._storage.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filter_metadata=filter_metadata,
        )

        return [
            SearchResultItem(
                content=r.content,
                source=r.metadata.get("source", "unknown"),
                score=r.score,
                metadata=r.metadata,
            )
            for r in results
        ]

    async def search_by_doc_id(
        self,
        query: str,
        doc_id: str,
        top_k: int = 5,
    ) -> list[SearchResultItem]:
        """Search within a specific document."""
        return await self.search(
            query=query,
            top_k=top_k,
            filter_metadata={"doc_id": doc_id},
        )
