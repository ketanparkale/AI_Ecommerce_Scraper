import asyncio
from urllib.parse import urlparse, parse_qs, urlencode

from fastapi import HTTPException
from app.scraper.brightdata_browser import BrightDataBrowser
from app.scraper.flipkart_scraper import FlipkartScraper
from app.models.product_response import (
    ProductResponse, ColorVariant, SizeVariant
)

RETRYABLE = ("no_peers", "Timeout", "ERR_", "Target closed")


def clean_flipkart_url(url: str) -> str:
    u = urlparse(url)
    q = parse_qs(u.query)
    keep = {k: q[k][0] for k in ("pid", "marketplace") if k in q}
    return f"{u.scheme}://{u.netloc}{u.path}?{urlencode(keep)}"


class ScraperService:
    def __init__(self, bright_data_browser: BrightDataBrowser):
        self.bright_data_browser = bright_data_browser

    async def _scrape_once(self, url: str) -> dict:
        await self.bright_data_browser.connect()
        try:
            return await FlipkartScraper(
                self.bright_data_browser
            ).scrape_product(url)
        finally:
            await self.bright_data_browser.close()

    async def scrape(self, product_url: str, attempts: int = 3) -> ProductResponse:
        url = clean_flipkart_url(product_url)
        raw, last_err = None, None

        for i in range(attempts):
            print("attempt", i + 1, url)
            try:
                raw = await self._scrape_once(url)
                break
            except Exception as e:
                last_err = e
                if not any(k in str(e) for k in RETRYABLE):
                    break
                await asyncio.sleep(2 * (i + 1))

        if raw is None:
            raise HTTPException(
                status_code=502,
                detail=f"Scrape failed after retries: {last_err}",
            )

        sizes = [
            SizeVariant(
                size=s["size"],
                pid=s["pid"],
                available=s["available"],
                price=s["price"],
            )
            for s in raw["sizes"]
            if s["size"] and s["pid"]
        ]

        return ProductResponse(
            title=raw["title"],
            brand=None,
            colors=[
                ColorVariant(
                    color="default",
                    pid=sizes[0].pid if sizes else "",
                    sizes=sizes,
                )
            ],
        )