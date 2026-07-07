"""
IntelliDesk - RAG-based AI Support Ticket Resolver
FastAPI Backend Entry Point
"""

import uvicorn
from src.config.config import settings
from src.api.endpoints import app  # noqa: F401

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
    )
