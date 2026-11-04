
from datetime import date
from html import unescape

from pydantic import BaseModel, Field, field_validator


class Brand(BaseModel):
    name: str | None = None


class Author(BaseModel):
    name: str | None = None
    location: str | None = None
    @field_validator("name", mode="before")
    @classmethod
    def collapse_whitespace(cls, value):
        return (
            " ".join(value.split())
            if isinstance(value, str)
            else value
        )


class ReviewRating(BaseModel):
    bestRating: float | None = None
    ratingValue: float | None = None


class Review(BaseModel):
    name: str | None = None
    author: Author | None = None
    reviewBody: str | None = None
    reviewRating: ReviewRating | None = None
    datePublished: date | None = None

    @field_validator("name", "reviewBody", mode="before")
    @classmethod
    def clean_text(cls, value):
        return (
            unescape(value).strip()
            if isinstance(value, str)
            else value
        )


class AggregateRating(BaseModel):
    ratingValue: float | None = None
    ratingCount: int | None = None
    reviewCount: int | None = None


class ParameterRating(BaseModel):
    parameter: str | None = None
    rating: str | None = None


class StarCount(BaseModel):
    ratingValue: int | None = None
    ratingCount: int | None = None


class ProductRating(BaseModel):
    rating: float | None = None
    ratingsCount: int | None = None
    reviewsCount: int | None = None

    parameterRating: list[ParameterRating] = Field(
        default_factory=list
    )

    individualRatingsCount: list[StarCount] = Field(
        default_factory=list
    )


class ZembraUsage(BaseModel):
    cost: float | None = None
    balance: float | None = None


class ReviewResponse(BaseModel):
    title: str | None = None
    description: str | None = None
    brand: Brand | None = None

    review: list[Review] = Field(default_factory=list)
    totalReviewCount: int | None = None
    # Number of review objects actually returned
    returnedReviewCount: int = 0

    aggregateRating: AggregateRating | None = None
    pr: ProductRating | None = None

    usage: ZembraUsage | None = None
