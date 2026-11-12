from app.services.embedding_service import EmbeddingService
from app.rag.review_models import StoredReview
from app.rag.review_repository import ReviewRepository


class ReviewIngestionService:

    def __init__(
        self,
        embedding_service: EmbeddingService,
        review_repository: ReviewRepository
    ):
        self.embedding_service = embedding_service
        self.review_repository = review_repository

    async def ingest(
        self,
        reviews: list[StoredReview]
    ) -> int:

        if not reviews:
            return 0

        # Extract review text
        texts = [
            review.text
            for review in reviews
            if review.text and review.text.strip()
        ]

        if not texts:
            return 0

        # Generate embeddings in a batch
        embeddings = await self.embedding_service.embed_texts(texts)

        # Attach embeddings to their corresponding reviews
        embedding_index = 0

        for review in reviews:
            if review.text and review.text.strip():
                review.embedding = embeddings[embedding_index]
                review.embedding_model = (
                    self.embedding_service.MODEL_NAME
                )
                embedding_index += 1

        
        await self.review_repository.save_many(reviews)

        return len(reviews)