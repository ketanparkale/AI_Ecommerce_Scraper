import json

from langchain_core.tools import StructuredTool

from app.services.review_fetch_service import ReviewFetchService


def create_review_tool(
    review_fetch_service: ReviewFetchService,
) -> StructuredTool:

    async def get_product_reviews(product_url: str) -> str:
        """
        Fetch customer reviews, generate embeddings,
        and store them in Redis.
        """

        result = await review_fetch_service.fetch_and_ingest(
            product_url=product_url
        )

        return json.dumps(result, default=str)

    return StructuredTool.from_function(
        coroutine=get_product_reviews,
        name="get_product_reviews",
        description=(
            "Fetch customer reviews from a Flipkart product URL "
            "and store them in Redis for semantic search."
        ),
    )