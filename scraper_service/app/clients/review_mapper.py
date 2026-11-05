import html
from datetime import date, datetime
from typing import Any

from app.models.review_response import (
    ReviewResponse,
    Brand,
    Author,
    Review,
    ReviewRating,
    AggregateRating,
    ParameterRating,
    StarCount,
    ProductRating,
    ZembraUsage,
)


class ReviewsNotReady(ValueError):
    """Raised while the Zembra job is still collecting reviews.

    The client can catch this and keep polling.
    """

# Text / date helpers

def clean_text(value: Any) -> str | None:
    """Decode HTML entities (&quot;, &hellip;) and strip outer whitespace."""
    if not isinstance(value, str):
        return None
    return html.unescape(value).strip() or None


def clean_name(value: Any) -> str | None:
    """Like clean_text, but also collapses repeated inner whitespace."""
    text = clean_text(value)
    return " ".join(text.split()) if text else None


def split_title_body(text: Any) -> tuple[str | None, str | None]:
    """Zembra GET reviews use 'Title\\nBody' in a single `text` field."""
    text = clean_text(text)
    if not text:
        return None, None

    title, sep, body = text.partition("\n")
    if not sep:
        return None, title

    return (title.strip() or None), (body.strip() or None)


def parse_date(value: Any) -> date | None:
    if not value:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if not isinstance(value, str):
        return None

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None



# Review extraction


def extract_reviews(raw: dict) -> list[dict]:
    data = raw.get("data") or {}

    # GET response: full review list
    reviews = data.get("reviews")
    if isinstance(reviews, list):
        return reviews

    # Fallback: sample reviews embedded in the product page markup
    target = data.get("target") or {}
    raw_data = target.get("rawData") or {}
    reviews = raw_data.get("review")

    return reviews if isinstance(reviews, list) else []


def map_review(item: dict) -> Review:
    author_data = item.get("author") or {}

    if isinstance(author_data, str):
        author_data = {"name": author_data}
    if not isinstance(author_data, dict):
        author_data = {}

    author = Author(
        name=clean_name(author_data.get("name") or item.get("authorName")),
        location=clean_name(author_data.get("location") or item.get("location")),
    )

    # Rating: page markup uses reviewRating{}, GET uses a plain `rating`
    rating_data = item.get("reviewRating")
    if not isinstance(rating_data, dict):
        rating_value = item.get("rating")
        rating_data = (
            {"ratingValue": rating_value} if rating_value is not None else None
        )

    review_rating = (
        ReviewRating.model_validate(rating_data) if rating_data else None
    )

    # Text: explicit fields first, otherwise split "Title\nBody"
    title = clean_text(item.get("name") or item.get("title"))
    body = clean_text(item.get("reviewBody") or item.get("content"))

    if not body:
        split_title, split_body = split_title_body(item.get("text"))
        title = title or split_title
        body = split_body

    return Review(
        name=title,
        author=author,
        reviewBody=body,
        reviewRating=review_rating,
        datePublished=(
            parse_date(item.get("datePublished"))
            or parse_date(item.get("timestamp"))
            or parse_date(item.get("date"))
        ),
    )



# Rating helpers

def map_product_rating(pr_data: Any) -> ProductRating | None:
    if not isinstance(pr_data, dict) or not pr_data:
        return None

    return ProductRating(
        rating=pr_data.get("rating"),
        ratingsCount=pr_data.get("ratingsCount"),
        reviewsCount=pr_data.get("reviewsCount"),
        parameterRating=[
            ParameterRating.model_validate(p)
            for p in (pr_data.get("parameterRating") or [])
            if isinstance(p, dict)
        ],
        individualRatingsCount=[
            StarCount.model_validate(s)
            for s in (pr_data.get("individualRatingsCount") or [])
            if isinstance(s, dict)
        ],
    )



# Main mapper

def map_review_response(raw: dict) -> ReviewResponse:
    if raw.get("status") != "SUCCESS":
        raise ValueError(raw.get("message", "Zembra request failed"))

    data = raw.get("data") or {}
    target = data.get("target") or {}
    raw_data = target.get("rawData") or {}

    if not raw_data and not data.get("reviews"):
        raise ReviewsNotReady(
            "Review data is not available yet. "
            "The Zembra job may still be processing."
        )

    # Brand
    brand_data = raw_data.get("brand")
    brand = (
        Brand.model_validate(brand_data) if isinstance(brand_data, dict) else None
    )

    # Aggregate rating
    aggregate_data = raw_data.get("aggregateRating")
    aggregate = (
        AggregateRating.model_validate(aggregate_data)
        if isinstance(aggregate_data, dict)
        else None
    )

    # Product rating breakdown
    psi = (
        ((raw_data.get("fdpEventTracking") or {}).get("events") or {}).get("psi")
        or {}
    )
    product_rating = map_product_rating(psi.get("pr"))

    # Reviews (skip deleted / hidden)
    reviews = [
        map_review(item)
        for item in extract_reviews(raw)
        if isinstance(item, dict)
        and not item.get("isDeleted")
        and not item.get("isHidden")
    ]

    # Total review count
    total_review_count = (
        ((target.get("reviewCount") or {}).get("native") or {}).get("total")
        or (aggregate.reviewCount if aggregate else None)
    )

    # Still collecting? Let the caller retry instead of returning a partial list.
    if total_review_count and len(reviews) < total_review_count:
        raise ReviewsNotReady(
            f"Reviews still loading: {len(reviews)}/{total_review_count}"
        )

    usage_data = data.get("usage") or {}
    return ReviewResponse(
        title=clean_text(raw_data.get("name")) or clean_text(target.get("name")),
        description=clean_text(raw_data.get("description")),
        brand=brand,
        review=reviews,
        totalReviewCount=total_review_count,
        returnedReviewCount=len(reviews),
        aggregateRating=aggregate,
        pr=product_rating,
        usage=ZembraUsage(
            cost=usage_data.get("cost"),
            balance=usage_data.get("balance"),
        )
    )