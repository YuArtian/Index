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
    """Abstract base class for storage providers. All methods are async."""

    @abstractmethod
    async def add(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict] | None = None,
    ) -> None:
        pass

    @abstractmethod
    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filter_metadata: dict | None = None,
    ) -> list[SearchResult]:
        pass

    @abstractmethod
    async def get_all(self) -> list[dict]:
        pass

    @abstractmethod
    async def delete(self, ids: list[str]) -> None:
        pass

    @abstractmethod
    async def count(self) -> int:
        pass
