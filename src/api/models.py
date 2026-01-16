"""
Pydantic models for API request/response.
"""

from typing import Optional
from pydantic import BaseModel


# Request Models
class IndexRequest(BaseModel):
    """Request to index a document."""

    content: str
    source: Optional[str] = "unknown"
    metadata: Optional[dict] = None
    file_type: Optional[str] = "text"  # "text" or "markdown"


class SearchRequest(BaseModel):
    """Request to search documents."""

    query: str
    top_k: Optional[int] = 5


# Response Models
class IndexResponse(BaseModel):
    """Response from index operation."""

    success: bool
    doc_id: str
    chunks_count: int
    message: str


class SearchResultItem(BaseModel):
    """Single search result item."""

    content: str
    source: str
    score: float
    metadata: dict


class SearchResponse(BaseModel):
    """Response from search operation."""

    results: list[SearchResultItem]
    total: int


class DocumentInfo(BaseModel):
    """Document information."""

    id: str
    source: str
    chunk_index: int
    created_at: str


class DocumentsResponse(BaseModel):
    """Response with list of documents."""

    documents: list[DocumentInfo]
    total: int


class StatsResponse(BaseModel):
    """Response with knowledge base stats."""

    name: str
    version: str
    embedding_provider: str
    embedding_model: str
    total_chunks: int


class DeleteResponse(BaseModel):
    """Response from delete operation."""

    success: bool
    message: str
