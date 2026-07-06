"""
IntelliDesk - RAG-based AI Support Ticket Resolver
FastAPI Backend Entry Point
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import logging

from src.pipeline import run_pipeline

import time

# Configure logging (both to console and app.log file)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
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
    start_time = time.time()
    try:
        answer = run_pipeline(request.question)
        elapsed_time = time.time() - start_time
        logger.info(f"Generated answer in {elapsed_time:.3f} seconds.")
        return AnswerResponse(question=request.question, answer=answer)
    except Exception as exc:
        logger.error(f"Error resolving ticket: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error resolving question.")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
