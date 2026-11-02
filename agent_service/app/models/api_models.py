from typing import Any
from pydantic import BaseModel,Field


class AgentRequest(BaseModel):
    message: str


class AgentResponse(BaseModel):
    answer: str | None = None
    tool_results: list[dict[str, Any]] = Field(default_factory=list)
    iteration_limit_reached: bool = False