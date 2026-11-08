
import pytest

from app.database.redis_client import connect_redis, close_redis
from app.rag.redis_review_store import (
    RedisReviewStore,
    ensure_review_index,
)
from app.rag.review_models import StoredReview
from app.services.embedding_service import EmbeddingService
from app.services.review_ingestion_service import ReviewIngestionService


@pytest.mark.asyncio
async def test_review_ingestion():

    await connect_redis()

    try:
        # Ensure the Redis search index exists.
        await ensure_review_index()

        # Initialize dependencies.
        embedding_service = EmbeddingService()
        review_store = RedisReviewStore()

        ingestion_service = ReviewIngestionService(
            embedding_service=embedding_service,
            review_repository=review_store,
        )

        # Prepare sample reviews.
        reviews = [
            StoredReview(
                review_id="test_review_001",
                product_id="test_product_001",
                product_title="ASICS GEL-PULSE 16",
                rating=5,
                text="Very comfortable shoes. Excellent cushioning for daily running.",
                author="Test User 1",
            ),
            StoredReview(
                review_id="test_review_002",
                product_id="test_product_001",
                product_title="ASICS GEL-PULSE 16",
                rating=2,
                text="The grip is poor on muddy surfaces. Not suitable for wet roads.",
                author="Test User 2",
            ),
            StoredReview(
                review_id="test_review_003",
                product_id="test_product_001",
                product_title="ASICS GEL-PULSE 16",
                rating=4,
                text=None,
                author="Test User 3",
            ),
        ]

        # Ingest reviews.
        saved_count = await ingestion_service.ingest(reviews)

        assert saved_count == 3

        # Verify embeddings.
        assert reviews[0].embedding is not None
        assert len(reviews[0].embedding) == 384

        assert reviews[1].embedding is not None
        assert len(reviews[1].embedding) == 384

        assert reviews[2].embedding is None

        # Verify reviews were saved.
        saved_reviews = await review_store.search(
            product_id="test_product_001",
            limit=10,
        )

        assert len(saved_reviews) == 3

        # Verify vector search.
        query_embedding = await embedding_service.embed_text(
            "Are these shoes comfortable for running?"
        )

        similar_reviews = await review_store.search_similar(
            product_id="test_product_001",
            embedding=query_embedding,
            limit=2,
        )

        assert len(similar_reviews) > 0

        print("\nIngestion test passed!")
        print(f"Saved reviews: {saved_count}")
        print(f"Vector search results: {len(similar_reviews)}")

        for review in similar_reviews:
            print(f"Rating: {review.rating}")
            print(f"Review: {review.text}")

    finally:
        await close_redis()
