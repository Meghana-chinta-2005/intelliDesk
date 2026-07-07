import logging
from typing import List, Dict
import faiss
from src.config.config import settings

logger = logging.getLogger(__name__)


def retrieve(
    query: str,
    index: faiss.Index,
    chunks: List[Dict],
    model,
    top_k: int = settings.TOP_K,
    threshold: float = settings.DISTANCE_THRESHOLD,
) -> List[Dict]:
    """
    Embed the query and return the top_k closest chunks whose L2 distance
    is below `threshold`. Returns an empty list when nothing is relevant.

    Returns:
        List of chunk dicts (keys: 'text', 'source', 'chunk_id', 'distance').
    """
    if not query.strip():
        logger.warning("Empty query received for retrieval.")
        return []

    try:
        logger.debug(f"Retrieving for query: {query!r}")
        # Encode and normalize query vector
        query_vec = model.encode([query], convert_to_numpy=True).astype("float32")
        faiss.normalize_L2(query_vec)

        # Search index
        distances, indices = index.search(query_vec, top_k)
        results = []

        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                # FAISS returns -1 when the index has fewer than top_k items
                continue

            if idx >= len(chunks):
                logger.error(
                    f"Index out of range: FAISS index {idx} but chunks size is {len(chunks)}."
                )
                continue

            if dist < threshold:
                chunk = dict(chunks[idx])
                chunk["distance"] = float(dist)
                results.append(chunk)
                logger.debug(
                    f"Matched chunk source: {chunk['source']} with distance: {dist:.4f}"
                )
            else:
                logger.debug(
                    f"Filtered out chunk from {chunks[idx]['source']} due to distance {dist:.4f} >= threshold {threshold}"
                )

        logger.info(
            f"Query: {query!r} -> Retrieved {len(results)} chunks below threshold {threshold}"
        )
        return results

    except Exception as exc:
        logger.error(
            f"Error during semantic retrieval for query {query!r}: {exc}",
            exc_info=True,
        )
        return []


if __name__ == "__main__":
    from src.utils.logger import setup_logging
    from src.vector_store.embed_store import load_store

    setup_logging()
    logger.info("Running local retrieve test...")
    try:
        index, chunks, model = load_store()
        query = "How do I reset my VPN password?"
        results = retrieve(query, index, chunks, model)
        for r in results:
            logger.info(
                f"[{r['source']} | distance={r['distance']:.4f}] {r['text'][:100]}..."
            )
    except Exception as e:
        logger.error(f"Retrieve test failed: {e}")
