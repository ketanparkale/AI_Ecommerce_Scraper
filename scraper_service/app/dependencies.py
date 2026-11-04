
from app.services.scraper_service import ScraperService

from app.browser.brightdata_browser import BrightDataBrowser
from app.config.settings import settings

from app.clients.zembra_client import ZembraClient

from app.scraper.flipkart_product_scraper import FlipkartProductScraper
from app.scraper.flipkart_review_scraper import FlipkartReviewScraper

from app.models.product_response import ProductResponse
from app.models.review_response import ReviewResponse


def get_product_scraper_service() -> ScraperService[ProductResponse]:

    bright_data_browser = BrightDataBrowser(
        ws_url=settings.bright_data_browser
    )

    scraper = FlipkartProductScraper(bright_data_browser)

    return ScraperService(scraper)


def get_review_scraper_service() -> ScraperService[ReviewResponse]:

    client = ZembraClient()

    scraper = FlipkartReviewScraper(client)

    return ScraperService(scraper)
