from app.scraper.base_scraper import BaseScraper
from app.clients.review_client import ReviewsClient
from app.models.review_response import ReviewResponse
from app.clients.review_mapper import extract_product_id, map_review_response


class FlipkartReviewScraper(BaseScraper[ReviewResponse]):

    def __init__(self, client: ReviewsClient):
        self.client = client

    async def scrape(self, url: str) -> ReviewResponse:
        product_id = extract_product_id(url)

        raw_response = await self.client.fetch_reviews(
            network="flipkart",
            slug=f"x/p/{product_id}",
            monitoring="none",
        )

        return map_review_response(raw_response, product_id)