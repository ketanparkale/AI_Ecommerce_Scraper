import httpx
from app.config.settings import settings
from agent_service.app.models.product_models import ProductResponse
from app.clients.base_scraper_client import BaseScraperClient

class ProductScraperClient(BaseScraperClient[ProductResponse]):
    async def scrape(self,product_url:str) -> ProductResponse:

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.get(
                f"{settings.scraper_service_url}/scrape",
                params={
                    "product_url" : product_url
                }
            )

            response.raise_for_status()
            
            return ProductResponse.model_validate(
                response.json()
            )