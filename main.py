"""
Index - Local Knowledge Base with Semantic Search

A minimal MVP for indexing and searching documents using vector embeddings.
"""

import os
import uuid
from datetime import datetime, timezone
from typing import Optional

import chromadb
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# =============================================================================
# Configuration
# =============================================================================

CHROMA_PATH = os.getenv("CHROMA_PATH", "./data/chroma")
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

# Determine embedding provider
if SILICONFLOW_API_KEY:
    EMBEDDING_PROVIDER = "siliconflow"
    EMBEDDING_API_KEY = SILICONFLOW_API_KEY
    EMBEDDING_BASE_URL = "https://api.siliconflow.cn/v1"
    EMBEDDING_MODEL = EMBEDDING_MODEL or "BAAI/bge-large-zh-v1.5"
elif OPENAI_API_KEY:
    EMBEDDING_PROVIDER = "openai"
    EMBEDDING_API_KEY = OPENAI_API_KEY
    EMBEDDING_BASE_URL = "https://api.openai.com/v1"
    EMBEDDING_MODEL = EMBEDDING_MODEL or "text-embedding-3-small"
else:
    EMBEDDING_PROVIDER = "local"
    EMBEDDING_API_KEY = None
    EMBEDDING_BASE_URL = None
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# =============================================================================
# Embedding Service
# =============================================================================


class EmbeddingService:
    """Embedding service with API and local fallback support."""

    def __init__(self):
        self.provider = EMBEDDING_PROVIDER
        self.model = EMBEDDING_MODEL
        self.api_key = EMBEDDING_API_KEY
        self.base_url = EMBEDDING_BASE_URL
        self._local_model = None

    async def get_embedding(self, text: str) -> list[float]:
        """Get embedding for a single text."""
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        if self.provider in ("siliconflow", "openai"):
            return await self._get_api_embedding(text.strip())
        else:
            return self._get_local_embedding(text.strip())

    async def get_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Get embeddings for multiple texts."""
        if not texts:
            return []

        valid_texts = [t.strip() for t in texts if t and t.strip()]
        if not valid_texts:
            return []

        if self.provider in ("siliconflow", "openai"):
            return await self._get_api_embeddings_batch(valid_texts)
        else:
            return self._get_local_embeddings_batch(valid_texts)

    async def _get_api_embedding(self, text: str) -> list[float]:
        """Get embedding from API."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={"model": self.model, "input": text},
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Embedding API error: {response.text}",
                )

            data = response.json()
            return data["data"][0]["embedding"]

    async def _get_api_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Get embeddings from API in batch."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={"model": self.model, "input": texts},
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Embedding API error: {response.text}",
                )

            data = response.json()
            return [item["embedding"] for item in data["data"]]

    def _load_local_model(self):
        """Load local sentence-transformers model."""
        if self._local_model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._local_model = SentenceTransformer(self.model)
            except ImportError:
                raise HTTPException(
                    status_code=500,
                    detail="Local embedding requires sentence-transformers. "
                    "Install with: pip install sentence-transformers",
                )
        return self._local_model

    def _get_local_embedding(self, text: str) -> list[float]:
        """Get embedding from local model."""
        model = self._load_local_model()
        embedding = model.encode([text])[0]
        return embedding.tolist()

    def _get_local_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Get embeddings from local model in batch."""
        model = self._load_local_model()
        embeddings = model.encode(texts)
        return [emb.tolist() for emb in embeddings]


# =============================================================================
# ChromaDB Storage
# =============================================================================


class ChromaStorage:
    """ChromaDB storage for vector search."""

    def __init__(self, path: str = CHROMA_PATH, collection_name: str = "index_kb"):
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict] | None = None,
    ):
        """Add documents to the collection."""
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> dict:
        """Search for similar documents."""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        return results

    def get_all_documents(self) -> dict:
        """Get all documents in the collection."""
        return self.collection.get(include=["metadatas"])

    def delete_document(self, doc_id: str):
        """Delete a document by ID."""
        self.collection.delete(ids=[doc_id])

    def count(self) -> int:
        """Get the number of documents."""
        return self.collection.count()


# =============================================================================
# Text Chunking
# =============================================================================


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks."""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap

    return chunks


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Index",
    description="Local Knowledge Base with Semantic Search",
    version="0.1.0",
)

