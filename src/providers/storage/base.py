"""
Base class for storage providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Search result item."""

    id: str
    content: str
    score: float
    metadata: dict


class StorageProvider(ABC):
    """
    Abstract base class for storage providers.

    All storage implementations must inherit from this class
    and implement the required methods.
    """

    @abstractmethod
    def add(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict] | None = None,
    ) -> None:
        """
        Add documents to storage.

        Args:
            ids: Document IDs
            documents: Document contents
            embeddings: Document embeddings
            metadatas: Optional metadata for each document
        """
        pass

    @abstractmethod
    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filter_metadata: dict | None = None,
    ) -> list[SearchResult]:
        """
        Search for similar documents.

        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            filter_metadata: Optional metadata filter

        Returns:
            List of SearchResult objects
        """
        pass

    @abstractmethod
    def get_all(self) -> list[dict]:
        """
        Get all documents.

        Returns:
            List of document info dictionaries
        """
        pass

    @abstractmethod
    def delete(self, ids: list[str]) -> None:
        """
        Delete documents by IDs.

        Args:
            ids: List of document IDs to delete
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """
        Get total document count.

        Returns:
            Number of documents in storage
        """
        pass
