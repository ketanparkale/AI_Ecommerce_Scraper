from datetime import date, datetime, timezone
from typing import Literal
from pydantic import BaseModel, Field


class StoredReview(BaseModel):
    review_id: str
    product_id: str

    product_title: str | None = None
    title: str | None = None
    text: str | None = None
    author: str | None = None
    rating: float | None = None
    review_date: date | None = None

    embedding: list[float] | None = None
    embedding_model: str | None = None

    fetched_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class SimilarReview(BaseModel):
    review: StoredReview

    score: float | None = Field(
        default=None,
        description="Cosine distance from semantic search. None for keyword-only matches."
    )

    match_type: Literal["semantic", "keyword"] = Field(
    default="semantic",
    description="Indicates whether the review was found through semantic or keyword search."
    )