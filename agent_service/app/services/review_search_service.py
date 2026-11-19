
import asyncio
import re
import hashlib

import numpy as np
import logging

logger = logging.getLogger(__name__)

from app.rag.review_repository import ReviewRepository
from app.rag.review_models import SimilarReview
from app.services.embedding_service import EmbeddingService


class ReviewSearchService:

    # Common words that don't help identify a review topic.
    STOP_WORDS = {
        "a", "an", "the", "is", "are", "was", "were",
        "has", "have", "had", "do", "does", "did",
        "anyone", "someone", "any", "about", "for",
        "of", "in", "on", "at", "to", "from",
        "this", "that", "these", "those",
        "me", "my", "it", "its", "they", "them",
        "and", "or", "but", "with",
        "mentioned", "mention", "say", "said",
        "review", "reviews", "customer", "customers",
        "product", "negative", "positive",
        "good", "bad",
    }

    def __init__(
        self,
        embedding_service: EmbeddingService,
        review_repository: ReviewRepository,
    ):
        self.embedding_service = embedding_service
        self.review_repository = review_repository

    @classmethod
    def _extract_keyword_query(cls, query: str) -> str | None:
        """
        Extract useful search terms from the user's natural-language query.

        Example:
            "Has anyone mentioned negative about the sole?"
            -> "sole"
        """

        tokens = re.findall(r"[a-zA-Z0-9]+", query.lower())

        keywords = [
            token
            for token in tokens
            if token not in cls.STOP_WORDS
        ]

        if not keywords:
            return None

        # Redis RediSearch supports | for OR between terms.
        return "|".join(keywords)

    async def search_similar_reviews(
        self,
        product_id: str,
        query: str,
        limit: int = 5,
        min_rating: float | None = None,
        max_rating: float | None = None,
        max_distance: float | None = None,
    ) -> list[SimilarReview]:

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

        # Extract useful keywords from the natural-language question.
        keyword_query = self._extract_keyword_query(query)

        # Run semantic and keyword retrieval concurrently.
        query_embedding = await self.embedding_service.embed_text(query)
        query_vector = np.asarray(query_embedding, dtype=np.float32)

        logger.info("Search query: %r", query)
        logger.info("Embedding dimensions: %d", len(query_vector))
        logger.info("Embedding first 5 values: %s", query_vector[:5])
        logger.info("Embedding norm: %f", np.linalg.norm(query_vector))
        semantic_task = self.review_repository.search_similar(
            product_id=product_id,
            embedding=query_embedding,
            limit=limit,
            min_rating=min_rating,
            max_rating=max_rating,
            max_distance=max_distance,
        )

        if keyword_query:
            keyword_task = self.review_repository.search(
                product_id=product_id,
                query=keyword_query,
                min_rating=min_rating,
                max_rating=max_rating,
                limit=limit,
            )

            semantic_results, keyword_results = await asyncio.gather(
                semantic_task,
                keyword_task,
            )
        else:
            semantic_results = await semantic_task
            keyword_results = []

        # Merge results and remove duplicates.
        merged: dict[str, SimilarReview] = {}
        logger.info(
            "Semantic results: %s",
            [
                (r.review.review_id, r.score)
                for r in semantic_results
            ],
        )

        logger.info(
            "Keyword results: %s",
            [
                r.review_id
                for r in keyword_results
            ],
        )
       

        # Add semantic results.
        for result in semantic_results:

            review_id = result.review.review_id

            merged[review_id] = SimilarReview(
                review=result.review,
                score=result.score,
                match_type="semantic",
            )

        # Add keyword results.
        for review in keyword_results:

            review_id = review.review_id

            if review_id in merged:

                # This review matched both retrieval strategies.
                # Preserve its semantic score but mark it as hybrid.
                existing = merged[review_id]

                merged[review_id] = existing.model_copy(
                    update={"match_type": "hybrid"}
                )

            else:

                merged[review_id] = SimilarReview(
                    review=review,
                    score=None,
                    match_type="keyword",
                )

        # Keep semantic and hybrid matches ahead of keyword-only matches.
        final_results = sorted(
            merged.values(),
            key=lambda item: (
                item.match_type == "keyword",
                item.score if item.score is not None else float("inf"),
            ),
        )
        logger.info(
            "Hybrid retrieval completed | semantic=%d | keyword=%d",
            len(semantic_results),
            len(keyword_results),
        )

        logger.info(
            "Final merged results | total=%d | semantic=%d | keyword=%d | hybrid=%d",
            len(final_results),
            sum(r.match_type == "semantic" for r in final_results),
            sum(r.match_type == "keyword" for r in final_results),
            sum(r.match_type == "hybrid" for r in final_results),
        )

        return final_results[:limit]
