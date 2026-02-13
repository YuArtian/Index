"""
Local embedding provider using sentence-transformers.
"""

from .base import EmbeddingProvider


class LocalEmbeddingProvider(EmbeddingProvider):
    """
    Embedding provider using local sentence-transformers models.

    Supports any model from HuggingFace that works with sentence-transformers.
    """

    def __init__(self, model: str = "all-MiniLM-L6-v2"):
        self._model_name = model
        self._model = None
        self._dimension: int | None = None

    def _load_model(self):
        """Lazy load the model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self._model_name)
                # Get dimension from model
                self._dimension = self._model.get_sentence_embedding_dimension()
            except ImportError:
                raise RuntimeError(
                    "Local embedding requires sentence-transformers. "
                    "Install with: pip install sentence-transformers"
                )
        return self._model

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        if self._dimension is None:
            self._load_model()
        return self._dimension  # type: ignore

    async def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        model = self._load_model()
        embedding = model.encode([text.strip()])[0]
        return embedding.tolist()

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []

        valid_texts = [t.strip() for t in texts if t and t.strip()]
        if not valid_texts:
            return []

        model = self._load_model()
        embeddings = model.encode(valid_texts)
        return [emb.tolist() for emb in embeddings]
