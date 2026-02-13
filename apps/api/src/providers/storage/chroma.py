"""
ChromaDB storage provider.
"""

import chromadb

from .base import StorageProvider, SearchResult


class ChromaStorageProvider(StorageProvider):
    """
    Storage provider using ChromaDB.

    ChromaDB is an embedded vector database that stores data locally.
    """

    def __init__(
        self,
        path: str = "./data/chroma",
        collection_name: str = "index_kb",
    ):
        self._path = path
        self._collection_name = collection_name
        self._client = chromadb.PersistentClient(path=path)
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    @property
    def collection_name(self) -> str:
        return self._collection_name

    def add(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict] | None = None,
    ) -> None:
        """Add documents to ChromaDB."""
        self._collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filter_metadata: dict | None = None,
    ) -> list[SearchResult]:
        """Search for similar documents in ChromaDB."""
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_metadata,
            include=["documents", "metadatas", "distances"],
        )

        search_results = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 0

                # Convert cosine distance to similarity score
                score = 1 - distance

                search_results.append(
                    SearchResult(
                        id=results["ids"][0][i],
                        content=doc,
                        score=round(score, 4),
                        metadata=metadata,
                    )
                )

        return search_results

    def get_all(self) -> list[dict]:
        """Get all documents from ChromaDB."""
        results = self._collection.get(include=["metadatas"])

        documents = []
        if results["ids"]:
            for i, doc_id in enumerate(results["ids"]):
                metadata = results["metadatas"][i] if results["metadatas"] else {}
                documents.append(
                    {
                        "id": doc_id,
                        "metadata": metadata,
                    }
                )

        return documents

    def delete(self, ids: list[str]) -> None:
        """Delete documents from ChromaDB."""
        self._collection.delete(ids=ids)

    def count(self) -> int:
        """Get document count in ChromaDB."""
        return self._collection.count()
