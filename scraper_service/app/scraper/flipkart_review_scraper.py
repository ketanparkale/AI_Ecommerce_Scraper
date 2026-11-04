
from app.scraper.base_scraper import BaseScraper
from app.clients import ReviewClient
from app.models.review_response import ReviewResponse
from scraper_service.app.clients.review_mapper import map_review_response


class FlipkartReviewScraper(BaseScraper[ReviewResponse]):

    def __init__(self, client: ReviewClient):
        self.client = client

    async def scrape(self, url: str) -> ReviewResponse:

        raw_response = await self.client.fetch_reviews(
            network="flipkart",
            slug=url,
            monitoring="none"
        )

        return map_review_response(raw_response)