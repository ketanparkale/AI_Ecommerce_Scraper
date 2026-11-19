from pydantic import BaseModel, Field

from app.models.api_models import AnswerSection, ReviewItem


class ReviewSummary(BaseModel):

    summary: str = Field(
        description="A concise summary answering the user's question."
    )

    sections: list[AnswerSection] = Field(
        default_factory=list,
        description="Structured findings with a title and supporting content."
    )

    reviews: list[ReviewItem] = Field(
        default_factory=list,
        description="Relevant customer reviews supporting the answer."
    )