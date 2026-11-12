from langchain_openai import ChatOpenAI


def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model="mlx-community/Qwen3-4B-4bit",
        base_url="http://localhost:8080/v1",
        api_key="local",
        temperature=0,
        max_tokens=1500,
    )