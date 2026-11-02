from typing import Any
from openai import AsyncOpenAI
from app.llm.base import BaseLLM, LLMResponse, ToolCall
import json

class LocalLLM(BaseLLM):
    def __init__(
        self,
        baseurl: str = "http://localhost:8080/v1",
        model:str = "mlx-community/Qwen3-4B-4bit"
        ):

        self.client = AsyncOpenAI(base_url=baseurl, api_key="local")

        self.model = model

    async def generate(self,messages: list[dict[str,Any]], tools : list[dict[str,Any]] | None = None) -> LLMResponse:

        response = await self.client.chat.completions.create(
            model = self.model,
            messages = messages,
            tools = tools,
            max_tokens = 1500
        )

        choice = response.choices[0]
        message = choice.message

        tool_calls = []

        if message.tool_calls:
            for call in message.tool_calls:
                tool_calls.append(
                    ToolCall(
                        id=call.id,
                        name=call.function.name,
                        arguments=json.loads(call.function.arguments),
                    )
                )


        return LLMResponse(
            text = message.content,
            tool_calls = tool_calls
        )        