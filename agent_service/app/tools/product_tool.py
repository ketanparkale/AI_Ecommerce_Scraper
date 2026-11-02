from langchain_protocol import Any

from app.clients.scraper_client import ScraperClient
from app.models.scraper_models import ProductResponse

class ProductTool:

    def __init__(self,scraper_client:ScraperClient):
        self.scraper_client = scraper_client

    @property
    def definition(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_product_details",
                "description": (
                    "Retrieve product details from a Flipkart product URL, "
                    "including the product title, brand, colors, sizes, "
                    "prices, and availability."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_url": {
                            "type": "string",
                            "description": "The Flipkart product URL."
                        }
                    },
                    "required": ["product_url"],
                    "additionalProperties": False
                },
                "strict": True
            }
        }

    async def execute(self, product_url: str) -> ProductResponse:
        return await self.scraper_client.scrape_product(product_url)
