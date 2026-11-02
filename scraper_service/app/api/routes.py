from fastapi import APIRouter, Depends, Query

from app.services.scraper_service import ScraperService
from app.models.product_response import ProductResponse
from app.dependencies import get_scraper_service

router = APIRouter(prefix="/scrape", tags=["scrape"])


@router.get("/product", response_model=ProductResponse)
async def scrape_product(
    product_url: str,
    scraper_service: ScraperService = Depends(get_scraper_service),
):
    return await scraper_service.scrape(product_url)
