"""
src/ingest.py
Loads all .txt documents from the knowledge base directory,
splits them into ~200-word chunks, and tags each chunk with
its source filename.
"""

import os
from pathlib import Path
from typing import List, Dict

KNOWLEDGE_BASE_DIR = Path(__file__).parent.parent / "data" / "knowledge_base"
CHUNK_SIZE_WORDS = 200


def load_documents(kb_dir: Path = KNOWLEDGE_BASE_DIR) -> List[Dict]:
    """
    Read every .txt file in kb_dir and return a list of document dicts.
    Each dict: {"filename": str, "text": str}
    """
    documents = []
    for txt_file in sorted(kb_dir.glob("*.txt")):
        text = txt_file.read_text(encoding="utf-8").strip()
        if text:
            documents.append({"filename": txt_file.name, "text": text})
    return documents


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE_WORDS) -> List[str]:
    """
    Split text into chunks of approximately `chunk_size` words.
    Splitting on word boundaries avoids cutting mid-sentence harshly.
    """
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks


def ingest(kb_dir: Path = KNOWLEDGE_BASE_DIR) -> List[Dict]:
    """
    Full ingestion pipeline:
    1. Load all .txt documents.
    2. Chunk each document.
    3. Return a flat list of chunk dicts with source metadata.

    Returns:
        List of dicts with keys: "text" (str), "source" (str), "chunk_id" (int)
    """
    documents = load_documents(kb_dir)
    all_chunks: List[Dict] = []

    for doc in documents:
        chunks = chunk_text(doc["text"])
        for idx, chunk in enumerate(chunks):
            all_chunks.append(
                {
                    "text": chunk,
                    "source": doc["filename"],
                    "chunk_id": idx,
                }
            )

    return all_chunks


if __name__ == "__main__":
    chunks = ingest()
    print(f"Total chunks produced: {len(chunks)}")
    for c in chunks[:3]:
        print(f"  [{c['source']} | chunk {c['chunk_id']}] {c['text'][:80]}…")
