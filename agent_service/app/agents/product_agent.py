
import asyncio
import json
import logging
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool
import app.prompts.product_prompt as prompts

logger = logging.getLogger(__name__)

NO_DATA_MESSAGE = (
    "I couldn't retrieve enough product information to answer that."
)

EMPTY_ANSWER_MESSAGE = (
    "I retrieved the product data but couldn't generate a summary."
)

TOOL_RESULT_MAX_CHARS = 12_000


class AgentExecutionError(Exception):
    """Raised when the agent cannot communicate with the language model."""


class ProductAgent:

    def __init__(
        self,
        llm: BaseChatModel,
        tools: list[BaseTool],
        max_iterations: int = 5,
        tool_result_max_chars: int = TOOL_RESULT_MAX_CHARS,
    ) -> None:

        if not tools:
            raise ValueError("At least one tool must be registered.")

        if len({tool.name for tool in tools}) != len(tools):
            raise ValueError("Tool names must be unique.")

        if max_iterations < 1:
            raise ValueError("max_iterations must be at least 1.")

        if tool_result_max_chars < 1:
            raise ValueError("tool_result_max_chars must be positive.")

        self.llm = llm
        self.max_iterations = max_iterations
        self.tool_result_max_chars = tool_result_max_chars

        self.tools = {
            tool.name: tool
            for tool in tools
        }

        # The model must support LangChain tool binding.
        self.llm_with_tools = self.llm.bind_tools(tools)

    async def run(self, user_message: str) -> dict[str, Any]:
        """
        Execute an agent conversation.

        Conversation messages and tool results are local to this call.
        The ProductAgent instance can therefore be shared across requests.
        """

        prompt_value = prompts.product_assistant_prompt.invoke({
            "user_message": user_message
        })

        messages = prompt_value.to_messages()

        tool_results: list[dict[str, Any]] = []

        for iteration in range(self.max_iterations):

            response = await self._invoke_model(
                self.llm_with_tools,
                messages,
                operation="tool selection",
            )

            logger.info(
                "Agent iteration %d completed; tool calls: %d",
                iteration + 1,
                len(response.tool_calls),
            )

            # The model has finished without requesting another tool.
            if not response.tool_calls:
                answer = self._extract_text(response.content)

                if answer:
                    return self._build_result(
                        answer,
                        tool_results,
                        iteration_limit_reached=False,
                    )

                # Empty response: ask the model to finish using history.
                break

            # Preserve the assistant message containing the tool calls.
            messages.append(response)

            # Execute independent tool calls concurrently.
            tool_messages = await asyncio.gather(
                *(
                    self._execute_tool(call)
                    for call in response.tool_calls
                )
            )

            for call, tool_message in zip(
                response.tool_calls,
                tool_messages,
            ):
                messages.append(tool_message)

                tool_results.append({
                    "tool": call["name"],
                    "result": self._parse_tool_message(
                        tool_message.content
                    ),
                    "error": tool_message.status == "error",
                })

        else:
            # The loop exhausted its allowed iterations.
            return await self._finish(
                messages,
                tool_results,
                iteration_limit_reached=True,
            )

        # The model returned empty content without requesting tools.
        return await self._finish(
            messages,
            tool_results,
            iteration_limit_reached=False,
        )

    async def _execute_tool(
        self,
        call: dict[str, Any],
    ) -> ToolMessage:
        """Execute one tool and return its corresponding ToolMessage."""

        tool_name = call["name"]
        tool = self.tools.get(tool_name)

        if tool is None:
            return self._tool_error(
                call["id"],
                f"Unknown tool: {tool_name}",
            )

        try:
            result = await tool.ainvoke(call["args"])

            content = self._serialize_tool_result(result)

            return ToolMessage(
                content=content,
                tool_call_id=call["id"],
                status="success",
            )

        except Exception:
            logger.exception(
                "Tool execution failed: %s",
                tool_name,
            )

            return self._tool_error(
                call["id"],
                (
                    f"Tool '{tool_name}' could not complete "
                    "the requested operation. Check the arguments "
                    "or try again."
                ),
            )

    async def _finish(
        self,
        messages: list,
        tool_results: list[dict[str, Any]],
        iteration_limit_reached: bool,
    ) -> dict[str, Any]:
        """Ask the model to produce a final answer from conversation history."""

        final_instruction = prompts.FINAL_ANSWER_INSTRUCTION

        if iteration_limit_reached:
            final_instruction += """
            The agent reached its maximum tool-call iteration limit.
            The retrieved information may be incomplete. Make this clear in your answer.
            """

        messages.append(
            HumanMessage(content=final_instruction)
        )

        try:
            response = await self._invoke_model(
                self.llm,
                messages,
                operation="final answer",
            )

            answer = self._extract_text(response.content)

            if not answer:
                answer = EMPTY_ANSWER_MESSAGE

        except AgentExecutionError:
            logger.exception("Could not generate the final answer")

            # Preserve all successfully retrieved tool results.
            answer = (
                "The product information was retrieved, "
                "but I couldn't generate the final answer. "
                "Please try again."
            )

        return self._build_result(
            answer,
            tool_results,
            iteration_limit_reached,
        )

    async def _invoke_model(
        self,
        model: BaseChatModel,
        messages: list,
        operation: str,
    ) -> AIMessage:
        """Invoke the model and normalize failures."""

        try:
            response = await model.ainvoke(messages)

            if not isinstance(response, AIMessage):
                raise TypeError(
                    "The chat model did not return an AIMessage."
                )

            return response

        except Exception as exc:
            logger.exception("LLM operation failed: %s", operation)

            raise AgentExecutionError(
                f"The language model failed during {operation}."
            ) from exc

    def _serialize_tool_result(self, result: Any) -> str:
        """Serialize a tool result while enforcing a size limit."""

        if hasattr(result, "model_dump"):
            result = result.model_dump(
                mode="json",
                exclude_none=True,
            )

        elif isinstance(result, str):
            try:
                result = json.loads(result)
            except json.JSONDecodeError:
                pass

        serialized = json.dumps(
            result,
            ensure_ascii=False,
            default=str,
        )

        if len(serialized) <= self.tool_result_max_chars:
            return serialized

        # Preserve valid JSON and explicitly indicate truncation.
        truncated_result = {
            "truncated": True,
            "message": (
                "The tool result exceeded the allowed size. "
                "The preview may not contain all retrieved information."
            ),
            "preview": serialized[
                : self.tool_result_max_chars // 2
            ],
        }

        return json.dumps(
            truncated_result,
            ensure_ascii=False,
        )

    @staticmethod
    def _parse_tool_message(content: Any) -> Any:
        """Convert JSON tool content back into Python data for the API."""

        if isinstance(content, str):
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return content

        return content

    @staticmethod
    def _extract_text(content: Any) -> str:
        """Extract text from string or block-based model responses."""

        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            return "".join(
                block.get("text", "")
                for block in content
                if isinstance(block, dict)
                and block.get("type") == "text"
            ).strip()

        return ""

    @staticmethod
    def _tool_error(
        tool_call_id: str,
        message: str,
    ) -> ToolMessage:

        return ToolMessage(
            content=json.dumps({
                "error": True,
                "message": message,
            }),
            tool_call_id=tool_call_id,
            status="error",
        )

    @staticmethod
    def _build_result(
        answer: str,
        tool_results: list[dict[str, Any]],
        iteration_limit_reached: bool,
    ) -> dict[str, Any]:

        return {
            "answer": answer,
            "tool_results": tool_results,
            "iteration_limit_reached": iteration_limit_reached,
        }
