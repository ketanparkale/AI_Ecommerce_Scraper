
import json
import logging
from typing import Annotated

from langchain_core.tools import StructuredTool, InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from app.services.review_fetch_service import ReviewFetchService


logger = logging.getLogger(__name__)


def create_review_tool(
    review_fetch_service: ReviewFetchService,
) -> StructuredTool:

    async def get_product_reviews(
        product_url: str,
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> Command:
        """
        Fetch customer reviews, generate embeddings,
        store them in Redis, and update active product context.
        """
        result = await review_fetch_service.fetch_and_ingest(
            product_url=product_url
        )

        # Convert the result into a dictionary.
        if hasattr(result, "model_dump"):
            result = result.model_dump(mode="json")

        if not isinstance(result, dict):
            raise TypeError("Review fetch service must return a dictionary.")

        product_id = result.get("product_id")
        product_title = result.get("product_title")

        if not product_id:
            raise ValueError(
                "Review ingestion succeeded without returning a product ID."
            )

        return Command(
            update={
                "current_product_id": product_id,
                "current_product_title": product_title,
                "messages": [
                    ToolMessage(
                        content=json.dumps(result, default=str),
                        tool_call_id=tool_call_id,
                    )
                ],
            }
        )

    return StructuredTool.from_function(
        coroutine=get_product_reviews,
        name="get_product_reviews",
        description=(
            "Fetch customer reviews from a Flipkart product URL, "
            "generate embeddings, and store them in Redis. "
            "Use when the user provides a product URL and requests "
            "review collection or refresh."
        ),
    )
