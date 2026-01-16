"""
Storage providers package.
"""

from .base import StorageProvider, SearchResult
from .chroma import ChromaStorageProvider


def create_storage_provider(
    provider: str,
    path: str = "./data/chroma",
    collection_name: str = "index_kb",
    **kwargs,
) -> StorageProvider:
    """
    Factory function to create storage provider.

    Args:
        provider: Provider type ("chroma", "pgvector", "milvus")
        path: Storage path (for file-based providers)
        collection_name: Collection/table name
        **kwargs: Additional provider-specific arguments

    Returns:
        StorageProvider instance
    """
    if provider == "chroma":
        return ChromaStorageProvider(path=path, collection_name=collection_name)
    # Future: pgvector, milvus, etc.
    else:
        raise ValueError(f"Unknown storage provider: {provider}")


__all__ = [
    "StorageProvider",
    "SearchResult",
    "ChromaStorageProvider",
    "create_storage_provider",
]
