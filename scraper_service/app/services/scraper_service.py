import asyncio

from fastapi import HTTPException
from typing import TypeVar, Generic

from app.scraper.base_scraper import BaseScraper

T = TypeVar("T")

RETRYABLE = ("no_peers", "Timeout", "ERR_", "Target closed")


class ScraperService(Generic[T]):

    def __init__(self, scraper: BaseScraper[T]):
        self.scraper = scraper

    async def scrape(
        self,
        url: str,
        attempts: int = 3
    ) -> T:

        last_err = None

        for i in range(attempts):

            try:
                return await self.scraper.scrape(url)

            except Exception as e:
                last_err = e

                if not any(k in str(e) for k in RETRYABLE):
                    break

                if i < attempts - 1:
                    await asyncio.sleep(2 * (i + 1))

        raise HTTPException(
            status_code=502,
            detail=f"Scrape failed after retries: {last_err}"
        )