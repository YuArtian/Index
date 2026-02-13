"""
PostgreSQL + pgvector storage provider.
"""

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import async_sessionmaker

from .base import StorageProvider, SearchResult
from ...models.chunk import Chunk
from ...models.document import Document


class PgvectorStorageProvider(StorageProvider):
    """Storage provider using PostgreSQL + pgvector."""

    def __init__(self, session_factory: async_sessionmaker):
        self._session_factory = session_factory

    async def add(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict] | None = None,
    ) -> None:
        """Add chunks to PostgreSQL."""
        async with self._session_factory() as session:
            for i, id_ in enumerate(ids):
                meta = metadatas[i] if metadatas else {}
                chunk = Chunk(
                    id=id_,
                    content=documents[i],
                    embedding=embeddings[i],
                    doc_id=meta.get("doc_id", ""),
                    source=meta.get("source"),
                    chunk_index=meta.get("chunk_index", 0),
                    metadata_=meta,
                )
                session.add(chunk)
            await session.commit()

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filter_metadata: dict | None = None,
    ) -> list[SearchResult]:
        """Search for similar chunks using cosine distance."""
        async with self._session_factory() as session:
            distance = Chunk.embedding.cosine_distance(query_embedding)
            query = select(Chunk, distance.label("distance"))

            if filter_metadata:
                if "doc_id" in filter_metadata:
                    query = query.where(Chunk.doc_id == filter_metadata["doc_id"])

            query = query.order_by(distance).limit(top_k)
            result = await session.execute(query)

            return [
                SearchResult(
                    id=row.Chunk.id,
                    content=row.Chunk.content,
                    score=round(1 - row.distance, 4),
                    metadata={**(row.Chunk.metadata_ or {}), "source": row.Chunk.source or ""},
                )
                for row in result
            ]

    async def get_all(self) -> list[dict]:
        """Get all chunks."""
        async with self._session_factory() as session:
            result = await session.execute(select(Chunk))
            return [
                {
                    "id": chunk.id,
                    "metadata": {
                        **(chunk.metadata_ or {}),
                        "doc_id": chunk.doc_id,
                        "source": chunk.source or "",
                        "chunk_index": chunk.chunk_index or 0,
                    },
                }
                for chunk in result.scalars()
            ]

    async def delete(self, ids: list[str]) -> None:
        """Delete chunks by IDs."""
        async with self._session_factory() as session:
            await session.execute(delete(Chunk).where(Chunk.id.in_(ids)))
            await session.commit()

    async def delete_by_doc_id(self, doc_id: str) -> None:
        """Delete all chunks belonging to a document."""
        async with self._session_factory() as session:
            await session.execute(delete(Chunk).where(Chunk.doc_id == doc_id))
            await session.execute(delete(Document).where(Document.id == doc_id))
            await session.commit()

    async def count(self) -> int:
        """Get total chunk count."""
        async with self._session_factory() as session:
            result = await session.scalar(select(func.count(Chunk.id)))
            return result or 0
