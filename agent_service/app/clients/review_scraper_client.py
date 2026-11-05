from app.clients.base_scraper_client import BaseScraperClient
from app.config.settings import settings
import httpx


class ReviewScraperClient(BaseScraperClient):
    
    async def scrape(self, product_url: str) -> dict:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.get(
                f"{settings.scraper_service_url}/scrape/reviews",
                params={
                    "product_url": product_url
                }
            )

            response.raise_for_status()

            return response.json()