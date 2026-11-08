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

    print("Number of embeddings:", len(embeddings))
    print("Dimensions:", len(embeddings[0]))
    print("First 10 values:", embeddings[0][:10])


if __name__ == "__main__":
    asyncio.run(main())