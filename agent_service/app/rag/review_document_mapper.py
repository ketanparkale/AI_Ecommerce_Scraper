import hashlib

from app.models.review_response import ReviewResponse
from app.rag.review_models import StoredReview


class ReviewDocumentMapper:

    @staticmethod
    def map_reviews(
        response: ReviewResponse,
        product_id: str
    ) -> list[StoredReview]:

        documents = []

        for review in response.reviews:

            # Skip reviews without useful text.
            if not review.text or not review.text.strip():
                continue

            review_id = ReviewDocumentMapper._generate_review_id(
                product_id=product_id,
                author=review.author,
                review_date=review.date,
                title=review.title,
                text=review.text,
            )

            documents.append(
                StoredReview(
                    review_id=review_id,
                    product_id=product_id,
                    product_title=response.product_title,
                    title=review.title,
                    text=review.text,
                    author=review.author,
                    rating=review.rating,
                    review_date=review.date,
                )
            )

        return documents

    @staticmethod
    def _generate_review_id(
        product_id: str,
        author: str | None,
        review_date,
        title: str | None,
        text: str,
    ) -> str:

        unique_value = "|".join([
            product_id,
            author or "",
            str(review_date or ""),
            title or "",
            text.strip(),
        ])

        return hashlib.sha256(
            unique_value.encode("utf-8")
        ).hexdigest()