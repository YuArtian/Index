"""
Embedding providers package.
"""

from .base import EmbeddingProvider
from .openai import OpenAIEmbeddingProvider
from .local import LocalEmbeddingProvider


def create_embedding_provider(
    provider: str,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
) -> EmbeddingProvider:
    """
    Factory function to create embedding provider.

    Args:
        provider: Provider type ("openai", "siliconflow", "local")
        api_key: API key for remote providers
        base_url: Base URL for API
        model: Model name

    Returns:
        EmbeddingProvider instance
    """
    if provider in ("openai", "siliconflow"):
        if not api_key:
            raise ValueError(f"{provider} requires an API key")
        return OpenAIEmbeddingProvider(
            api_key=api_key,
            base_url=base_url or "https://api.openai.com/v1",
            model=model or "text-embedding-3-small",
        )
    elif provider == "local":
        return LocalEmbeddingProvider(model=model or "all-MiniLM-L6-v2")
    else:
        raise ValueError(f"Unknown embedding provider: {provider}")


__all__ = [
    "EmbeddingProvider",
    "OpenAIEmbeddingProvider",
    "LocalEmbeddingProvider",
    "create_embedding_provider",
]
