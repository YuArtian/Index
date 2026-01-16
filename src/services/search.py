"""
Search service - handles semantic search operations.
"""

from dataclasses import dataclass

from ..providers.embedding import EmbeddingProvider
from ..providers.storage import StorageProvider, SearchResult


@dataclass
class SearchResultItem:
    """Search result item with all details."""

    content: str
    source: str
    score: float
    metadata: dict


class SearchService:
    """
    Service for semantic search operations.

    Handles query embedding and retrieval.
    """

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
        """
        Search for similar documents.

        Args:
            query: Search query text
            top_k: Number of results to return
            filter_metadata: Optional metadata filter

        Returns:
            List of SearchResultItem objects
        """
        if not query or not query.strip():
            return []

        # Get query embedding
        query_embedding = await self._embedding.embed(query.strip())

        # Search in storage
        results = self._storage.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filter_metadata=filter_metadata,
        )

        # Convert to SearchResultItem
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
        """
        Search within a specific document.

        Args:
            query: Search query text
            doc_id: Document ID to search within
            top_k: Number of results to return

        Returns:
            List of SearchResultItem objects
        """
        return await self.search(
            query=query,
            top_k=top_k,
            filter_metadata={"doc_id": doc_id},
        )
