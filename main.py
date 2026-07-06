"""
IntelliDesk - RAG-based AI Support Ticket Resolver
FastAPI Backend Entry Point
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import logging

from src.pipeline import run_pipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="IntelliDesk API",
    description="RAG-based AI Support Ticket Resolver for internal employee queries",
    version="1.0.0",
)


class QuestionRequest(BaseModel):
    question: str


class AnswerResponse(BaseModel):
    question: str
    answer: str


@app.get("/health", summary="Health check endpoint")
def health_check():
    """Returns service health status."""
    return {"status": "ok", "service": "IntelliDesk"}


@app.post("/ask", response_model=AnswerResponse, summary="Ask a support question")
def ask_question(request: QuestionRequest):
    """
    Accepts an employee support question, retrieves relevant knowledge-base
    chunks via FAISS, and returns a grounded answer from the LLM.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    logger.info(f"Received question: {request.question!r}")
    answer = run_pipeline(request.question)

    return AnswerResponse(question=request.question, answer=answer)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
