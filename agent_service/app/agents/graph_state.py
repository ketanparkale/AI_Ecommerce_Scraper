from typing import TypedDict
from langgraph.graph import MessagesState

from app.models.agent_response import ReviewSummary
from app.rag.review_models import SimilarReview


class ProductContext(TypedDict):
    product_id: str
    title: str | None
    url: str


class AgentState(MessagesState):
    products: dict[str, ProductContext]

    current_product_id: str | None
    current_product_title: str | None
    current_product_url: str | None

    review_search_status: str | None
    review_search_results: list[dict]

    answer: ReviewSummary | None