"""
src/embed_store.py
Embeds document chunks using sentence-transformers (all-MiniLM-L6-v2),
builds a FAISS IndexFlatL2, and persists both the index and chunk
metadata to disk so ingestion only runs once.
"""

import pickle
from pathlib import Path
from typing import List, Dict

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"
INDEX_PATH = Path(__file__).parent.parent / "faiss_index.bin"
CHUNKS_PATH = Path(__file__).parent.parent / "chunks.pkl"


def get_embeddings(texts: List[str], model: SentenceTransformer) -> np.ndarray:
    """Return L2-normalised embeddings for a list of text strings."""
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    # Normalise so that L2 distance ≈ cosine similarity (optional but consistent)
    faiss.normalize_L2(embeddings)
    return embeddings


def build_and_save(chunks: List[Dict]) -> None:
    """
    Embed all chunks, build a FAISS IndexFlatL2, and persist index + metadata.
    Args:
        chunks: List of dicts with keys 'text', 'source', 'chunk_id'.
    """
    model = SentenceTransformer(MODEL_NAME)
    texts = [c["text"] for c in chunks]

    print(f"Embedding {len(texts)} chunks with '{MODEL_NAME}'…")
    embeddings = get_embeddings(texts, model)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    faiss.write_index(index, str(INDEX_PATH))
    with open(CHUNKS_PATH, "wb") as f:
        pickle.dump(chunks, f)

    print(f"Saved FAISS index → {INDEX_PATH}")
    print(f"Saved chunk metadata → {CHUNKS_PATH}")


def load_store():
    """
    Load the persisted FAISS index and chunk metadata from disk.
    Returns:
        (index, chunks, model)
    Raises:
        FileNotFoundError if the index has not been built yet.
    """
    if not INDEX_PATH.exists() or not CHUNKS_PATH.exists():
        raise FileNotFoundError(
            "FAISS index not found. Run `python -m src.embed_store` to build it first."
        )

    index = faiss.read_index(str(INDEX_PATH))
    with open(CHUNKS_PATH, "rb") as f:
        chunks = pickle.load(f)
    model = SentenceTransformer(MODEL_NAME)
    return index, chunks, model


if __name__ == "__main__":
    from src.ingest import ingest

    chunks = ingest()
    build_and_save(chunks)
