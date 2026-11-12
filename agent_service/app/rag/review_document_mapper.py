from app.models.review_model import ReviewResponse
from app.rag.review_models import StoredReview


class ReviewDocumentMapper:

    @staticmethod
    def map_reviews(
        response: ReviewResponse,
    ) -> list[StoredReview]:

        documents = []

        for review in response.reviews:

            if not review.text or not review.text.strip():
                continue

            documents.append(
                StoredReview(
                    review_id=review.review_id,
                    product_id=response.product_id,
                    product_title=response.product_title,
                    title=review.title,
                    text=review.text,
                    author=review.author,
                    rating=review.rating,
                    review_date=review.review_date,
                )
            )

        return documents