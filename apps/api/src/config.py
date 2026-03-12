"""
Configuration management using pydantic-settings.

Environment variables are loaded from .env at project root.
Nested settings use double underscore delimiter: DATABASE__URL, EMBEDDING__API_KEY, etc.
"""

from pathlib import Path

from pydantic_settings import BaseSettings

# Project root: Index/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class DatabaseSettings(BaseSettings):
    url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/index"


class EmbeddingSettings(BaseSettings):
    provider: str = "voyage"
    api_key: str = ""
    base_url: str = "https://api.voyageai.com/v1"
    model: str = "voyage-3.5"


class Neo4jSettings(BaseSettings):
    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: str = "neo4j_password"


class LogSettings(BaseSettings):
    level: str = "INFO"
    dir: str = str(PROJECT_ROOT / "logs")
    rotation: str = "10 MB"
    retention: str = "7 days"


class Settings(BaseSettings):
    database: DatabaseSettings = DatabaseSettings()
    embedding: EmbeddingSettings = EmbeddingSettings()
    neo4j: Neo4jSettings = Neo4jSettings()
    log: LogSettings = LogSettings()
    anthropic_api_key: str = ""
    chunk_size: int = 500
    chunk_overlap: int = 50
    cors_origins: list[str] = ["http://localhost:5173"]
    data_dir: str = str(PROJECT_ROOT / "data" / "files")

    model_config = {"env_file": "../../.env", "env_nested_delimiter": "__"}


settings = Settings()
