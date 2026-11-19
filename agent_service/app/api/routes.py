
import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException
from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.graph.state import CompiledStateGraph

from app.rag.redis_review_store import ensure_review_index
from app.database.redis_client import connect_redis, close_redis, get_redis
from app.models.api_models import (
    AgentRequest,
    AgentResponse,
    AgentAnswer,
)
from app import dependencies


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_redis()

    try:
        await ensure_review_index()
        await dependencies.initialize_agent_graph()
        yield
    finally:
        await close_redis()


app = FastAPI(
    title="Ecommerce AI Agent API",
    description="AI-powered ecommerce assistant",
    version="1.0.0",
    lifespan=lifespan,
)


def get_agent_graph() -> CompiledStateGraph:
    return dependencies.get_agent_graph()


@app.post("/agent/chat", response_model=AgentResponse)
async def chat(
    request: AgentRequest,
    graph: CompiledStateGraph = Depends(get_agent_graph),
):
    try:
        print("inside the chat function")
        conversation_id = request.conversation_id or uuid4()
        config = {
            "configurable": {
                "thread_id": str(conversation_id)
            },
            "recursion_limit": 15,
        }

        logger.info(
            "Processing conversation: %s",
            conversation_id,
        )

        result = await graph.ainvoke(
            {
                "messages": [
                    HumanMessage(content=request.message)
                ]
            },
            config=config,
        )

        # Get the structured response from the graph state.
        structured_answer = result.get("answer")

        if structured_answer is None:
            answer = AgentAnswer(
                summary="I couldn't generate an answer. Please try again."
            )

        else:
            if hasattr(structured_answer, "model_dump"):
                structured_answer = structured_answer.model_dump()

            answer = AgentAnswer.model_validate(structured_answer)

        # Collect tool execution results.
        tool_results = []
        print("result messages: ", result["messages"])
        for message in result["messages"]:
            if isinstance(message, ToolMessage):
                tool_results.append({
                    "tool": message.name,
                    "result": message.content,
                    "error": message.status == "error",
                })

        return AgentResponse(
            conversation_id=conversation_id,
            answer=answer,
            tool_results=tool_results,
            iteration_limit_reached=False,
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
            detail="Redis is unavailable",
        )
