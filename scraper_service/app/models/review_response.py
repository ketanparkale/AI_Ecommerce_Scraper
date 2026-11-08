from datetime import date

from pydantic import BaseModel, Field


class Review(BaseModel):
    review_id: str
    title: str | None = None
    text: str | None = None
    author: str | None = None
    rating: float | None = None
    review_date: date | None = None


class ZembraUsage(BaseModel):
    cost: float | None = None
    balance: float | None = None


class ReviewResponse(BaseModel):
    product_id: str
    product_title: str | None = None
    brand: str | None = None

    average_rating: float | None = None
    rating_count: int | None = None
    returned_count: int = 0

    rating_distribution: dict[int, int] = Field(default_factory=dict)
    parameter_ratings: dict[str, str] = Field(default_factory=dict)

    reviews: list[Review] = Field(default_factory=list)
    usage: ZembraUsage | None = None