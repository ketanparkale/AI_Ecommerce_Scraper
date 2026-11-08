from datetime import date, datetime, timezone

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