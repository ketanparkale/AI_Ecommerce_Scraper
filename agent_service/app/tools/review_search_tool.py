import json
import logging
from typing import Annotated

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from langchain_core.tools import InjectedToolCallId

from app.services.review_search_service import ReviewSearchService


logger = logging.getLogger(__name__)

MAX_REVIEW_DISTANCE = 0.55
MAX_REVIEW_SEARCH_CALLS = 3


def create_review_search_tool(
    review_search_service: ReviewSearchService,
) -> StructuredTool:

    async def search_product_reviews(
        query: str,
        state: Annotated[dict, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
        limit: int = 5,
        min_rating: float | None = None,
        max_rating: float | None = None,
    ) -> Command:
        def make_result(status: str, data: dict) -> Command:
            
            return Command(
                update={
                    "review_search_status": status,
                    "review_search_results": data.get("reviews", []),
                    "messages": [
                        ToolMessage(
                            content=json.dumps(data, ensure_ascii=False),
                            tool_call_id=tool_call_id,
                        )
                    ],
                }
            )

        product_id = state.get("current_product_id")
        
        if not product_id:
            return make_result(
                "error",
                {
                    "error": (
                        "No active product found. "
                        "Please provide a product URL first."
                    )
                },
            )

        conversation_messages = state.get("messages", [])

        last_user_index = max(
            (
                index
                for index, message in enumerate(conversation_messages)
                if isinstance(message, HumanMessage)
            ),
            default=-1,
        )

        search_call_count = sum(
            1
            for message in conversation_messages[last_user_index + 1:]
            if isinstance(message, AIMessage)
            for tool_call in message.tool_calls
            if tool_call.get("name") == "search_product_reviews"
        )

        if search_call_count >= MAX_REVIEW_SEARCH_CALLS:
            logger.warning("Review search limit reached.")

            return make_result(
                "error",
                {
                    "error": (
                        "Review search limit reached. "
                        "Use the results already retrieved."
                    )
                },
            )
        logger.info(
            "Review search | product_id=%s | query=%r | limit=%s",
            product_id,
            query,
            limit,
        )
        try:
            logger.info("Generating embedding for query: %r", query)
            results = await review_search_service.search_similar_reviews(
                product_id=product_id,
                query=query,
                limit=limit,
                min_rating=min_rating,
                max_rating=max_rating,
                max_distance=MAX_REVIEW_DISTANCE,
            )

            if not results:
                return make_result(
                    "no_matches",
                    {
                        "status": "no_matches",
                        "message": (
                            "No sufficiently relevant reviews were found "
                            "for this query."
                        ),
                        "reviews": [],
                    },
                )

            reviews = [
                {
                    "review": result.review.model_dump(
                        mode="json",
                        exclude={"embedding"},
                        exclude_none=True,
                    ),
                    "distance": result.score,
                    "match_type": result.match_type,
                }
                for result in results
            ]

            return make_result(
                "success",
                {
                    "status": "success",
                    "reviews": reviews,
                },
            )

        except Exception:
            logger.exception("Review search failed")

            return make_result(
                "error",
                {
                    "error": "Unable to search product reviews right now."
                },
            )

    return StructuredTool.from_function(
        coroutine=search_product_reviews,
        name="search_product_reviews",
        description="""
            Search customer reviews stored for the current product.
            The active product is selected automatically. Never pass a product ID.

            Call this tool for every question about a product characteristic or
            customer experience, including:
            - Cushioning, comfort and softness
            - Fit, sizing and usability
            - Durability and material quality
            - Authenticity, fake products and genuine products
            - Defects, complaints and negative experiences
            - Comparisons with other brands or products
            - Any other question that needs customer review evidence

            Rules:
            - Search again for every new question, even a repeated one.
            Do not reuse previous search results as a substitute.
            - query: short topic keywords from the user's latest question,
            not the full sentence. Examples: "cushioning soft sole",
            "fake duplicate genuine", "Puma comparison".
            - limit: use 10 unless the user asks for fewer.
            - min_rating / max_rating: leave empty unless the user asks for a
            rating range. Never filter out low ratings for complaint or
            authenticity questions.

            Searches reviews already stored; it does not fetch new reviews.
            Results include match_type (semantic or keyword). Semantic results have
            a distance where lower means more similar.
            """
    )