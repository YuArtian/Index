"""
Configuration management using pydantic-settings.

Environment variables are loaded from .env at project root.
Nested settings use double underscore delimiter: DATABASE__URL, EMBEDDING__API_KEY, etc.
"""

from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/index"


class EmbeddingSettings(BaseSettings):
    provider: str = "siliconflow"
    api_key: str = ""
    base_url: str = "https://api.siliconflow.cn/v1"
    model: str = "BAAI/bge-large-zh-v1.5"


class Settings(BaseSettings):
    database: DatabaseSettings = DatabaseSettings()
    embedding: EmbeddingSettings = EmbeddingSettings()
    anthropic_api_key: str = ""
    chunk_size: int = 500
    chunk_overlap: int = 50
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = {"env_file": "../../.env", "env_nested_delimiter": "__"}


settings = Settings()
