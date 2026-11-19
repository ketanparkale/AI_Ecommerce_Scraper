import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from app.agents.agent_graph import build_agent_graph
from app.models.agent_response import ReviewSummary


class StubLLM:
    def bind_tools(self, _tools):
        return self

    async def ainvoke(self, _prompt):
        return AIMessage(content="No additional review search was needed.")


@pytest.mark.asyncio
async def test_graph_resets_search_state_and_preserves_product_context():
    graph = build_agent_graph(StubLLM(), [], InMemorySaver())
    product = {
        "product_id": "product-1",
        "title": "Running shoe",
        "url": "https://example.com/product-1",
    }
    config = {"configurable": {"thread_id": "conversation-1"}}

    await graph.ainvoke(
        {
            "messages": [HumanMessage(content="Tell me about this shoe.")],
            "products": {"product-1": product},
            "current_product_id": "product-1",
            "current_product_title": "Running shoe",
            "current_product_url": "https://example.com/product-1",
        },
        config=config,
    )
    await graph.aupdate_state(
        config,
        {
            "review_search_status": "success",
            "review_search_results": [{"review": "stale review"}],
            "answer": ReviewSummary(
                summary="Stale answer",
                sections=[],
                reviews=[],
            ),
        },
    )

    result = await graph.ainvoke(
        {"messages": [HumanMessage(content="Is the shoe comfortable?")]},
        config=config,
    )

    assert result["review_search_status"] is None
    assert result["review_search_results"] == []
    assert result["answer"].summary == (
        "No relevant customer reviews were retrieved."
    )
    assert result["products"] == {"product-1": product}
    assert result["current_product_id"] == "product-1"
    assert result["current_product_title"] == "Running shoe"
    assert result["current_product_url"] == product["url"]
    human_messages = [
        message.content
        for message in result["messages"]
        if isinstance(message, HumanMessage)
    ]
    assert human_messages == [
        "Tell me about this shoe.",
        "Is the shoe comfortable?",
    ]
