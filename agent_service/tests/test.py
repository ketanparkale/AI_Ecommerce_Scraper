import asyncio

from app.llm.langchain_llm import get_llm


async def main():
    llm = get_llm()

    response = await llm.ainvoke(
        "Explain what an ecommerce product review is in two sentences."
    )

    print(response.content)


if __name__ == "__main__":
    asyncio.run(main())