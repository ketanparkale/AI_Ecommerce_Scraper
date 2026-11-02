
import asyncio

from app.llm.local_llm import LocalLLM


async def main():
    llm = LocalLLM()

    response = await llm.generate(
        messages=[
            {
                "role": "user",
                "content": "Explain what an AI agent is in two sentences."
            }
        ]
    )

    print("LLM Response:", response.text)
    print("Tool Calls:", response.tool_calls)


if __name__ == "__main__":
    asyncio.run(main())
