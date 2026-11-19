import asyncio

from app.services.embedding_service import EmbeddingService


async def main():
    embedding_service = EmbeddingService()

    reviews = [
        "These shoes are comfortable for daily running.",
        "The grip is poor on wet roads.",
        "The outsole is very durable."
    ]

    embeddings = await embedding_service.embed_texts(reviews)


if __name__ == "__main__":
    asyncio.run(main())