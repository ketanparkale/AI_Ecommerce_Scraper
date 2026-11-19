import asyncio

from app.database.redis_client import connect_redis, close_redis
from app.rag.redis_review_store import RedisReviewStore


async def main():

    await connect_redis()

    try:
        store = RedisReviewStore()

        reviews = await store.get_all(
            product_id="itm597ecf6078978"
        )

    finally:
        await close_redis()


if __name__ == "__main__":
    asyncio.run(main())