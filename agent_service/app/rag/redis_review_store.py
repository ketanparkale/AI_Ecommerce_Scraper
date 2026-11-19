import asyncio
import json
import logging
import math
import re
import math
import struct

from redis.exceptions import ResponseError

from app.database.redis_client import get_redis
from app.rag.review_models import StoredReview, SimilarReview
from app.rag.review_repository import ReviewRepository

logger = logging.getLogger(__name__)

INDEX_NAME = "idx:reviews"
KEY_PREFIX = "review:"

EMBEDDING_DIM = 384
EMBEDDING_ALGORITHM = "FLAT"
PIPELINE_BATCH_SIZE = 500
REDIS_DATA_TTL = 8 * 60 * 60  # 8 hours

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
    def _extract_similar_documents(
        response
    ) -> list[SimilarReview]:

        similar_reviews = []

        if not isinstance(response, dict):
            raise TypeError(
                f"Unexpected Redis response type: {type(response).__name__}"
            )

        # Redis response uses byte keys.
        results = response.get(b"results", [])

        for item in results:

            attributes = item.get(b"extra_attributes", {})

            # Extract JSON document and similarity score.
            document = attributes.get(b"$")
            score = attributes.get(b"score")

            if document is None or score is None:
                continue

            # Pydantic can validate JSON directly from bytes.
            review = StoredReview.model_validate_json(document)

            # Embeddings are not required after retrieval.
            review = review.model_copy(
                update={"embedding": None}
            )

            similar_reviews.append(
                SimilarReview(
                    review=review,
                    score=float(score)
                )
            )

        return similar_reviews

    
    @staticmethod
    def _extract_documents(response) -> list[StoredReview]:
        """
        Extract StoredReview documents from Redis FT.SEARCH responses.
        """

        reviews = []

        # Redis returns dictionary keys as bytes.
        results = response.get(b"results", [])

        for result in results:

            extra_attributes = result.get(b"extra_attributes", {})

            # Extract the JSON document.
            json_data = extra_attributes.get(b"$")

            if not json_data:
                continue

            # Decode bytes and parse JSON.
            if isinstance(json_data, bytes):
                json_data = json_data.decode("utf-8")

            document = json.loads(json_data)

            # Embeddings are not needed when retrieving reviews.
            document.pop("embedding", None)

            reviews.append(
                StoredReview.model_validate(document)
            )

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

                    pipe.expire(key, REDIS_DATA_TTL)
                    
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
                keyword_expression = "|".join(tokens)

                filters.append(
                    f"@review_text:({keyword_expression})"
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

    async def _count_reviews(
    self,
    product_id: str,
    min_rating: float | None = None,
    max_rating: float | None = None
    ) -> int:

        filters = [
            self._build_product_filter(product_id)
        ]

        if min_rating is not None or max_rating is not None:
            lower = min_rating if min_rating is not None else "-inf"
            upper = max_rating if max_rating is not None else "+inf"

            filters.append(
                f"@rating:[{lower} {upper}]"
            )

        query = " ".join(filters)

        response = await self.client.execute_command(
            "FT.AGGREGATE",
            INDEX_NAME,
            query,
            "GROUPBY", "0",
            "REDUCE", "COUNT", "0", "AS", "total",
            "DIALECT", "2"
        )

        # Redis returns a dictionary, not a list.
        results = response.get(b"results", [])

        if not results:
            return 0

        attributes = results[0].get(b"extra_attributes", {})

        total = attributes.get(b"total", b"0")

        return int(total)



    @staticmethod
    def _extract_projected_documents(response) -> list[SimilarReview]:

        similar_reviews = []

        results = response.get(b"results", [])

        for item in results:
            attributes = item.get(b"extra_attributes", {})

            def get_value(field):
                value = attributes.get(field)

                if value is None:
                    return None

                if isinstance(value, bytes):
                    return value.decode("utf-8")

                return value

            rating = get_value(b"$.rating")
            score = get_value(b"score")

            review = StoredReview(
                review_id=get_value(b"$.review_id"),
                product_id=get_value(b"$.product_id"),
                title=get_value(b"$.title"),
                text=get_value(b"$.text"),
                author=get_value(b"$.author"),
                rating=float(rating) if rating is not None else None,
                review_date=get_value(b"$.review_date"),
                embedding=None
            )

            similar_reviews.append(
                SimilarReview(
                    review=review,
                    score=float(score)
                )
            )

        return similar_reviews

    async def search_similar(
        self,
        product_id: str,
        embedding: list[float],
        limit: int = 5,
        min_rating: float | None = None,
        max_rating: float | None = None,
        max_distance: float | None = None
    ) -> list[SimilarReview]:

        # 1. Validate inputs
        if limit < 1:
            return []

        if len(embedding) != EMBEDDING_DIM:
            raise ValueError(
                f"Expected {EMBEDDING_DIM} dimensions, "
                f"received {len(embedding)}."
            )

        if not all(math.isfinite(value) for value in embedding):
            raise ValueError("Embedding contains invalid values.")

        if max_distance is not None and not 0 <= max_distance <= 2:
            raise ValueError("max_distance must be between 0 and 2.")

        # 2. Count eligible reviews for this product
        candidate_count = await self._count_reviews(
            product_id=product_id,
            min_rating=min_rating,
            max_rating=max_rating
        )

        if candidate_count == 0:
            return []

        # 3. Build product and rating filters
        filters = [
            self._build_product_filter(product_id)
        ]

        if min_rating is not None or max_rating is not None:
            lower = min_rating if min_rating is not None else "-inf"
            upper = max_rating if max_rating is not None else "+inf"

            filters.append(
                f"@rating:[{lower} {upper}]"
            )

        filter_query = " ".join(filters)

        # 4. Build KNN query
        search_query = (
            f"({filter_query})"
            f"=>[KNN {candidate_count} @embedding $vec AS score]"
        )

        # 5. Convert embedding to FLOAT32 bytes
        vector = struct.pack(
            f"<{len(embedding)}f",
            *embedding
        )

        # 6. Execute Redis vector search
        response = await self.client.execute_command(
            "FT.SEARCH",
            INDEX_NAME,
            search_query,
            "PARAMS", "2",
            "vec", vector,
            "RETURN", "8",
            "$.review_id",
            "$.product_id",
            "$.title",
            "$.text",
            "$.author",
            "$.rating",
            "$.review_date",
            "score",
            "SORTBY", "score", "ASC",
            "LIMIT", "0", str(candidate_count),
            "DIALECT", "2"
        )

        similar_reviews = self._extract_projected_documents(response)

        # Apply distance threshold
        if max_distance is not None:
            similar_reviews = [
                item for item in similar_reviews
                if item.score <= max_distance
            ]

        return similar_reviews[:limit]



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



    async def get_all(
    self,
    product_id: str
    ) -> list[StoredReview]:

        query = self._build_product_filter(product_id)

        response = await self.client.execute_command(
            "FT.SEARCH",
            INDEX_NAME,
            query,
            "RETURN", "1", "$",
            "LIMIT", "0", "1000",
            "DIALECT", "2"
        )

        return self._extract_documents(response)