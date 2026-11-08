from abc import ABC, abstractmethod

from app.rag.review_models import StoredReview


class ReviewRepository(ABC):

    @abstractmethod
    async def save_many(
        self,
        reviews: list[StoredReview]
    ) -> None:
        ...

    @abstractmethod
    async def search(
        self,
        product_id: str,
        query: str | None = None,
        min_rating: float | None = None,
        max_rating: float | None = None,
        limit: int = 10
    ) -> list[StoredReview]:
        ...

    @abstractmethod
    async def search_similar(
        self,
        product_id: str,
        embedding: list[float],
        limit: int = 5,
        min_rating: float | None = None,
        max_rating: float | None = None
    ) -> list[StoredReview]:
        ...

    @abstractmethod
    async def stats(
        self,
        product_id: str
    ) -> dict:
        ...