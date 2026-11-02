
import json
import logging
from typing import Any
 
from app.llm.base import BaseLLM
 
logger = logging.getLogger(__name__)
 
SYSTEM_PROMPT = (
    "You are an ecommerce product assistant. "
    "Use the available tools to retrieve product information. "
    "Base your answers only on tool results. "
    "If a tool fails or data looks incomplete, say so honestly. "
    "Never invent prices, sizes, or availability."
)
 
SYNTHESIS_SYSTEM_PROMPT = "You are an ecommerce assistant."
 
EMPTY_ANSWER_MESSAGE = "I retrieved the product data but couldn't summarize it."
NO_DATA_MESSAGE = "I couldn't find any product data to answer that."
 
 
class ProductAgent:
    def __init__(
        self,
        llm: BaseLLM,
        tools: list[Any],
        max_iterations: int = 5,
    ):
        self.llm = llm
        self.max_iterations = max_iterations
        self.tools = {
            tool.definition["function"]["name"]: tool
            for tool in tools
        }
 
    async def run(self, user_message: str) -> dict[str, Any]:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]
        
        tool_definitions = [t.definition for t in self.tools.values()]
        all_results: list[dict[str, Any]] = []
        limit_reached = False

        # for-else: runs only if the loop ended without break
        for iteration in range(self.max_iterations):
            response = await self.llm.generate(
                messages=messages,
                tools=tool_definitions or None,
            )
            logger.info(
                "iter=%s text=%r tool_calls=%s",
                iteration, response.text, response.tool_calls,
            )
 
            # No tool calls: the model is either done or returned nothing.
            if not response.tool_calls:
                text = (response.text or "").strip()
                if text:
                    return self._result(text, all_results, limit_reached=False)
                break
 
            # Record the assistant's tool calls in the conversation.
            messages.append({
                "role": "assistant",
                "content": response.text or "",
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.name,
                            "arguments": json.dumps(call.arguments),
                        },
                    }
                    for call in response.tool_calls
                ],
            })
 
            # Run each tool and feed its result back to the model.
            for call in response.tool_calls:
                result = await self._run_tool(call)
                all_results.append({"tool": call.name, "result": result})
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                })
        else:
            # Loop finished without the model giving a final answer.
            limit_reached = True
 
        answer = await self._synthesize(user_message, all_results)
        return self._result(answer, all_results, limit_reached)
 
    async def _run_tool(self, call) -> Any:
        tool = self.tools.get(call.name)
        if tool is None:
            return {"error": f"Unknown tool {call.name}"}
 
        try:
            result = await tool.execute(**call.arguments)
            return result.model_dump() if hasattr(result, "model_dump") else result
        except Exception:
            logger.exception("Tool %s failed", call.name)
            return {
                "error": f"Tool '{call.name}' failed. The operation could not be completed."
            }
 
    async def _synthesize(self, user_message: str, all_results: list[dict[str, Any]]) -> str:
        """Turn raw tool results into a natural-language answer (no tools allowed)."""
        if not all_results:
            return NO_DATA_MESSAGE
 
        prompt = (
            f"User question: {user_message}\n\n"
            f"Tool results (JSON):\n"
            f"{json.dumps(all_results, ensure_ascii=False, default=str)}\n\n"
            "Answer the user's question in a short, friendly way using ONLY this data. "
            "Do not invent sizes, prices or availability. "
            "If the data looks incomplete or contains an error, say so."
        )
        response = await self.llm.generate(
            messages=[
                {"role": "system", "content": SYNTHESIS_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            tools=None,
        )
        return (response.text or "").strip() or EMPTY_ANSWER_MESSAGE
 
    @staticmethod
    def _result(
        answer: str,
        tool_results: list[dict[str, Any]],
        limit_reached: bool,
    ) -> dict[str, Any]:
        return {
            "answer": answer,
            "tool_results": tool_results,
            "iteration_limit_reached": limit_reached,
        }