
import json
import logging
import re

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser

from app.agents.graph_state import AgentState
from app.models.agent_response import ReviewSummary
from app.prompts.product_prompt import product_assistant_prompt
from app.models.api_models import AnswerSection


logger = logging.getLogger(__name__)

THINK_PATTERN = re.compile(r"<think>.*?</think>", re.DOTALL)


def _turn_messages(state: AgentState) -> list:
    """Return messages belonging to the current user turn."""

    messages = state["messages"]

    last_human = max(
        (
            i
            for i, message in enumerate(messages)
            if isinstance(message, HumanMessage)
        ),
        default=-1,
    )

    return messages[last_human + 1:]


def _last_ai_text(state: AgentState) -> str:
    """Get the latest assistant response for the current turn."""

    for message in reversed(_turn_messages(state)):

        if (
            isinstance(message, AIMessage)
            and not message.tool_calls
            and message.content
        ):
            return str(message.content).strip()

    return ""


def _strip_think(text: str) -> str:
    """Remove Qwen reasoning tags from the response."""

    return THINK_PATTERN.sub("", text or "").strip()


def build_agent_graph(llm, tools, checkpointer):

    # Bind tools to the LLM.
    llm_with_tools = llm.bind_tools(tools)

    builder = StateGraph(AgentState)


    async def reset_request_state(state: AgentState):

        return {
            "review_search_status": None,
            "review_search_results": [],
            "answer": None,
        }


    async def agent_node(state: AgentState):

        prompt_value = product_assistant_prompt.invoke({
            "messages": state["messages"]
        })

        response = await llm_with_tools.ainvoke(prompt_value)

        logger.info(
            "Agent response | tool_calls=%s",
            len(response.tool_calls),
        )

        return {
            "messages": [response]
        }


    async def format_response_node(state: AgentState):

        review_search_results = state.get(
            "review_search_results",
            []
        )

        # No review search was performed.
        # Return the LLM's direct response.
        if not review_search_results:

            draft = _last_ai_text(state)

            return {
                "answer": ReviewSummary(
                    summary=(
                        draft
                        or "No relevant customer reviews were retrieved."
                    ),
                    sections=[],
                    reviews=[],
                )
            }

        parser = PydanticOutputParser(
            pydantic_object=ReviewSummary
        )

        user_message = ""

        for message in reversed(state["messages"]):

            if isinstance(message, HumanMessage):
                user_message = str(message.content)
                break

        prompt = f"""
        You are an ecommerce product review analyst.

        Answer the user's question using ONLY the customer reviews below.

        Rules:

        1. Read each review's title and text.
        Ignore the distance values; they show similarity, not relevance.

        2. Classify each review:

        DIRECT:
        Explicitly answers the user's question.

        RELATED:
        Discusses the same general topic but does not directly answer
        the user's question.

        IRRELEVANT:
        Does not address the user's question.

        3. Base the answer on DIRECT reviews.
        Mention RELATED reviews separately and explain what they do not tell us.
        Leave out IRRELEVANT reviews.

        4. If there is no DIRECT review, clearly say that the answer
        was not found in the retrieved reviews.

        Never claim that no customer has ever mentioned it.

        5. Do not treat a high rating as proof of a specific feature.
        Do not turn one customer's opinion into a general fact.
        Do not claim a majority opinion.

        6. For claims such as fake products or defects, distinguish:
        - A customer who confirms the opposite.
        - A customer who suspects something.
        - A customer who explicitly states something.

        Suspicion is not proof.

        7. Include reviews that contradict each other.

        8. Never change or invent review text, ratings or authors.

        9. Populate the reviews field with the actual DIRECT and RELATED
        reviews used in your answer. Do not leave it empty when relevant
        reviews are available.

        10. Preserve the original review text and author information.

        Return actual JSON, not a JSON schema.
        Do not include explanations outside JSON.

        {parser.get_format_instructions()}

        User question:
        {user_message}

        Review data:
        {json.dumps(review_search_results, ensure_ascii=False)}
        """

        answer = None

        for attempt in range(2):

            response = await llm.ainvoke(prompt)

            try:

                answer = parser.parse(
                    _strip_think(str(response.content))
                )

                break

            except Exception:

                logger.warning(
                    "Could not parse formatted answer (attempt %s)",
                    attempt + 1,
                )

        if answer is None:

            answer = ReviewSummary(
                summary=(
                    f"I retrieved {len(review_search_results)} reviews "
                    "but could not summarise them reliably. "
                    "Please try again."
                ),
                sections=[],
                reviews=[],
            )

        return {
            "answer": answer,
            "messages": [
                AIMessage(content=answer.summary)
            ],
        }

    # Handle empty search results

    async def no_matches_node(state: AgentState):

        answer = ReviewSummary(
            summary=(
                "I couldn't find sufficiently relevant customer reviews "
                "to answer that question from the retrieved reviews."
            ),
            sections=[
                AnswerSection(
                    title="Search results",
                    content="No sufficiently relevant reviews were found.",
                )
            ],
            reviews=[],
        )

        return {
            "answer": answer,
            "messages": [
                AIMessage(content=answer.summary)
            ],
        }

    # Handle search errors

    async def search_error_node(state: AgentState):

        answer = ReviewSummary(
            summary=(
                "I couldn't retrieve the reviews needed to answer "
                "that question right now. Please try again later."
            ),
            sections=[],
            reviews=[],
        )

        return {
            "answer": answer,
            "messages": [
                AIMessage(content=answer.summary)
            ],
        }
 

    def route_after_agent(state: AgentState) -> str:

        last_message = state["messages"][-1]

        # The LLM requested one or more tools.
        if (
            isinstance(last_message, AIMessage)
            and last_message.tool_calls
        ):
            return "tools"

        # The LLM answered directly.
        return "format_response"

    def route_after_tools(state: AgentState) -> str:

        status = state.get("review_search_status")

        if status == "success":
            return "format_response"

        if status == "no_matches":
            return "no_matches"

        if status == "error":
            return "search_error"

        # Return control to the LLM so it can decide what to do next.
        return "agent"


    # Graph wiring

    builder.add_node(
        "reset_request_state",
        reset_request_state,
    )

    builder.add_node(
        "agent",
        agent_node,
    )

    builder.add_node(
        "tools",
        ToolNode(tools),
    )

    builder.add_node(
        "format_response",
        format_response_node,
    )

    builder.add_node(
        "no_matches",
        no_matches_node,
    )

    builder.add_node(
        "search_error",
        search_error_node,
    )

    builder.add_edge(
        START,
        "reset_request_state",
    )

    builder.add_edge(
        "reset_request_state",
        "agent",
    )

    builder.add_conditional_edges(
        "agent",
        route_after_agent,
        {
            "tools": "tools",
            "format_response": "format_response",
        },
    )

    builder.add_conditional_edges(
        "tools",
        route_after_tools,
        {
            "agent": "agent",
            "format_response": "format_response",
            "no_matches": "no_matches",
            "search_error": "search_error",
        },
    )

    builder.add_edge(
        "format_response",
        END,
    )

    builder.add_edge(
        "no_matches",
        END,
    )

    builder.add_edge(
        "search_error",
        END,
    )

    return builder.compile(
        checkpointer=checkpointer
    )
