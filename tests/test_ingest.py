"""
tests/test_ingest.py
Unit tests for the ingestion and chunking module.
(Full tests will be added in Phase 10.)
"""

import pytest
from pathlib import Path
from src.ingest import chunk_text, load_documents, ingest


def test_chunk_text_basic():
    """chunk_text should split text into correct-sized word chunks."""
    words = ["word"] * 450
    text = " ".join(words)
    chunks = chunk_text(text, chunk_size=200)
    assert len(chunks) == 3  # 200 + 200 + 50
    assert len(chunks[0].split()) == 200
    assert len(chunks[2].split()) == 50


def test_chunk_text_empty():
    """chunk_text on empty string should return empty list."""
    assert chunk_text("") == []


def test_chunk_text_small():
    """chunk_text on text smaller than chunk_size returns one chunk."""
    text = "This is a short document."
    chunks = chunk_text(text, chunk_size=200)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_load_documents_returns_list(tmp_path):
    """load_documents should return one dict per .txt file."""
    (tmp_path / "doc1.txt").write_text("Hello world document one.")
    (tmp_path / "doc2.txt").write_text("Hello world document two.")
    docs = load_documents(tmp_path)
    assert len(docs) == 2
    filenames = {d["filename"] for d in docs}
    assert "doc1.txt" in filenames
    assert "doc2.txt" in filenames


def test_ingest_produces_chunks(tmp_path):
    """ingest should return a non-empty list of chunk dicts."""
    words = " ".join(["word"] * 400)
    (tmp_path / "sample.txt").write_text(words)
    chunks = ingest(kb_dir=tmp_path)
    assert len(chunks) == 2
    for c in chunks:
        assert "text" in c
        assert "source" in c
        assert "chunk_id" in c
