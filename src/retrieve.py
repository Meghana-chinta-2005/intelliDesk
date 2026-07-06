"""
src/retrieve.py
Given a natural-language query, embed it and search the FAISS index.
Returns the top_k most relevant chunks filtered by a distance threshold
(the hallucination guard — queries with no good match return an empty list).

Design Decision — Distance Threshold:
  - We use L2 distance on normalised vectors (≈ 2*(1 - cosine_similarity)).
  - Threshold = 0.8 was chosen empirically:
      * Distance < 0.8  → chunk is meaningfully related to the query
      * Distance ≥ 0.8  → treat as "no relevant context found"
  - This is conservative; increase to ~1.0 to allow fuzzier matches,
    decrease to ~0.6 to be stricter.
"""

from typing import List, Dict
import numpy as np
import faiss

TOP_K = 3
DISTANCE_THRESHOLD = 0.8  # L2 distance on normalised embeddings


def retrieve(
    query: str,
    index: faiss.Index,
    chunks: List[Dict],
    model,
    top_k: int = TOP_K,
    threshold: float = DISTANCE_THRESHOLD,
) -> List[Dict]:
    """
    Embed the query and return the top_k closest chunks whose L2 distance
    is below `threshold`. Returns an empty list when nothing is relevant.

    Returns:
        List of chunk dicts (keys: 'text', 'source', 'chunk_id', 'distance').
    """
    query_vec = model.encode([query], convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(query_vec)

    distances, indices = index.search(query_vec, top_k)
    results = []

    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue  # FAISS returns -1 when the index has fewer than top_k items
        if dist < threshold:
            chunk = dict(chunks[idx])
            chunk["distance"] = float(dist)
            results.append(chunk)

    return results


if __name__ == "__main__":
    from src.embed_store import load_store

    index, chunks, model = load_store()
    query = "How do I reset my VPN password?"
    results = retrieve(query, index, chunks, model)
    if results:
        for r in results:
            print(f"[{r['source']} | d={r['distance']:.4f}] {r['text'][:120]}…")
    else:
        print("No relevant results found.")
