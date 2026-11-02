import httpx
from app.config.settings import settings
from app.models.scraper_models import ProductResponse

class ScraperClient:
    async def scrape_product(self,product_url:str) -> ProductResponse:

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