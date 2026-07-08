import logging
from typing import List, Dict, Any, Optional
import numpy as np

from src.config.config import settings
from src.vector_store.embed_store import get_chroma_client, get_collection, get_embedding_model

logger = logging.getLogger(__name__)


def retrieve(
    *args,
    user_id: Optional[int] = None,
    query: Optional[str] = None,
    top_k: int = settings.TOP_K,
    threshold: float = settings.DISTANCE_THRESHOLD,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Dual-signature semantic retrieval supporting both positional and keyword arguments:
    
    1. Multi-Tenant ChromaDB Signature:
       retrieve(user_id=1, query="text") or retrieve(1, "text")
       
    2. Legacy FAISS Signature:
       retrieve("text", index, chunks, model)
    """
    
    # 1. Detect Signature Type
    is_legacy = False
    
    if len(args) >= 1:
        first_arg = args[0]
        if isinstance(first_arg, str):
            is_legacy = True

    # 2. Case A: Legacy FAISS Retrieval
    if is_legacy:
        legacy_query = args[0]
        index = args[1] if len(args) > 1 else None
        chunks = args[2] if len(args) > 2 else None
        model = args[3] if len(args) > 3 else None
        legacy_top_k = args[4] if len(args) > 4 else top_k
        legacy_threshold = args[5] if len(args) > 5 else threshold
        
        logger.info(f"Retrieve: Running legacy FAISS query path for {legacy_query!r}")
        if not legacy_query.strip():
            return []
            
        try:
            # Encode and normalize query vector
            query_vec = model.encode([legacy_query], convert_to_numpy=True).astype("float32")
            
            # L2 normalization
            norm = np.linalg.norm(query_vec)
            if norm > 0:
                query_vec = query_vec / norm
                
            # Search index
            distances, indices = index.search(query_vec, legacy_top_k)
            results = []
            
            for dist, idx in zip(distances[0], indices[0]):
                if idx == -1:
                    continue
                if idx >= len(chunks):
                    continue
                if dist < legacy_threshold:
                    chunk = dict(chunks[idx])
                    chunk["distance"] = float(dist)
                    results.append(chunk)
            return results
        except Exception as e:
            logger.error(f"Retrieve: Legacy query failed: {e}", exc_info=True)
            return []

    # 3. Case B: New ChromaDB Retrieval
    # Resolve parameters from positional args or kwargs
    resolved_user_id = user_id
    resolved_query = query
    resolved_top_k = top_k
    resolved_threshold = threshold

    if len(args) >= 1:
        resolved_user_id = args[0]
    if len(args) >= 2:
        resolved_query = args[1]
    if len(args) >= 3:
        resolved_top_k = args[2]
    if len(args) >= 4:
        resolved_threshold = args[3]

    if resolved_query is None or not resolved_query.strip():
        logger.warning("Empty query received for retrieval.")
        return []

    try:
        logger.info(f"Retrieving chunks for user_id={resolved_user_id}, query={resolved_query!r}")
        
        # 1. Embed query text
        model = get_embedding_model()
        query_vec = model.encode([resolved_query], convert_to_numpy=True).tolist()[0]

        # 2. Get ChromaDB collection
        client = get_chroma_client()
        collection = get_collection(client)

        # 3. Query with user_id constraint
        results = collection.query(
            query_embeddings=[query_vec],
            n_results=resolved_top_k,
            where={"user_id": resolved_user_id}
        )

        retrieved_chunks = []
        if not results or "ids" not in results or not results["ids"] or not results["ids"][0]:
            logger.info("No matching vector embeddings found in collection.")
            return []

        ids = results["ids"][0]
        distances = results["distances"][0]
        metadatas = results["metadatas"][0]
        documents = results["documents"][0]

        for i in range(len(ids)):
            dist = float(distances[i])
            meta = metadatas[i]
            text = documents[i]

            # 4. Filter by semantic L2 threshold
            if dist < resolved_threshold:
                retrieved_chunks.append({
                    "text": text,
                    "source": meta.get("source", "unknown"),
                    "page": meta.get("page", "1"),
                    "distance": dist
                })
                logger.debug(
                    f"Match chunk source: {meta.get('source')} | page: {meta.get('page')} | distance: {dist:.4f}"
                )
            else:
                logger.debug(
                    f"Filtered out chunk from {meta.get('source')} page {meta.get('page')} due to distance {dist:.4f} >= threshold {resolved_threshold}"
                )

        logger.info(
            f"Query: {resolved_query!r} -> Retrieved {len(retrieved_chunks)} chunks for user_id={resolved_user_id} below threshold {resolved_threshold}"
        )
        return retrieved_chunks

    except Exception as exc:
        logger.error(
            f"Error during semantic retrieval for query {resolved_query!r}: {exc}",
            exc_info=True,
        )
        return []
