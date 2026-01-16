"""
Configuration management for Index.

All configuration is loaded from environment variables with sensible defaults.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class EmbeddingConfig:
    """Embedding service configuration."""

    provider: str  # "openai", "siliconflow", "local"
    api_key: str | None
    base_url: str | None
    model: str


@dataclass
class StorageConfig:
    """Storage service configuration."""

    provider: str  # "chroma", "pgvector", "milvus"
    path: str  # For file-based storage
    collection_name: str


@dataclass
class Config:
    """Application configuration."""

    embedding: EmbeddingConfig
    storage: StorageConfig
    chunk_size: int
    chunk_overlap: int


def load_config() -> Config:
    """Load configuration from environment variables."""

    # Determine embedding provider
    siliconflow_key = os.getenv("SILICONFLOW_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if siliconflow_key:
        embedding_config = EmbeddingConfig(
            provider="siliconflow",
            api_key=siliconflow_key,
            base_url="https://api.siliconflow.cn/v1",
            model=os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-zh-v1.5"),
        )
    elif openai_key:
        embedding_config = EmbeddingConfig(
            provider="openai",
            api_key=openai_key,
            base_url="https://api.openai.com/v1",
            model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
        )
    else:
        embedding_config = EmbeddingConfig(
            provider="local",
            api_key=None,
            base_url=None,
            model=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
        )

    # Storage configuration
    storage_config = StorageConfig(
        provider=os.getenv("STORAGE_PROVIDER", "chroma"),
        path=os.getenv("STORAGE_PATH", "./data/chroma"),
        collection_name=os.getenv("COLLECTION_NAME", "index_kb"),
    )

    return Config(
        embedding=embedding_config,
        storage=storage_config,
        chunk_size=int(os.getenv("CHUNK_SIZE", "500")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "50")),
    )


# Global config instance
config = load_config()
