"""
Knowledge service - handles document indexing and management.

Updated: storage calls are now async, documents table tracks processing status.
"""

import uuid
from dataclasses import dataclass

from loguru import logger
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..models.document import Document
from ..providers.embedding import EmbeddingProvider
from ..providers.storage import StorageProvider
from ..providers.parser import create_parser
from .graph import GraphService


@dataclass
class IndexResult:
    success: bool
    doc_id: str
    chunks_count: int
    message: str


class KnowledgeService:
    """Service for managing knowledge base documents."""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        storage_provider: StorageProvider,
        session_factory: async_sessionmaker,
        default_chunk_size: int = 500,
        default_chunk_overlap: int = 50,
        graph_service: GraphService | None = None,
    ):
        self._embedding = embedding_provider
        self._storage = storage_provider
        self._session_factory = session_factory
        self._chunk_size = default_chunk_size
        self._chunk_overlap = default_chunk_overlap
        self._graph = graph_service

    async def index_document(
        self,
        content: str,
        source: str = "unknown",
        metadata: dict | None = None,
        file_type: str = "text",
    ) -> IndexResult:
        """Index a document: parse → embed → store in pgvector."""
        doc_id = str(uuid.uuid4())

        # Create document record
        async with self._session_factory() as session:
            doc = Document(
                id=doc_id,
                filename=source,
                source=source,
                content_type=file_type,
                status="parsing",
                file_size=len(content.encode()),
            )
            session.add(doc)
            await session.commit()

        try:
            # Parse
            parser = create_parser(
                file_type=file_type,
                chunk_size=self._chunk_size,
                chunk_overlap=self._chunk_overlap,
            )
            parsed = parser.parse(content, metadata)

            if not parsed.chunks:
                async with self._session_factory() as session:
                    doc = await session.get(Document, doc_id)
                    doc.status = "error"
                    doc.error_message = "No content to index"
                    await session.commit()
                return IndexResult(False, doc_id, 0, "No content to index")

            # Update status to indexing
            async with self._session_factory() as session:
                doc = await session.get(Document, doc_id)
                doc.status = "indexing"
                await session.commit()

            # Embed
            chunk_contents = [chunk.content for chunk in parsed.chunks]
            embeddings = await self._embedding.embed_batch(chunk_contents)

            # Store chunks
            ids = [f"{doc_id}_{chunk.index}" for chunk in parsed.chunks]
            metadatas = [
                {
                    "doc_id": doc_id,
                    "source": source,
                    "chunk_index": chunk.index,
                    **(metadata or {}),
                    **chunk.metadata,
                }
                for chunk in parsed.chunks
            ]

            await self._storage.add(
                ids=ids,
                documents=chunk_contents,
                embeddings=embeddings,
                metadatas=metadatas,
            )

            # Mark as ready
            async with self._session_factory() as session:
                doc = await session.get(Document, doc_id)
                doc.status = "ready"
                doc.chunk_count = len(parsed.chunks)
                await session.commit()

            # Extract concepts to knowledge graph
            if self._graph:
                try:
                    await self._graph.extract_and_save(
                        chunks=chunk_contents,
                        doc_id=doc_id,
                        chunk_ids=ids,
                    )
                except Exception as e:
                    logger.warning(f"Concept extraction failed for {doc_id}: {e}")

            logger.info(f"Indexed document {doc_id}: {len(parsed.chunks)} chunks from {source}")

            return IndexResult(
                success=True,
                doc_id=doc_id,
                chunks_count=len(parsed.chunks),
                message=f"Successfully indexed {len(parsed.chunks)} chunks",
            )

        except Exception as e:
            async with self._session_factory() as session:
                doc = await session.get(Document, doc_id)
                if doc:
                    doc.status = "error"
                    doc.error_message = str(e)
                    await session.commit()
            logger.error(f"Failed to index document {doc_id}: {e}")
            raise

    async def list_documents(self) -> list[Document]:
        """List all documents from the documents table."""
        from sqlalchemy import select
        async with self._session_factory() as session:
            result = await session.execute(
                select(Document).order_by(Document.created_at.desc())
            )
            return list(result.scalars().all())

    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document, its chunks, and the stored file."""
        import os
        # Remove stored file from disk
        file_path = await self.get_file_path(doc_id)
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Removed file {file_path}")
        await self._storage.delete_by_doc_id(doc_id)
        if self._graph:
            try:
                await self._graph.delete_document_concepts(doc_id)
            except Exception as e:
                logger.warning(f"Failed to clean graph for {doc_id}: {e}")
        logger.info(f"Deleted document {doc_id}")
        return True

    async def set_file_path(self, doc_id: str, file_path: str) -> None:
        """Store the file path for a document."""
        async with self._session_factory() as session:
            doc = await session.get(Document, doc_id)
            if doc:
                doc.file_path = file_path
                await session.commit()

    async def get_file_path(self, doc_id: str) -> str | None:
        """Get the stored file path for a document."""
        async with self._session_factory() as session:
            doc = await session.get(Document, doc_id)
            return doc.file_path if doc else None

    async def get_stats(self) -> dict:
        """Get knowledge base statistics."""
        total_chunks = await self._storage.count()
        return {
            "total_chunks": total_chunks,
            "embedding_model": self._embedding.model_name,
        }
