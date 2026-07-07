import logging
import time
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from src.models.api_models import QuestionRequest, AnswerResponse
from src.services.pipeline import run_pipeline
from src.utils.logger import setup_logging

logger = logging.getLogger(__name__)

# Initialize central logging configuration
setup_logging()

app = FastAPI(
    title="IntelliDesk API",
    description="Production-ready RAG-based AI Support Ticket Resolver",
    version="1.0.0",
)


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Custom validation handler returning HTTP 400 for structural invalidity."""
    logger.error(f"Validation error for path {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": "Invalid request structure.",
            "errors": exc.errors(),
        },
    )


@app.exception_handler(Exception)
def global_exception_handler(request: Request, exc: Exception):
    """Global exception fallback to prevent leakage of internal stacktraces."""
    logger.error(
        f"Unhandled exception encountered at {request.url.path}: {exc}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred resolving your request."},
    )


@app.get("/health", summary="Health check status")
def health_check():
    """Returns service health status."""
    logger.debug("Health check ping received.")
    return {"status": "ok", "service": "IntelliDesk"}


@app.post(
    "/ask",
    response_model=AnswerResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a support question",
)
def ask_question(request: QuestionRequest):
    """
    Accepts an employee support question, retrieves relevant knowledge-base
    chunks via FAISS, and returns a grounded answer from the LLM.
    """
    question_text = request.question.strip()
    if not question_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty or whitespaces only.",
        )

    logger.info(f"API: Processing /ask request: {question_text!r}")
    start_time = time.time()

    try:
        answer = run_pipeline(question_text)
        elapsed_time = time.time() - start_time
        logger.info(
            f"API: Question resolved in {elapsed_time:.3f}s. Returning response."
        )
        return AnswerResponse(question=question_text, answer=answer)
    except FileNotFoundError as fnf:
        logger.error(f"RAG files missing at startup: {fnf}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System is not fully initialized. Ingestion/indexing has not been run.",
        )
    except Exception as exc:
        logger.error(f"Error handling /ask endpoint request: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error resolving support question.",
        )
