"""
src/pipeline.py
Orchestrates the end-to-end RAG pipeline:
  1. Load (or lazy-init) the FAISS index and embedding model.
  2. Retrieve relevant chunks for the query.
  3. Generate a grounded answer via the Groq LLM.

The index and model are loaded once at module import time (singleton pattern)
so repeated API calls do not reload them on every request.
"""

import logging
from typing import List, Dict

from src.embed_store import load_store
from src.retrieve import retrieve
from src.generate import generate

logger = logging.getLogger(__name__)

# ── Singleton: load once, reuse across all requests ───────────────────────────
_index = None
_chunks: List[Dict] = []
_model = None


def _ensure_loaded():
    global _index, _chunks, _model
    if _index is None:
        logger.info("Loading FAISS index and embedding model…")
        _index, _chunks, _model = load_store()
        logger.info(f"Index loaded with {_index.ntotal} vectors.")


def run_pipeline(question: str) -> str:
    """
    Full RAG pipeline for a single question.
    Returns the LLM-generated answer string.
    """
    _ensure_loaded()

    # Step 1: Retrieve
    relevant_chunks = retrieve(question, _index, _chunks, _model)
    logger.info(
        f"Retrieved {len(relevant_chunks)} chunk(s) for question: {question!r}"
    )

    # Step 2: Generate
    answer = generate(question, relevant_chunks)
    return answer
