import logging
from typing import List, Dict, Any

import chromadb
from sentence_transformers import SentenceTransformer

from src.config.config import settings, ROOT_DIR

logger = logging.getLogger(__name__)

# Singleton wrapper for embedding model to avoid loading it repeatedly
_embedding_model = None


def get_embedding_model() -> SentenceTransformer:
    """Lazy-load the SentenceTransformer model in a thread-safe manner."""
    global _embedding_model
    if _embedding_model is None:
        logger.info(f"Loading SentenceTransformer model: {settings.EMBEDDING_MODEL_NAME}...")
        try:
            _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        except Exception as e:
            logger.critical(f"Failed to load embedding model: {e}", exc_info=True)
            raise
    return _embedding_model


def get_chroma_client() -> chromadb.PersistentClient:
    """Returns a thread-safe persistent ChromaDB client."""
    db_path = settings.CHROMADB_DIR
    db_path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(db_path))


def get_collection(client: chromadb.PersistentClient = None):
    """Retrieve or create the document collection configured with L2 distance."""
    if client is None:
        client = get_chroma_client()
    # Using L2 distance to maintain compatibility with our semantic threshold settings
    return client.get_or_create_collection(
        name=settings.CHROMA_COLLECTION_NAME,
        metadata={"hnsw:space": "l2"}
    )


def add_document_chunks(
    user_id: int,
    document_id: int,
    filename: str,
    chunks: List[Dict[str, Any]]
) -> int:
    """
    Generate embeddings for document chunks and index them in ChromaDB.
    Ensures user-level metadata filters are attached for multi-tenant isolation.
    """
    if not chunks:
        logger.warning(f"No chunks to index for document {document_id} ({filename})")
        return 0

    logger.info(f"Indexing {len(chunks)} chunks for doc_id={document_id} user_id={user_id}...")
    model = get_embedding_model()
    
    texts = [chunk["text"] for chunk in chunks]
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True).tolist()

    ids = []
    metadatas = []
    documents = []

    for idx, chunk in enumerate(chunks):
        chunk_text = chunk["text"]
        page_ref = str(chunk["page"])
        
        # Globally unique vector identifier
        chunk_uuid = f"usr_{user_id}_doc_{document_id}_chunk_{idx}"
        ids.append(chunk_uuid)
        
        # Attach strict isolation metadata fields
        metadatas.append({
            "user_id": user_id,
            "document_id": document_id,
            "source": filename,
            "page": page_ref
        })
        documents.append(chunk_text)

    client = get_chroma_client()
    collection = get_collection(client)

    # Perform batch upsert
    collection.add(
        ids=ids,
        embeddings=embeddings,
        metadatas=metadatas,
        documents=documents
    )
    logger.info(f"ChromaDB indexing completed: {len(chunks)} vectors added.")
    return len(chunks)


def delete_document_chunks(document_id: int) -> None:
    """
    Evict all vector embeddings associated with a deleted document.
    """
    logger.info(f"Evicting all ChromaDB vectors for document_id={document_id}...")
    try:
        client = get_chroma_client()
        collection = get_collection(client)
        
        # Query matching document_id in metadata
        collection.delete(where={"document_id": document_id})
        logger.info(f"Successfully evicted vector embeddings for document_id={document_id}")
    except Exception as e:
        logger.error(f"Failed to delete ChromaDB vectors for document_id={document_id}: {e}", exc_info=True)
        raise


def load_store(index_path=None, chunks_path=None):
    """Legacy helper to load FAISS index from disk, used strictly by testing suites."""
    import faiss
    import pickle
    
    idx_p = index_path or ROOT_DIR / "faiss_index.bin"
    chk_p = chunks_path or ROOT_DIR / "chunks.pkl"
    
    logger.info(f"Retrieving legacy FAISS index from {idx_p}...")
    index = faiss.read_index(str(idx_p))
    
    with open(chk_p, "rb") as f:
        chunks = pickle.load(f)
        
    model = get_embedding_model()
    return index, chunks, model
