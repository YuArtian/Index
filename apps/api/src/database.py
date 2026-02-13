"""
SQLAlchemy async engine and session management.
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from .config import settings

engine = create_async_engine(settings.database.url, pool_size=5, max_overflow=10)

async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_session() -> AsyncSession:
    """Dependency: yield a database session."""
    async with async_session() as session:
        yield session


async def init_db():
    """Initialize database connection (called at startup)."""
    pass


async def close_db():
    """Dispose engine (called at shutdown)."""
    await engine.dispose()
