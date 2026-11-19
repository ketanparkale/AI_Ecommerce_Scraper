import pytest

from app.api.routes import chat
from app.models.agent_response import ReviewSummary
from app.models.api_models import (
    AgentRequest,
    AnswerSection,
    ReviewItem,
)


class StubGraph:
    def __init__(self, answer):
        self.answer = answer

    async def ainvoke(self, state, *, config):
        self.last_state = state
        self.last_config = config
        return {
            "answer": self.answer,
            "messages": [],
        }


@pytest.mark.asyncio
async def test_chat_preserves_structured_answer_sections():
    expected_section = AnswerSection(
        title="Cushioning",
        content="A reviewer described the cushioning as soft.",
    )
    expected_review = ReviewItem(
        text="The cushioning is soft.",
    )
    graph = StubGraph(
        ReviewSummary(
            summary="The cushioning feels soft.",
            sections=[expected_section],
            reviews=[expected_review],
        )
    )

    response = await chat(
        AgentRequest(message="How is the cushioning?"),
        graph=graph,
    )

    assert response.answer.summary == "The cushioning feels soft."
    assert response.answer.sections == [expected_section]
    assert response.answer.reviews == [expected_review]


@pytest.mark.asyncio
async def test_chat_keeps_fallback_when_graph_answer_is_missing():
    response = await chat(
        AgentRequest(message="Question"),
        graph=StubGraph(None),
    )

    assert response.answer.summary == (
        "I couldn't generate an answer. Please try again."
    )
    assert response.answer.sections == []
    assert response.answer.reviews == []
