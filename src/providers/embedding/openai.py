"""
OpenAI-compatible embedding provider.

Works with OpenAI, SiliconFlow, and other OpenAI-compatible APIs.
"""

import httpx

from .base import EmbeddingProvider


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """
    Embedding provider using OpenAI-compatible API.

    Supports OpenAI, SiliconFlow, Azure OpenAI, and other compatible APIs.
    """

    # Known model dimensions
    MODEL_DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
        "BAAI/bge-large-zh-v1.5": 1024,
        "BAAI/bge-small-zh-v1.5": 512,
        "BAAI/bge-m3": 1024,
    }

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "text-embedding-3-small",
        timeout: float = 30.0,
    ):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._dimension: int | None = self.MODEL_DIMENSIONS.get(model)

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def dimension(self) -> int:
        if self._dimension is None:
            raise ValueError(
                f"Unknown dimension for model {self._model}. "
                "Call embed() first to auto-detect."
            )
        return self._dimension

    async def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        embeddings = await self._call_api([text.strip()])
        return embeddings[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []

        valid_texts = [t.strip() for t in texts if t and t.strip()]
        if not valid_texts:
            return []

        return await self._call_api(valid_texts)

    async def _call_api(self, texts: list[str]) -> list[list[float]]:
        """Call the embedding API."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={"model": self._model, "input": texts},
            )

            if response.status_code != 200:
                raise RuntimeError(
                    f"Embedding API error ({response.status_code}): {response.text}"
                )

            data = response.json()
            embeddings = [item["embedding"] for item in data["data"]]

            # Auto-detect dimension
            if self._dimension is None and embeddings:
                self._dimension = len(embeddings[0])

            return embeddings
