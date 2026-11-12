from langchain_core.tools import StructuredTool

from app.services.review_search_service import ReviewSearchService


def create_review_search_tool(
    review_search_service: ReviewSearchService,
) -> StructuredTool:

    async def search_product_reviews(
        product_id: str,
        query: str,
        limit: int = 5,
        min_rating: float | None = None,
        max_rating: float | None = None,
    ) -> list[dict]:

        results = await review_search_service.search_similar_reviews(
            product_id=product_id,
            query=query,
            limit=limit,
            min_rating=min_rating,
            max_rating=max_rating,
        )

        return [
            {
                "review": result.review.model_dump(
                    mode="json",
                    exclude={"embedding"},
                    exclude_none=True,
                ),
                "similarity_score": result.score,
            }
            for result in results
        ]

    return StructuredTool.from_function(
        coroutine=search_product_reviews,
        name="search_product_reviews",
        description=(
            "Search previously collected customer reviews using semantic "
            "similarity. Returns review details and a cosine-distance "
            "similarity score. Lower scores indicate closer matches. "
            "Use this to find customer complaints, positive feedback, "
            "product quality, durability, performance, and customer "
            "experiences. This searches reviews already stored in Redis; "
            "it does not scrape new reviews."
        ),
    )