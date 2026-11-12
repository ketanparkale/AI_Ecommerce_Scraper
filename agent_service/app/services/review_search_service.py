
from app.rag.review_repository import ReviewRepository
from app.rag.review_models import StoredReview
from app.services.embedding_service import EmbeddingService


class ReviewSearchService:

    def __init__(
        self,
        embedding_service: EmbeddingService,
        review_repository: ReviewRepository,
    ):
        self.embedding_service = embedding_service
        self.review_repository = review_repository

    async def search_similar_reviews(
        self,
        product_id: str,
        query: str,
        limit: int = 5,
        min_rating: float | None = None,
        max_rating: float | None = None,
    ) -> list[StoredReview]:

        if not product_id or not product_id.strip():
            raise ValueError("Product ID cannot be empty.")

        if not query or not query.strip():
            raise ValueError("Search query cannot be empty.")

        if limit < 1:
            raise ValueError("Limit must be greater than zero.")

        if (
            min_rating is not None
            and max_rating is not None
            and min_rating > max_rating
        ):
            raise ValueError("Minimum rating cannot exceed maximum rating.")

        # Convert the user's question into an embedding.
        query_embedding = await self.embedding_service.embed_text(query)

        # Search Redis using vector similarity.
        reviews = await self.review_repository.search_similar(
            product_id=product_id,
            embedding=query_embedding,
            limit=limit,
            min_rating=min_rating,
            max_rating=max_rating,
        )

        return reviews
