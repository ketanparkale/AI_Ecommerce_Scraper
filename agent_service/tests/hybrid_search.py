
import asyncio

from app.database.redis_client import connect_redis, close_redis
from app.rag.redis_review_store import RedisReviewStore
from app.services.embedding_service import EmbeddingService
from app.services.review_search_service import ReviewSearchService


PRODUCT_ID = "itmf644ddc37ea0b"


async def main():

    await connect_redis()

    try:
        repository = RedisReviewStore()
        embedding_service = EmbeddingService()

        search_service = ReviewSearchService(
            embedding_service=embedding_service,
            review_repository=repository,
        )

        query = "Has anyone mentioned negative about the sole?"

        results = await search_service.search_similar_reviews(
            product_id=PRODUCT_ID,
            query=query,
            limit=10,
            min_rating=1,
            max_rating=2,
            max_distance=0.55,
        )

    finally:
        await close_redis()


if __name__ == "__main__":
    asyncio.run(main())
