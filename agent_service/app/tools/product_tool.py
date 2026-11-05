from typing import Any
from agent_service.app.clients.base_scraper_client import BaseScraperClient
from agent_service.app.models.product_models import ProductResponse
from app.tools.base_tool import BaseTool

class ProductTool(BaseTool):

    def __init__(self,scraper_client:BaseScraperClient[ProductResponse]):
        self._client = scraper_client

    @property
    def name(self) -> str:
        return "get_product_details"

    @property
    def definition(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
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

    async def _run(self, product_url: str) -> str:
        product = await self._client.execute(product_url)
        return product.model_dump_json(exclude_none=True)
