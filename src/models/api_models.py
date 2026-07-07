from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    """API request model for asking a support question."""

    question: str = Field(
        ...,
        description="The support question from the employee.",
        min_length=1,
    )


class AnswerResponse(BaseModel):
    """API response model containing the question and LLM-generated answer."""

    question: str = Field(..., description="The original question asked.")
    answer: str = Field(..., description="The grounded AI-generated response.")
