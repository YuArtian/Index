"""
Storage providers package.
"""

from .base import StorageProvider, SearchResult
from .pgvector import PgvectorStorageProvider


def create_storage_provider(provider: str, **kwargs) -> StorageProvider:
    """
    Factory function to create storage provider.

    Args:
        provider: Provider type ("pgvector")
        **kwargs: Provider-specific arguments (session_factory for pgvector)

    Returns:
        StorageProvider instance
    """
    if provider == "pgvector":
        return PgvectorStorageProvider(session_factory=kwargs["session_factory"])
    else:
        raise ValueError(f"Unknown storage provider: {provider}")


__all__ = [
    "StorageProvider",
    "SearchResult",
    "PgvectorStorageProvider",
    "create_storage_provider",
]
