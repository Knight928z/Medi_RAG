import asyncio
from typing import List

from sentence_transformers import SentenceTransformer


class EmbeddingProvider:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts, normalize_embeddings=True).tolist()

    async def embed_async(self, texts: List[str]) -> List[List[float]]:
        return await asyncio.to_thread(self.embed, texts)
