from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AnswerSection(BaseModel):
    title: str
    content: str


class ReviewItem(BaseModel):
    rating: float | None = None
    title: str | None = None
    text: str


class AgentAnswer(BaseModel):
    summary: str
    sections: list[AnswerSection] = Field(default_factory=list)
    reviews: list[ReviewItem] = Field(default_factory=list)


class AgentRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: UUID | None = None


class AgentResponse(BaseModel):
    conversation_id: UUID
    answer: AgentAnswer
    tool_results: list[dict[str, Any]] = Field(default_factory=list)
    iteration_limit_reached: bool = False