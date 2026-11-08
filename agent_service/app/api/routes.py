import logging
from contextlib import asynccontextmanager
from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException

from app.rag.redis_review_store import ensure_review_index
from app.agents.product_agent import ProductAgent
from app.clients.product_scraper_client import ProductScraperClient
from app.clients.review_scraper_client import ReviewScraperClient
from app.database.redis_client import connect_redis, close_redis, get_redis
from app.llm.local_llm import LocalLLM
from app.models.api_models import AgentRequest, AgentResponse
from app.tools.product_tool import ProductTool
from app.tools.review_tool import ReviewTool

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_redis()
    try:
        await ensure_review_index()
        yield
    finally:
        await close_redis()


app = FastAPI(
    title="Ecommerce AI Agent API",
    description="AI-powered ecommerce assistant",
    version="1.0.0",
    lifespan=lifespan,
)

@lru_cache
def get_llm() -> LocalLLM:
    return LocalLLM()

@lru_cache
def get_product_scraper_client() -> ProductScraperClient:
    return ProductScraperClient()


@lru_cache
def get_review_scraper_client() -> ReviewScraperClient:
    return ReviewScraperClient()

def get_agent(
    llm: LocalLLM = Depends(get_llm),
    product_scraper: ProductScraperClient = Depends(
        get_product_scraper_client
    ),
    review_scraper: ReviewScraperClient = Depends(
        get_review_scraper_client
    ),
) -> ProductAgent:

    tools = [
        ProductTool(product_scraper),
        ReviewTool(review_scraper),
    ]

    return ProductAgent(llm=llm, tools=tools)


@app.post("/agent/chat", response_model = AgentResponse)
async def chat(
    request : AgentRequest,
    agent : ProductAgent = Depends(get_agent)
):
    try:
        return await agent.run(request.message)
    except Exception:
        logger.exception("Agent execution failed")
        raise HTTPException(
            status_code=500,
            detail="Unable to process request"
        )

@app.get("/redis-health", tags=["Health"])
async def redis_health():
    try:
        client = get_redis()
        await client.ping()

        return {"redis": "connected"}

    except Exception:
        logger.exception("Redis health check failed")
        raise HTTPException(
            status_code=503,
            detail="Redis is unavailable"
        )    