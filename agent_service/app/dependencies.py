
from functools import lru_cache

from langchain_core.tools import StructuredTool

from app.clients.product_scraper_client import ProductScraperClient
from app.clients.review_scraper_client import ReviewScraperClient

from app.rag.redis_review_store import RedisReviewStore

from app.services.embedding_service import EmbeddingService
from app.services.review_search_service import ReviewSearchService
from app.services.review_fetch_service import ReviewFetchService
from app.services.review_ingestion_service import ReviewIngestionService

from app.tools.product_tool import create_product_tool
from app.tools.review_tool import create_review_tool
from app.tools.review_search_tool import create_review_search_tool
from app.agents.agent_graph import build_agent_graph
from app.llm.langchain_llm import get_llm
from langgraph.checkpoint.redis.aio import AsyncRedisSaver

from app.database.redis_client import get_redis
from app.agents.agent_graph import build_agent_graph
import logging


logger = logging.getLogger(__name__)

# Scraper clients

@lru_cache
def get_product_scraper_client() -> ProductScraperClient:
    return ProductScraperClient()


@lru_cache
def get_review_scraper_client() -> ReviewScraperClient:
    return ReviewScraperClient()


# Redis repository

@lru_cache
def get_review_repository() -> RedisReviewStore:
    return RedisReviewStore()


# Embedding service

@lru_cache
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()


# Review services

@lru_cache
def get_review_ingestion_service() -> ReviewIngestionService:
    return ReviewIngestionService(
        embedding_service=get_embedding_service(),
        review_repository=get_review_repository(),
    )


@lru_cache
def get_review_fetch_service() -> ReviewFetchService:
    return ReviewFetchService(
        scraper_client=get_review_scraper_client(),
        ingestion_service=get_review_ingestion_service(),
    )


@lru_cache
def get_review_search_service() -> ReviewSearchService:
    return ReviewSearchService(
        embedding_service=get_embedding_service(),
        review_repository=get_review_repository(),
    )


# LangChain tools

@lru_cache
def get_product_tool() -> StructuredTool:
    return create_product_tool(
        get_product_scraper_client()
    )


@lru_cache
def get_review_tool() -> StructuredTool:
    return create_review_tool(
        get_review_fetch_service()
    )


@lru_cache
def get_review_search_tool() -> StructuredTool:
    return create_review_search_tool(
        get_review_search_service()
    )

@lru_cache
def get_agent_graph():
    tools = [
        get_product_tool(),
        get_review_tool(),
        get_review_search_tool(),
    ]

    return build_agent_graph(
        llm=get_llm(),
        tools=tools,
    )



# LangGraph initialization

_agent_graph = None
_checkpointer = None


async def initialize_agent_graph():

    global _agent_graph, _checkpointer

    tools = [
        get_product_tool(),
        get_review_tool(),
        get_review_search_tool(),
    ]

   
    ttl_config = {
        "default_ttl": 1440,       # Minutes
        "refresh_on_read": True,
    }

    # Reuse the existing asynchronous Redis connection.
    _checkpointer = AsyncRedisSaver(
        redis_client=get_redis(),
        checkpoint_prefix="agent_checkpoint",
        checkpoint_write_prefix="agent_checkpoint_write",
        ttl=ttl_config,
    )

    # Create the required Redis indexes.
    await _checkpointer.asetup()

    # Compile the graph with persistent state.
    _agent_graph = build_agent_graph(
        llm=get_llm(),
        tools=tools,
        checkpointer=_checkpointer,
    )


def get_agent_graph():

    if _agent_graph is None:
        raise RuntimeError(
            "Agent graph has not been initialized."
        )

    return _agent_graph