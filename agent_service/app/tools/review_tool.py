from typing import Any
from app.tools.base_tool import BaseTool

class ReviewTool(BaseTool):
    
    def __init__(self, scraper_client):
        self._client = scraper_client

    @property
    def name(self) -> str:
        return "get_product_reviews"

    @property
    def definition(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": (
                    "Retrieve product reviews from a Flipkart product URL, "
                    "including the reviewer's name, rating, review text,date and usage."
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
        reviews = await self._client.execute(product_url)
        return reviews.model_dump_json(exclude_none=True)