from app.services.scraper_service import ScraperService
from app.browser.brightdata_browser import BrightDataBrowser
from app.config.settings import settings

def get_scraper_service() -> ScraperService:

    bright_data_browser = BrightDataBrowser(
        ws_url = settings.bright_data_browser
    )

    return ScraperService(
        bright_data_browser = bright_data_browser
    )