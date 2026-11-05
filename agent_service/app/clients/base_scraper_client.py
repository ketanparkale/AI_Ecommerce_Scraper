from typing import Protocol, TypeVar

T = TypeVar("T")

class BaseScraperClient(Protocol[T]):
    
    async def scrape(self, product_url: str) -> T:
        ...