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
    if provider in ("openai", "siliconflow", "voyage"):
        if not api_key:
            raise ValueError(f"{provider} requires an API key")

        defaults = {
            "openai": ("https://api.openai.com/v1", "text-embedding-3-small"),
            "siliconflow": ("https://api.siliconflow.cn/v1", "BAAI/bge-m3"),
            "voyage": ("https://api.voyageai.com/v1", "voyage-3.5"),
        }
        default_url, default_model = defaults[provider]

        return OpenAIEmbeddingProvider(
            api_key=api_key,
            base_url=base_url or default_url,
            model=model or default_model,
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
