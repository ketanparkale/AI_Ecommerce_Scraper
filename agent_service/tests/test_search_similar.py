
import asyncio

from app.database.redis_client import connect_redis, close_redis
from app.rag.redis_review_store import RedisReviewStore
from app.services.embedding_service import EmbeddingService


async def main():
    try:
        await connect_redis()

        store = RedisReviewStore()

        embedding_service = EmbeddingService()

        query = "Are these shoes comfortable for long-distance running?"

        query_embedding = await embedding_service.embed_text(query)
        normal_reviews = await store.search(
            product_id="itm0d1fb35c1614b",
            limit=10
        )
        similar_reviews = await store.search_similar(
            product_id="itm0d1fb35c1614b",
            embedding=query_embedding,
            limit=10,
            max_distance=0.60,
        )

    finally:
        await close_redis()


if __name__ == "__main__":
    asyncio.run(main())
