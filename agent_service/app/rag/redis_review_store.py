import asyncio
import logging
import math
import re
import struct   
import json

from redis.exceptions import ResponseError

from app.database.redis_client import get_redis
from app.rag.review_models import StoredReview
from app.rag.review_repository import ReviewRepository
from app.rag.review_models import StoredReview, SimilarReview


logger = logging.getLogger(__name__)

INDEX_NAME = "idx:reviews"
KEY_PREFIX = "review:"

EMBEDDING_DIM = 384
EMBEDDING_ALGORITHM = "FLAT"
PIPELINE_BATCH_SIZE = 500


def escape_tag(value: str) -> str:
    """Escape special characters in Redis TAG query values."""
    special_chars = r",.<>{}[]\"':;!@#$%^&*()-+=~| "
    return "".join(
        "\\" + char if char in special_chars else char
        for char in value
    )


async def ensure_review_index():
    client = get_redis()

    try:
        await client.execute_command("FT.INFO", INDEX_NAME)
        logger.info("Redis review index already exists.")
        return

    except ResponseError as exc:
        error = str(exc).lower()

        if "unknown index" not in error and "no such index" not in error:
            raise

    logger.info("Creating Redis review index.")

    try:
        await client.execute_command(
            "FT.CREATE",
            INDEX_NAME,
            "ON", "JSON",
            "PREFIX", "1", KEY_PREFIX,
            "SCHEMA",

            "$.product_id",
            "AS", "product_id",
            "TAG",

            "$.rating",
            "AS", "rating",
            "NUMERIC", "SORTABLE",

            "$.fetched_at",
            "AS", "fetched_at",
            "TEXT", "SORTABLE",

            "$.text",
            "AS", "review_text",
            "TEXT",

            "$.title",
            "AS", "review_title",
            "TEXT",

            "$.embedding",
            "AS", "embedding",
            "VECTOR", EMBEDDING_ALGORITHM, "6",
            "TYPE", "FLOAT32",
            "DIM", str(EMBEDDING_DIM),
            "DISTANCE_METRIC", "COSINE"
        )

        logger.info("Redis review index created.")

    except ResponseError as exc:
        # Another application instance may have created it
        # between FT.INFO and FT.CREATE.
        if "already exists" not in str(exc).lower():
            raise

        logger.info("Redis review index was created by another instance.")


