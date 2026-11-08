import asyncio
from sentence_transformers import SentenceTransformer


class EmbeddingService:

    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM = 384

    def __init__(self):
        self.model = SentenceTransformer(self.MODEL_NAME)

    def _encode(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True
        )
        return embeddings.tolist()


    async def embed_texts(
        self,
        texts: list[str]
    ) -> list[list[float]]:

        if not texts:
            return []

        if any(not text or not text.strip() for text in texts):
            raise ValueError("Texts cannot contain empty values")

        return await asyncio.to_thread(
            self._encode,
            texts
        )

    async def embed_text(self, text: str) -> list[float]:

        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        embeddings = await self.embed_texts([text])
        return embeddings[0]