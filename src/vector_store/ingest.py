import logging
from pathlib import Path
from typing import List, Dict
from src.config.config import settings

logger = logging.getLogger(__name__)


def load_documents(kb_dir: Path) -> List[Dict]:
    """
    Read every .txt file in kb_dir and return a list of document dicts.
    Each dict: {"filename": str, "text": str}
    """
    documents = []
    if not kb_dir.exists():
        logger.warning(f"Knowledge base directory does not exist: {kb_dir.resolve()}")
        return documents

    for txt_file in sorted(kb_dir.glob("*.txt")):
        try:
            text = txt_file.read_text(encoding="utf-8").strip()
            if text:
                documents.append({"filename": txt_file.name, "text": text})
                logger.debug(
                    f"Successfully loaded document: {txt_file.name} ({len(text)} chars)"
                )
        except Exception as exc:
            logger.error(
                f"Failed to read file {txt_file.resolve()} (UTF-8): {exc}",
                exc_info=True,
            )

    logger.info(f"Loaded {len(documents)} documents from {kb_dir}")
    return documents


def chunk_text(text: str, chunk_size: int = settings.CHUNK_SIZE_WORDS) -> List[str]:
    """
    Split text into chunks of approximately `chunk_size` words.
    Splitting on word boundaries avoids cutting mid-sentence harshly.
    """
    if not text.strip():
        return []
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks


def ingest(kb_dir: Path = settings.KNOWLEDGE_BASE_DIR) -> List[Dict]:
    """
    Full ingestion pipeline:
    1. Load all .txt documents from the configured knowledge base directory.
    2. Chunk each document.
    3. Return a flat list of chunk dicts with source metadata.

    Returns:
        List of dicts with keys: "text" (str), "source" (str), "chunk_id" (int)
    """
    logger.info(f"Starting document ingestion from: {kb_dir}")
    try:
        documents = load_documents(kb_dir)
        all_chunks: List[Dict] = []

        chunk_size = settings.CHUNK_SIZE_WORDS
        for doc in documents:
            chunks = chunk_text(doc["text"], chunk_size)
            for idx, chunk in enumerate(chunks):
                all_chunks.append(
                    {
                        "text": chunk,
                        "source": doc["filename"],
                        "chunk_id": idx,
                    }
                )

        logger.info(f"Finished ingestion. Produced {len(all_chunks)} chunks total.")
        return all_chunks
    except Exception as exc:
        logger.error(f"Error during ingestion pipeline: {exc}", exc_info=True)
        return []


if __name__ == "__main__":
    from src.utils.logger import setup_logging

    setup_logging()
    chunks = ingest()
    logger.info(f"Sample ingestion finished. Chunks produced: {len(chunks)}")
