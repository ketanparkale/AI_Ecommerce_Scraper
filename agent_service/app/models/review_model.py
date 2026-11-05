from datetime import date

from pydantic import BaseModel, Field


class Review(BaseModel):
    title: str | None = None
    text: str | None = None
    author: str | None = None
    rating: float | None = None
    date: date | None = None


class ZembraUsage(BaseModel):
    cost: float | None = None
    balance: float | None = None


class ReviewResponse(BaseModel):
    product_title: str | None = None
    description: str | None = None
    brand: str | None = None
    average_rating: float | None = None
    rating_count: int | None = None
    returned_count: int = 0
    reviews: list[Review] = Field(default_factory=list)
    usage: ZembraUsage | None = None
