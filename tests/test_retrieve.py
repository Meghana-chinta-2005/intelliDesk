from unittest.mock import MagicMock
import numpy as np
from src.vector_store.retrieve import retrieve


def test_retrieve_under_threshold():
    """retrieve should return chunks that are under the distance threshold."""
    # Mock model
    model = MagicMock()
    model.encode.return_value = np.zeros((1, 384))

    # Mock index.search to return distances and indices
    index = MagicMock()
    index.search.return_value = (np.array([[0.5, 0.9]]), np.array([[0, 1]]))

    chunks = [
        {"text": "Chunk 1 text", "source": "doc1.txt", "chunk_id": 0},
        {"text": "Chunk 2 text", "source": "doc2.txt", "chunk_id": 1},
    ]

    results = retrieve("query", index, chunks, model, top_k=2, threshold=0.8)
    assert len(results) == 1
    assert results[0]["source"] == "doc1.txt"
    assert results[0]["distance"] == 0.5


def test_retrieve_empty_when_over_threshold():
    """retrieve should filter out chunks that exceed the distance threshold."""
    model = MagicMock()
    model.encode.return_value = np.zeros((1, 384))

    index = MagicMock()
    index.search.return_value = (np.array([[0.85]]), np.array([[0]]))

    chunks = [{"text": "Chunk 1 text", "source": "doc1.txt", "chunk_id": 0}]

    results = retrieve("query", index, chunks, model, top_k=1, threshold=0.8)
    assert len(results) == 0


def test_retrieve_handles_faiss_out_of_bounds():
    """retrieve should ignore index -1 returned by FAISS when fewer items than top_k exist."""
    model = MagicMock()
    model.encode.return_value = np.zeros((1, 384))

    index = MagicMock()
    index.search.return_value = (
        np.array([[0.3, 0.4]]),
        np.array([[0, -1]]),
    )

    chunks = [{"text": "Chunk 1 text", "source": "doc1.txt", "chunk_id": 0}]

    results = retrieve("query", index, chunks, model, top_k=2, threshold=0.8)
    assert len(results) == 1
    assert results[0]["source"] == "doc1.txt"