# Initialize services
embedding_service = EmbeddingService()
storage = ChromaStorage()


# Request/Response Models
class IndexRequest(BaseModel):
    content: str
    source: Optional[str] = "unknown"
    metadata: Optional[dict] = None


class IndexResponse(BaseModel):
    success: bool
    doc_id: str
    chunks_count: int
    message: str


class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


class SearchResult(BaseModel):
    content: str
    source: str
    score: float
    metadata: dict


class SearchResponse(BaseModel):
    results: list[SearchResult]
    total: int


class DocumentInfo(BaseModel):
    id: str
    source: str
    chunk_index: int
    created_at: str


class DocumentsResponse(BaseModel):
    documents: list[DocumentInfo]
    total: int


# API Endpoints
@app.get("/")
async def root():
    """Health check and system info."""
    return {
        "name": "Index",
        "version": "0.1.0",
        "embedding_provider": embedding_service.provider,
        "embedding_model": embedding_service.model,
        "documents_count": storage.count(),
    }


@app.post("/index", response_model=IndexResponse)
async def index_document(request: IndexRequest):
    """Index a document for semantic search."""
    try:
        # Split text into chunks
        chunks = chunk_text(request.content)

        # Generate document ID
        doc_id = str(uuid.uuid4())[:8]
        created_at = datetime.now(timezone.utc).isoformat()

        # Get embeddings for all chunks
        embeddings = await embedding_service.get_embeddings_batch(chunks)

        # Prepare data for storage
        ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "doc_id": doc_id,
                "source": request.source or "unknown",
                "chunk_index": i,
                "created_at": created_at,
                **(request.metadata or {}),
            }
            for i in range(len(chunks))
        ]

        # Store in ChromaDB
        storage.add_documents(
            ids=ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        return IndexResponse(
            success=True,
            doc_id=doc_id,
            chunks_count=len(chunks),
            message=f"Successfully indexed {len(chunks)} chunks",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """Search for similar documents."""
    try:
        # Get query embedding
        query_embedding = await embedding_service.get_embedding(request.query)

        # Search in ChromaDB
        results = storage.search(query_embedding, top_k=request.top_k)

        # Format results
        search_results = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 0

                # Convert distance to similarity score (cosine distance to similarity)
                score = 1 - distance

                search_results.append(
                    SearchResult(
                        content=doc,
                        source=metadata.get("source", "unknown"),
                        score=round(score, 4),
                        metadata=metadata,
                    )
                )

        return SearchResponse(results=search_results, total=len(search_results))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents", response_model=DocumentsResponse)
async def list_documents():
    """List all indexed documents."""
    try:
        all_docs = storage.get_all_documents()

        documents = []
        if all_docs["ids"]:
            for i, doc_id in enumerate(all_docs["ids"]):
                metadata = all_docs["metadatas"][i] if all_docs["metadatas"] else {}
                documents.append(
                    DocumentInfo(
                        id=doc_id,
                        source=metadata.get("source", "unknown"),
                        chunk_index=metadata.get("chunk_index", 0),
                        created_at=metadata.get("created_at", ""),
                    )
                )

        return DocumentsResponse(documents=documents, total=len(documents))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document by ID."""
    try:
        storage.delete_document(doc_id)
        return {"success": True, "message": f"Deleted document {doc_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    print(f"Starting Index server...")
    print(f"Embedding provider: {embedding_service.provider}")
    print(f"Embedding model: {embedding_service.model}")
    print(f"ChromaDB path: {CHROMA_PATH}")
    print(f"API docs: http://localhost:8000/docs")

    uvicorn.run(app, host="0.0.0.0", port=8000)
