from fastapi import FastAPI, Depends

from app.agents.product_agent import ProductAgent
from app.llm.local_llm import LocalLLM
from agent_service.app.clients.product_scraper_client import ScraperClient
from app.tools.product_tool import ProductTool
from app.models.api_models import AgentRequest, AgentResponse
import logging
from fastapi import HTTPException
from functools import lru_cache

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Ecommerce AI Agent API",
    description="AI-powered ecommerce assistant",
    version="1.0.0"
)

@lru_cache
def get_llm() -> LocalLLM:
    return LocalLLM()

@lru_cache
def get_scraper_client() -> ScraperClient:
    return ScraperClient()

def get_agent(
    llm: LocalLLM = Depends(get_llm),
    scraper: ScraperClient = Depends(get_scraper_client),
) -> ProductAgent:
    return ProductAgent(llm=llm, tools=[ProductTool(scraper)])


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