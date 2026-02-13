"""
Pydantic models for API request/response.
"""

from pydantic import BaseModel


# Request Models
class IndexRequest(BaseModel):
    content: str
    source: str | None = "unknown"
    metadata: dict | None = None
    file_type: str | None = "text"


class SearchRequest(BaseModel):
    query: str
    top_k: int | None = 5


# Response Models
class IndexResponse(BaseModel):
    success: bool
    doc_id: str
    chunks_count: int
    message: str


class SearchResultItem(BaseModel):
    content: str
    source: str
    score: float
    metadata: dict


class SearchResponse(BaseModel):
    results: list[SearchResultItem]
    total: int


class DocumentResponse(BaseModel):
    id: str
    filename: str
    source: str
    status: str
    chunk_count: int
    created_at: str


class DocumentsResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int


class StatsResponse(BaseModel):
    name: str
    version: str
    embedding_provider: str
    embedding_model: str
    total_chunks: int


class DeleteResponse(BaseModel):
    success: bool
    message: str
