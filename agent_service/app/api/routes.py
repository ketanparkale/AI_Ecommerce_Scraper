import logging
from contextlib import asynccontextmanager
from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException

from app.rag.redis_review_store import ensure_review_index
from app.agents.product_agent import AgentExecutionError, ProductAgent
from app.clients.product_scraper_client import ProductScraperClient
from app.clients.review_scraper_client import ReviewScraperClient
from app.database.redis_client import connect_redis, close_redis, get_redis
from app.llm.langchain_llm import get_llm
from app.models.api_models import AgentRequest, AgentResponse
from app import dependencies

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

def get_agent(
    llm = Depends(get_llm),
) -> ProductAgent:

    tools = [
        dependencies.get_product_tool(),
        dependencies.get_review_tool(),
        dependencies.get_review_search_tool()
    ]

    return ProductAgent(
        llm=llm,
        tools=tools,
    )


@app.post("/agent/chat", response_model=AgentResponse)
async def chat(
    request: AgentRequest,
    agent: ProductAgent = Depends(get_agent),
):
    try:
        return await agent.run(request.message)

    except AgentExecutionError:
        logger.exception("Agent execution failed")
        raise HTTPException(
            status_code=502,
            detail="The AI service could not process the request.",
        )

    except Exception:
        logger.exception("Unexpected agent error")
        raise HTTPException(
            status_code=500,
            detail="Unable to process request.",
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