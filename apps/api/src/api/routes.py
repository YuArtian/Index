"""
API routes definition.
"""

from fastapi import APIRouter, HTTPException

from ..services import KnowledgeService, SearchService
from .models import (
    IndexRequest,
    IndexResponse,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    DocumentsResponse,
    DocumentInfo,
    StatsResponse,
    DeleteResponse,
)


def create_router(
    knowledge_service: KnowledgeService,
    search_service: SearchService,
    version: str = "0.2.0",
) -> APIRouter:
    """
    Create API router with all endpoints.

    Args:
        knowledge_service: Knowledge service instance
        search_service: Search service instance
        version: API version

    Returns:
        Configured APIRouter
    """
    router = APIRouter()

    @router.get("/", response_model=StatsResponse)
    async def get_stats():
        """Get knowledge base statistics and health check."""
        stats = knowledge_service.get_stats()
        return StatsResponse(
            name="Index",
            version=version,
            embedding_provider=knowledge_service._embedding.__class__.__name__,
            embedding_model=stats["embedding_model"],
            total_chunks=stats["total_chunks"],
        )

    @router.post("/index", response_model=IndexResponse)
    async def index_document(request: IndexRequest):
        """Index a document for semantic search."""
        try:
            result = await knowledge_service.index_document(
                content=request.content,
                source=request.source or "unknown",
                metadata=request.metadata,
                file_type=request.file_type or "text",
            )

            return IndexResponse(
                success=result.success,
                doc_id=result.doc_id,
                chunks_count=result.chunks_count,
                message=result.message,
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/search", response_model=SearchResponse)
    async def search_documents(request: SearchRequest):
        """Search for similar documents."""
        try:
            results = await search_service.search(
                query=request.query,
                top_k=request.top_k or 5,
            )

            return SearchResponse(
                results=[
                    SearchResultItem(
                        content=r.content,
                        source=r.source,
                        score=r.score,
                        metadata=r.metadata,
                    )
                    for r in results
                ],
                total=len(results),
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/documents", response_model=DocumentsResponse)
    async def list_documents():
        """List all indexed documents."""
        try:
            documents = knowledge_service.list_documents()

            return DocumentsResponse(
                documents=[
                    DocumentInfo(
                        id=doc.id,
                        source=doc.source,
                        chunk_index=doc.chunk_index,
                        created_at=doc.created_at,
                    )
                    for doc in documents
                ],
                total=len(documents),
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.delete("/documents/{doc_id}", response_model=DeleteResponse)
    async def delete_document(doc_id: str):
        """Delete a document by ID."""
        try:
            success = knowledge_service.delete_document(doc_id)

            if not success:
                raise HTTPException(
                    status_code=404, detail=f"Document {doc_id} not found"
                )

            return DeleteResponse(
                success=True,
                message=f"Successfully deleted document {doc_id}",
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return router
