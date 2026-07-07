import logging
from typing import List, Dict

from src.vector_store.embed_store import load_store
from src.vector_store.retrieve import retrieve
from src.services.generate import generate

logger = logging.getLogger(__name__)

# --- Singleton: load once, reuse across all API requests ---
_index = None
_chunks: List[Dict] = []
_model = None


def _ensure_loaded():
    """Lazy-load the FAISS index and embedding model if not loaded yet."""
    global _index, _chunks, _model
    if _index is None:
        logger.info(
            "First request: Initializing FAISS store and sentence-transformer model..."
        )
        try:
            _index, _chunks, _model = load_store()
            logger.info(
                f"FAISS store successfully loaded with {_index.ntotal} vectors."
            )
        except Exception as exc:
            logger.critical(
                f"Failed to initialize core RAG resources: {exc}", exc_info=True
            )
            raise


def run_pipeline(question: str) -> str:
    """
    Full RAG pipeline execution for a single employee question.
    Returns the LLM-generated grounded answer string.
    """
    logger.info(f"Running pipeline for question: {question!r}")
    try:
        # Step 0: Ensure FAISS index & models are loaded
        _ensure_loaded()

        # Step 1: Retrieve context chunks
        relevant_chunks = retrieve(question, _index, _chunks, _model)
        logger.info(
            f"Retrieved {len(relevant_chunks)} context chunk(s) below distance threshold."
        )

        # Step 2: Generate response using LLM
        answer = generate(question, relevant_chunks)
        return answer
    except Exception as exc:
        logger.error(
            f"RAG pipeline execution failed for question {question!r}: {exc}",
            exc_info=True,
        )
        raise
