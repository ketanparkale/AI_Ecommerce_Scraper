from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")

class BaseScraper(ABC, Generic[T]):
    @abstractmethod

    async def scrape(self, url:str) -> T:
        pass
