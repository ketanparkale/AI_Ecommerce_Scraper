from fastapi import APIRouter, Depends, Query

from app.services.scraper_service import ScraperService
from app.models.product_response import ProductResponse
from app.dependencies import get_review_scraper_service, get_product_scraper_service
from app.models.review_response import ReviewResponse
from app.scraper.flipkart_review_scraper import FlipkartReviewScraper

router = APIRouter(prefix="/scrape", tags=["scrape"])


@router.get("/product", response_model=ProductResponse)
async def scrape_product(
    product_url: str,
    scraper_service: ScraperService = Depends(get_product_scraper_service),
):
    return await scraper_service.scrape(product_url)

@router.get("/reviews", response_model=ReviewResponse)
async def scrape_reviews(
    product_url : str,
    scraper : FlipkartReviewScraper = Depends(get_review_scraper_service)
):
    return await scraper.scrape(product_url)