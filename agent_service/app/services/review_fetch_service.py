from app.clients.review_scraper_client import ReviewScraperClient
from app.models.review_model import ReviewResponse
from app.rag.review_document_mapper import ReviewDocumentMapper
from app.services.review_ingestion_service import ReviewIngestionService


class ReviewFetchService:

    def __init__(
        self,
        scraper_client: ReviewScraperClient,
        ingestion_service: ReviewIngestionService,
    ):
        self.scraper_client = scraper_client
        self.ingestion_service = ingestion_service

    async def fetch_and_ingest(
        self,
        product_url: str,
    ) -> dict:

        #Fetch raw response from scraper_service.
        raw_data = await self.scraper_client.scrape(product_url)

        response = ReviewResponse.model_validate(raw_data)

        # Convert API reviews into Redis documents.
        reviews = ReviewDocumentMapper.map_reviews(response)

        # Generate embeddings and save reviews in Redis.
        saved_count = await self.ingestion_service.ingest(reviews)

        return {
            "product_id": response.product_id,
            "product_title": response.product_title,
            "fetched_count": response.returned_count,
            "mapped_count": len(reviews),
            "saved_count": saved_count,
        }