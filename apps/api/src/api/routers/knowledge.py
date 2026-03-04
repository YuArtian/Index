"""Knowledge base routes — index, search, documents."""

from fastapi import APIRouter, Form, HTTPException, UploadFile, File

from ...services import KnowledgeService, SearchService
from ...providers.parser.file_extractor import extract_text, get_file_type, SUPPORTED_EXTENSIONS
from ..models import (
    IndexRequest,
    IndexResponse,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    DocumentResponse,
    DocumentsResponse,
    StatsResponse,
    DeleteResponse,
)

router = APIRouter(tags=["Knowledge"])


def init_router(
    knowledge_service: KnowledgeService,
    search_service: SearchService,
    anthropic_api_key: str = "",
) -> APIRouter:
    """Initialize knowledge router with service instances."""

    @router.get("/", response_model=StatsResponse)
    async def get_stats():
        """Health check + knowledge base stats."""
        stats = await knowledge_service.get_stats()
        return StatsResponse(
            name="Index",
            version="0.3.0",
            embedding_provider=knowledge_service._embedding.__class__.__name__,
            embedding_model=stats["embedding_model"],
            total_chunks=stats["total_chunks"],
        )

    @router.post("/index", response_model=IndexResponse)
    async def index_document(request: IndexRequest):
        """Index a document for semantic search."""
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

    @router.post("/search", response_model=SearchResponse)
    async def search_documents(request: SearchRequest):
        """Search for similar documents."""
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

    @router.get("/documents", response_model=DocumentsResponse)
    async def list_documents():
        """List all indexed documents."""
        documents = await knowledge_service.list_documents()
        return DocumentsResponse(
            documents=[
                DocumentResponse(
                    id=doc.id,
                    filename=doc.filename,
                    source=doc.source or "",
                    status=doc.status,
                    chunk_count=doc.chunk_count,
                    created_at=doc.created_at.isoformat() if doc.created_at else "",
                )
                for doc in documents
            ],
            total=len(documents),
        )

    @router.delete("/documents/{doc_id}", response_model=DeleteResponse)
    async def delete_document(doc_id: str):
        """Delete a document by ID."""
        success = await knowledge_service.delete_document(doc_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
        return DeleteResponse(success=True, message=f"Deleted document {doc_id}")

    @router.post("/upload", response_model=IndexResponse)
    async def upload_file(
        file: UploadFile = File(...),
        high_quality: bool = Form(False),
    ):
        """Upload a file and index it. Supports: """ + ", ".join(sorted(SUPPORTED_EXTENSIONS))
        filename = file.filename or "upload"
        if get_file_type(filename) is None:
            supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported file type. Supported extensions: {supported}",
            )
        data = await file.read()
        try:
            text, parser_type = await extract_text(filename, data, anthropic_api_key, high_quality)
        except (ValueError, RuntimeError) as e:
            raise HTTPException(status_code=422, detail=str(e))
        if not text.strip():
            raise HTTPException(status_code=422, detail="No text content found in file")
        result = await knowledge_service.index_document(
            content=text,
            source=filename,
            file_type=parser_type,
        )
        return IndexResponse(
            success=result.success,
            doc_id=result.doc_id,
            chunks_count=result.chunks_count,
            message=result.message,
        )

    return router