class RedisReviewStore(ReviewRepository):

    def __init__(self):
        self.client = get_redis()

    @staticmethod
    def _get_key(review: StoredReview) -> str:
        return (
            f"{KEY_PREFIX}"
            f"{review.product_id}:"
            f"{review.review_id}"
        )

    @staticmethod
    def _build_product_filter(product_id: str) -> str:
        return f"@product_id:{{{escape_tag(product_id)}}}"

    @staticmethod
    def _row_to_dict(row) -> dict:
        result = {}

        for i in range(0, len(row), 2):
            key, value = row[i], row[i + 1]

            if isinstance(key, bytes):
                key = key.decode("utf-8")

            if isinstance(value, bytes):
                value = value.decode("utf-8")

            result[key] = value

        return result

    @staticmethod
    def _extract_similar_documents(response) -> list[SimilarReview]:

        results = []

        if not isinstance(response, dict):
            raise TypeError(
                f"Unexpected Redis response type: {type(response).__name__}"
            )

        for item in response.get("results", []):

            attributes = item.get("extra_attributes", {})

            document = attributes.get("$")
            score = attributes.get("score")

            if document is None or score is None:
                continue

            if isinstance(document, str):
                document = json.loads(document)

            review = StoredReview.model_validate(document)

            review = review.model_copy(
                update={"embedding": None}
            )

            results.append(
                SimilarReview(
                    review=review,
                    score=float(score),
                )
            )

        return results

    @staticmethod
    def _extract_documents(response) -> list[StoredReview]:
        reviews = []

        # Handle the dictionary response format.
        if isinstance(response, dict):
            results = response.get("results", [])

            for result in results:
                extra_attributes = result.get("extra_attributes", {})

                # We requested RETURN $ in our FT.SEARCH query.
                document = extra_attributes.get("$")

                if document is None:
                    continue

                # Redis may return the JSON document as a string.
                if isinstance(document, str):
                    document = json.loads(document)

                review = StoredReview.model_validate(document)

                # Don't expose embeddings in search results.
                review = review.model_copy(
                    update={"embedding": None}
                )

                reviews.append(review)

            return reviews



    async def save_many(
        self,
        reviews: list[StoredReview]
    ) -> None:

        if not reviews:
            return

        # Validate before writing anything.
        for review in reviews:

        # Reviews without text may not have embeddings.
            if review.embedding is None:
                continue

            if len(review.embedding) != EMBEDDING_DIM:
                raise ValueError(
                    f"Expected {EMBEDDING_DIM} embedding dimensions, "
                    f"received {len(review.embedding)}."
                )

            if not all(math.isfinite(value) for value in review.embedding):
                raise ValueError(
                    f"Review {review.review_id} has an invalid embedding."
                )

        # Write in batches to avoid building an excessively large pipeline.
        for start in range(0, len(reviews), PIPELINE_BATCH_SIZE):
            batch = reviews[start:start + PIPELINE_BATCH_SIZE]

            async with self.client.pipeline(
                transaction=False
            ) as pipe:

                for review in batch:
                    key = self._get_key(review)

                    pipe.execute_command(
                        "JSON.SET",
                        key,
                        "$",
                        review.model_dump_json()
                    )

                await pipe.execute()

        logger.info("Saved %d reviews to Redis.", len(reviews))

    async def search(
        self,
        product_id: str,
        query: str | None = None,
        min_rating: float | None = None,
        max_rating: float | None = None,
        limit: int = 10
    ) -> list[StoredReview]:

        if limit < 1:
            return []

        if (
            min_rating is not None
            and max_rating is not None
            and min_rating > max_rating
        ):
            raise ValueError("min_rating cannot exceed max_rating.")

        filters = [
            self._build_product_filter(product_id)
        ]

        if min_rating is not None or max_rating is not None:
            lower = min_rating if min_rating is not None else "-inf"
            upper = max_rating if max_rating is not None else "+inf"

            filters.append(f"@rating:[{lower} {upper}]")

        if query:
            tokens = re.findall(r"\w+", query)

            if tokens:
                filters.append(
                    f"@review_text:({' '.join(tokens)})"
                )

        search_query = " ".join(filters)

        response = await self.client.execute_command(
            "FT.SEARCH",
            INDEX_NAME,
            search_query,
            "RETURN", "1", "$",
            "SORTBY", "fetched_at", "DESC",
            "LIMIT", "0", str(limit),
            "DIALECT", "2"
        )

        return self._extract_documents(response)


    async def search_similar(
        self,
        product_id: str,
        embedding: list[float],
        limit: int = 5,
        min_rating: float | None = None,
        max_rating: float | None = None
    ) -> list[StoredReview]:

        if limit < 1:
            return []

        if len(embedding) != EMBEDDING_DIM:
            raise ValueError(
                f"Expected {EMBEDDING_DIM} embedding dimensions, "
                f"received {len(embedding)}."
            )

        if not all(math.isfinite(value) for value in embedding):
            raise ValueError("Embedding contains invalid numeric values.")

        if (
            min_rating is not None
            and max_rating is not None
            and min_rating > max_rating
        ):
            raise ValueError("min_rating cannot exceed max_rating.")

        filters = [
            self._build_product_filter(product_id)
        ]

        if min_rating is not None or max_rating is not None:
            lower = min_rating if min_rating is not None else "-inf"
            upper = max_rating if max_rating is not None else "+inf"

            filters.append(f"@rating:[{lower} {upper}]")

        filter_query = " ".join(filters)

        search_query = (
            f"({filter_query})"
            f"=>[KNN {limit} @embedding $vec AS score]"
        )

        vector = struct.pack(f"<{len(embedding)}f", *embedding)

        response = await self.client.execute_command(
            "FT.SEARCH",
            INDEX_NAME,
            search_query,
            "PARAMS", "2",
            "vec", vector,
            "RETURN", "2",
            "$", "score",
            "SORTBY", "score", "ASC",
            "LIMIT", "0", str(limit),
            "DIALECT", "2"
        )

        return self._extract_similar_documents(response)


    async def stats(
        self,
        product_id: str
    ) -> dict:

        product_filter = self._build_product_filter(product_id)

        # Run both independent aggregations concurrently.
        overall_query = self.client.execute_command(
            "FT.AGGREGATE",
            INDEX_NAME,
            product_filter,
            "GROUPBY", "0",
            "REDUCE", "COUNT", "0", "AS", "total",
            "REDUCE", "AVG", "1", "@rating",
            "AS", "average_rating",
            "DIALECT", "2"
        )

        five_star_query = self.client.execute_command(
            "FT.AGGREGATE",
            INDEX_NAME,
            f"{product_filter} @rating:[5 5]",
            "GROUPBY", "0",
            "REDUCE", "COUNT", "0", "AS", "total",
            "DIALECT", "2"
        )

        overall_response, five_star_response = await asyncio.gather(
            overall_query,
            five_star_query
        )

        total = 0
        average_rating = None
        five_star_count = 0

        if len(overall_response) > 1 and overall_response[1]:
            result = self._row_to_dict(overall_response[1])

            total = int(result.get("total", 0))

            average = result.get("average_rating")

            if total > 0 and average not in (None, "nan", "NaN"):
                average_rating = float(average)

        if len(five_star_response) > 1 and five_star_response[1]:
            result = self._row_to_dict(five_star_response[1])
            five_star_count = int(result.get("total", 0))

        return {
            "product_id": product_id,
            "total_reviews": total,
            "average_rating": average_rating,
            "five_star_reviews": five_star_count
        }