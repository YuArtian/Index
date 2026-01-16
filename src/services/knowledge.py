"""
Knowledge service - handles document indexing and management.
"""

import uuid
from datetime import datetime, timezone
from dataclasses import dataclass

from ..providers.embedding import EmbeddingProvider
from ..providers.storage import StorageProvider
from ..providers.parser import ParserProvider, create_parser


@dataclass
class IndexResult:
    """Result of indexing operation."""

    success: bool
    doc_id: str
    chunks_count: int
    message: str


@dataclass
class DocumentInfo:
    """Document information."""

    id: str
    source: str
    chunk_index: int
    created_at: str


class KnowledgeService:
    """
    Service for managing knowledge base documents.

    Handles document indexing, retrieval, and deletion.
    """

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        storage_provider: StorageProvider,
        default_chunk_size: int = 500,
        default_chunk_overlap: int = 50,
    ):
        self._embedding = embedding_provider
        self._storage = storage_provider
        self._chunk_size = default_chunk_size
        self._chunk_overlap = default_chunk_overlap

    async def index_document(
        self,
        content: str,
        source: str = "unknown",
        metadata: dict | None = None,
        file_type: str = "text",
    ) -> IndexResult:
        """
        Index a document into the knowledge base.

        Args:
            content: Document content
            source: Source identifier
            metadata: Optional metadata
            file_type: Content type ("text", "markdown")

        Returns:
            IndexResult with operation details
        """
        # Create parser for the file type
        parser = create_parser(
            file_type=file_type,
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
        )

        # Parse content into chunks
        parsed = parser.parse(content, metadata)

        if not parsed.chunks:
            return IndexResult(
                success=False,
                doc_id="",
                chunks_count=0,
                message="No content to index",
            )

        # Generate document ID
        doc_id = str(uuid.uuid4())[:8]
        created_at = datetime.now(timezone.utc).isoformat()

        # Get embeddings for all chunks
        chunk_contents = [chunk.content for chunk in parsed.chunks]
        embeddings = await self._embedding.embed_batch(chunk_contents)

        # Prepare data for storage
        ids = [f"{doc_id}_{chunk.index}" for chunk in parsed.chunks]
        metadatas = [
            {
                "doc_id": doc_id,
                "source": source,
                "chunk_index": chunk.index,
                "created_at": created_at,
                **(metadata or {}),
                **chunk.metadata,
            }
            for chunk in parsed.chunks
        ]

        # Store in storage provider
        self._storage.add(
            ids=ids,
            documents=chunk_contents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        return IndexResult(
            success=True,
            doc_id=doc_id,
            chunks_count=len(parsed.chunks),
            message=f"Successfully indexed {len(parsed.chunks)} chunks",
        )

    async def index_file(
        self,
        file_path: str,
        metadata: dict | None = None,
    ) -> IndexResult:
        """
        Index a file into the knowledge base.

        Args:
            file_path: Path to the file
            metadata: Optional metadata

        Returns:
            IndexResult with operation details
        """
        # Determine file type from extension
        file_type = "text"
        if file_path.endswith((".md", ".markdown")):
            file_type = "markdown"

        # Create parser and parse file
        parser = create_parser(
            file_type=file_type,
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
        )

        parsed = parser.parse_file(file_path)

        if not parsed.chunks:
            return IndexResult(
                success=False,
                doc_id="",
                chunks_count=0,
                message="No content to index",
            )

        # Generate document ID
        doc_id = str(uuid.uuid4())[:8]
        created_at = datetime.now(timezone.utc).isoformat()

        # Get embeddings
        chunk_contents = [chunk.content for chunk in parsed.chunks]
        embeddings = await self._embedding.embed_batch(chunk_contents)

        # Prepare storage data
        ids = [f"{doc_id}_{chunk.index}" for chunk in parsed.chunks]
        metadatas = [
            {
                "doc_id": doc_id,
                "chunk_index": chunk.index,
                "created_at": created_at,
                **(parsed.metadata or {}),
                **(metadata or {}),
                **chunk.metadata,
            }
            for chunk in parsed.chunks
        ]

        # Store
        self._storage.add(
            ids=ids,
            documents=chunk_contents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        return IndexResult(
            success=True,
            doc_id=doc_id,
            chunks_count=len(parsed.chunks),
            message=f"Successfully indexed {len(parsed.chunks)} chunks from {file_path}",
        )

    def list_documents(self) -> list[DocumentInfo]:
        """
        List all documents in the knowledge base.

        Returns:
            List of DocumentInfo objects
        """
        all_docs = self._storage.get_all()

        documents = []
        for doc in all_docs:
            metadata = doc.get("metadata", {})
            documents.append(
                DocumentInfo(
                    id=doc["id"],
                    source=metadata.get("source", "unknown"),
                    chunk_index=metadata.get("chunk_index", 0),
                    created_at=metadata.get("created_at", ""),
                )
            )

        return documents

    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document by ID.

        Args:
            doc_id: Document ID (can be full chunk ID or doc_id prefix)

        Returns:
            True if deleted, False if not found
        """
        # Get all documents and find matching ones
        all_docs = self._storage.get_all()

        ids_to_delete = []
        for doc in all_docs:
            metadata = doc.get("metadata", {})
            if doc["id"] == doc_id or metadata.get("doc_id") == doc_id:
                ids_to_delete.append(doc["id"])

        if not ids_to_delete:
            return False

        self._storage.delete(ids_to_delete)
        return True

    def get_stats(self) -> dict:
        """
        Get knowledge base statistics.

        Returns:
            Dictionary with stats
        """
        return {
            "total_chunks": self._storage.count(),
            "embedding_model": self._embedding.model_name,
        }
