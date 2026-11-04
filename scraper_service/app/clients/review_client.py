from typing import Protocol


class ReviewsClient(Protocol):

    async def fetch_reviews(
        self,
        network: str,
        slug: str,
        monitoring: str = "none"
    ) -> dict:
        ...