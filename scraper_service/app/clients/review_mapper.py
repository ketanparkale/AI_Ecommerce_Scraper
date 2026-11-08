import html
import re
from datetime import date, datetime
from typing import Any

from app.models.review_response import Review, ReviewResponse, ZembraUsage


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def extract_product_id(url: str) -> str:
    """Flipkart product id from the URL path, e.g. 'itm1ff0105e41af8'."""
    match = re.search(r"/p/(itm[a-z0-9]+)", url, re.I)
    if not match:
        raise ValueError("Could not find Flipkart product id in URL")
    return match.group(1).lower()


def clean_text(value: Any) -> str | None:
    """Decode HTML entities and strip outer whitespace."""
    if not isinstance(value, str):
        return None
    return html.unescape(value).strip() or None


def clean_name(value: Any) -> str | None:
    """Like clean_text, but also collapses repeated inner whitespace."""
    text = clean_text(value)
    return " ".join(text.split()) if text else None


def split_title_body(text: Any) -> tuple[str | None, str | None]:
    """Zembra sends reviews as 'Title\\nBody' in a single `text` field."""
    text = clean_text(text)
    if not text:
        return None, None

    title, sep, body = text.partition("\n")
    if not sep:
        return None, title

    return title.strip() or None, body.strip() or None


def parse_date(value: Any) -> date | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value).date()   # "2026-10-20 00:00:00"
    except ValueError:
        return None


# --------------------------------------------------
# Review mapping
# --------------------------------------------------

def map_review(item: dict) -> Review:
    title, body = split_title_body(item.get("text"))
    author = item.get("author") or {}

    return Review(
        review_id=item["id"],                      # retrieved from Zembra's response
        title=title,
        text=body,
        author=clean_name(author.get("name")),
        rating=item.get("rating"),
        review_date=parse_date(item.get("timestamp")),
    )


# --------------------------------------------------
# Main mapper
# --------------------------------------------------

def map_review_response(raw: dict, product_id: str) -> ReviewResponse:
    if raw.get("status") != "SUCCESS":
        raise ValueError(raw.get("message", "Zembra request failed"))

    data = raw.get("data") or {}
    target = data.get("target") or {}
    raw_data = target.get("rawData") or {}
    aggregate = raw_data.get("aggregateRating") or {}

    # Fragile provider path: always use .get()
    pr = (
        ((raw_data.get("fdpEventTracking") or {}).get("events") or {})
        .get("psi") or {}
    ).get("pr") or {}

    reviews: list[Review] = []
    seen: set[str] = set()

    for item in data.get("reviews") or []:
        if not isinstance(item, dict) or not item.get("id"):
            continue                                # no Zembra id -> skip
        if item.get("isDeleted") or item.get("isHidden"):
            continue

        review = map_review(item)

        if not (review.title or review.text):
            continue
        if review.review_id in seen:
            continue

        seen.add(review.review_id)
        reviews.append(review)

    return ReviewResponse(
        product_id=product_id,
        product_title=clean_text(target.get("name")),
        brand=(raw_data.get("brand") or {}).get("name"),
        average_rating=target.get("globalRating") or pr.get("rating"),
        rating_count=aggregate.get("ratingCount") or pr.get("ratingsCount"),
        returned_count=len(reviews),
        rating_distribution={
            s["ratingValue"]: s["ratingCount"]
            for s in pr.get("individualRatingsCount") or []
            if s.get("ratingValue") is not None and s.get("ratingCount") is not None
        },
        parameter_ratings={
            p["parameter"]: p["rating"]
            for p in pr.get("parameterRating") or []
            if p.get("parameter") and p.get("rating")
        },
        reviews=reviews,
        usage=ZembraUsage(
            cost=(data.get("job") or {}).get("cost"),
            balance=raw.get("balance"),
        ),
    )