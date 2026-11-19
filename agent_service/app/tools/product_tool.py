
from langchain_core.tools import StructuredTool

from app.clients.base_scraper_client import BaseScraperClient
from app.models.product_models import ProductResponse


def create_product_tool(
    scraper_client: BaseScraperClient[ProductResponse],
) -> StructuredTool:

    async def get_product_details(product_url: str) -> str:
        """
        Retrieve product details from a Flipkart product URL,
        including title, brand, colors, sizes, prices and availability.
        """
        product = await scraper_client.scrape(product_url)
        return product.model_dump_json(exclude_none=True)

    return StructuredTool.from_function(
        coroutine=get_product_details,
        name="get_product_details",
        description=(
            "Retrieve product details from a Flipkart product URL, "
            "including product title, brand, colors, sizes, "
            "prices and availability."
        ),
    )
