from fastapi import FastAPI, Depends
from app.scraper.scraper_service import ScraperService
from app.models.product_response import ProductResponse
from app.dependencies import get_scraper_service

app = FastAPI(
    title="Ecommerce AI Service",
    description="This is AI service for data processing",
    version="1.0.0"
)



@app.get("/scrape", tags=["Scraper"], response_model=ProductResponse)
async def scrape_product(
    product_url:str,
    scraper_service : ScraperService = Depends(get_scraper_service)
):
    result =  await scraper_service.scrape(product_url)
    return result


@app.get("/health", tags=["Health Check"])
def health_check():
    return {
        "status": "healthy",
        "message": "Ecommerce AI Service is running smoothly."
    }
