import logging
import pickle
from pathlib import Path
from typing import List, Dict

# pyrefly: ignore [missing-import]
import faiss
import numpy as np

# pyrefly: ignore [missing-import]
from sentence_transformers import SentenceTransformer

from src.config.config import settings

logger = logging.getLogger(__name__)


def get_embeddings(texts: List[str], model: SentenceTransformer) -> np.ndarray:
    """Return L2-normalised embeddings for a list of text strings."""
    try:
        embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        faiss.normalize_L2(embeddings)
        return embeddings
    except Exception as exc:
        logger.error(
            f"Error generating embeddings for {len(texts)} texts: {exc}",
            exc_info=True,
        )
        raise


def build_and_save(
    chunks: List[Dict],
    index_path: Path = settings.INDEX_PATH,
    chunks_path: Path = settings.CHUNKS_PATH,
) -> None:
    """
    Embed all chunks, build a FAISS IndexFlatL2, and persist index + metadata.
    Args:
        chunks: List of dicts with keys 'text', 'source', 'chunk_id'.
        index_path: Path to write the FAISS index.
        chunks_path: Path to write the chunks pickle metadata.
    """
    if not chunks:
        logger.warning("No chunks provided to build and save.")
        return

    logger.info(
        f"Embedding {len(chunks)} chunks with model '{settings.EMBEDDING_MODEL_NAME}'..."
    )
    try:
        model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        texts = [c["text"] for c in chunks]

        embeddings = get_embeddings(texts, model)

        dim = embeddings.shape[1]
        logger.info(f"Creating FAISS index FlatL2 with dimension size: {dim}...")
        index = faiss.IndexFlatL2(dim)
        index.add(embeddings)

        # Ensure parent directories exist
        index_path.parent.mkdir(parents=True, exist_ok=True)
        chunks_path.parent.mkdir(parents=True, exist_ok=True)

        faiss.write_index(index, str(index_path))
        with open(chunks_path, "wb") as f:
            pickle.dump(chunks, f)

        logger.info(f"Saved FAISS index successfully -> {index_path}")
        logger.info(f"Saved chunk metadata successfully -> {chunks_path}")
    except Exception as exc:
        logger.error(f"Failed to build or save FAISS store: {exc}", exc_info=True)
        raise


def load_store(
    index_path: Path = settings.INDEX_PATH,
    chunks_path: Path = settings.CHUNKS_PATH,
):
    """
    Load the persisted FAISS index and chunk metadata from disk.
    Returns:
        (index, chunks, model)
    Raises:
        FileNotFoundError if the index has not been built yet.
    """
    if not index_path.exists() or not chunks_path.exists():
        msg = (
            f"FAISS files not found at index_path={index_path} or chunks_path={chunks_path}. "
            "Please run the indexing module first to build it."
        )
        logger.error(msg)
        raise FileNotFoundError(msg)

    try:
        logger.info(f"Loading FAISS index from {index_path}...")
        index = faiss.read_index(str(index_path))

        logger.info(f"Loading chunk metadata from {chunks_path}...")
        with open(chunks_path, "rb") as f:
            chunks = pickle.load(f)

        logger.info(
            f"Initializing sentence transformer: {settings.EMBEDDING_MODEL_NAME}..."
        )
        model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)

        return index, chunks, model
    except Exception as exc:
        logger.error(f"Failed to load FAISS index / store: {exc}", exc_info=True)
        raise


if __name__ == "__main__":
    from src.utils.logger import setup_logging
    from src.vector_store.ingest import ingest

    setup_logging()
    logger.info("Running local FAISS build and save...")
    try:
        chunks = ingest()
        build_and_save(chunks)
        logger.info("Local FAISS build completed successfully.")
    except Exception as e:
        logger.error(f"Build failed: {e}")
