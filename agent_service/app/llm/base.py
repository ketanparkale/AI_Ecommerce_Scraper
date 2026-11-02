from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel,Field

class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any]

class LLMResponse(BaseModel):
    text : str | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)

class BaseLLM(ABC):
    @abstractmethod
    async def generate(
        self,
        messages: list[dict[str,Any]],
        tools : list[dict[str,Any]] | None = None,
        ) -> LLMResponse: 
        ...