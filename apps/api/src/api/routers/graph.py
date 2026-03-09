"""
Knowledge graph API routes.
"""

from fastapi import APIRouter, Query

from ...services.graph import GraphService


def init_router(graph_service: GraphService) -> APIRouter:
    router = APIRouter(prefix="/graph", tags=["graph"])

    @router.get("")
    async def get_graph(limit: int = Query(200, ge=1, le=1000)):
        """Get the full knowledge graph for visualization."""
        return await graph_service.get_graph(limit=limit)

    @router.get("/stats")
    async def get_stats():
        """Get graph statistics (concept count, relation count)."""
        return await graph_service.get_stats()

    @router.get("/search")
    async def search_concepts(
        q: str = Query(..., min_length=1),
        limit: int = Query(20, ge=1, le=100),
    ):
        """Search concepts by name."""
        return await graph_service.search_concepts(query=q, limit=limit)

    @router.get("/neighbors/{concept_name}")
    async def get_neighbors(
        concept_name: str,
        depth: int = Query(2, ge=1, le=5),
    ):
        """Get a concept and its neighbors up to N hops."""
        return await graph_service.get_neighbors(concept_name, depth=depth)

    return router
