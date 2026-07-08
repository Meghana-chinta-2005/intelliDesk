import logging
from pathlib import Path
from typing import List, Dict
import pdfplumber
import fitz  # PyMuPDF
import docx
import pandas as pd

from src.config.config import settings

logger = logging.getLogger(__name__)

# File validation constraints from configuration
ALLOWED_EXTENSIONS = set(settings.ALLOWED_EXTENSIONS)
MAX_FILE_SIZE_MB = settings.MAX_FILE_SIZE_MB


def validate_file(filename: str, file_size_bytes: int) -> None:
    """
    Validate that the file meets extension and size requirements.
    Raises ValueError if validation fails.
    """
    path = Path(filename)
    ext = path.suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file format '{ext}'. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    file_size_mb = file_size_bytes / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(
            f"File size exceeds the limit of {MAX_FILE_SIZE_MB}MB (size: {file_size_mb:.2f}MB)"
        )


def parse_pdf(file_path: Path) -> List[Dict]:
    """Parse PDF file page by page using pdfplumber with a PyMuPDF fallback."""
    pages = []
    try:
        logger.info(f"Parsing PDF with pdfplumber: {file_path}")
        with pdfplumber.open(file_path) as pdf:
            for idx, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text and text.strip():
                    pages.append({"text": text.strip(), "page": idx})
    except Exception as e:
        logger.warning(f"pdfplumber failed for {file_path}, falling back to PyMuPDF (fitz): {e}")
        try:
            doc = fitz.open(file_path)
            for idx in range(len(doc)):
                page = doc[idx]
                text = page.get_text()
                if text and text.strip():
                    # Only insert if we don't have this page yet
                    if not any(p["page"] == idx + 1 for p in pages):
                        pages.append({"text": text.strip(), "page": idx + 1})
        except Exception as fitz_err:
            logger.error(f"PyMuPDF parsing also failed for {file_path}: {fitz_err}")
            raise ValueError(f"Could not extract text from PDF file: {fitz_err}")

    if not pages:
        raise ValueError("PDF file contains no indexable text.")
    return pages


def parse_docx(file_path: Path) -> List[Dict]:
    """Parse Word document, grouping paragraphs into simulated logical pages."""
    try:
        logger.info(f"Parsing DOCX with python-docx: {file_path}")
        doc = docx.Document(file_path)
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

        pages = []
        current_page_text = []
        current_char_count = 0
        page_idx = 1

        for p in paragraphs:
            current_page_text.append(p)
            current_char_count += len(p)
            if current_char_count >= 1200:
                pages.append({"text": "\n".join(current_page_text), "page": page_idx})
                current_page_text = []
                current_char_count = 0
                page_idx += 1

        if current_page_text:
            pages.append({"text": "\n".join(current_page_text), "page": page_idx})

        if not pages:
            raise ValueError("DOCX document contains no indexable text.")
        return pages
    except Exception as e:
        logger.error(f"Error parsing DOCX file {file_path}: {e}", exc_info=True)
        raise ValueError(f"Could not extract text from DOCX file: {e}")


def parse_xlsx(file_path: Path) -> List[Dict]:
    """Parse Excel spreadsheet sheets using pandas, formatting rows as structured text lines."""
    try:
        logger.info(f"Parsing XLSX with pandas: {file_path}")
        excel_file = pd.ExcelFile(file_path)
        pages = []

        for sheet_name in excel_file.sheet_names:
            df = excel_file.parse(sheet_name)
            df = df.fillna("")
            headers = [str(col).strip() for col in df.columns]

            lines = []
            for index, row in df.iterrows():
                row_items = []
                for h in headers:
                    val = str(row[h]).strip()
                    if val:
                        row_items.append(f"{h}: {val}")
                if row_items:
                    lines.append(f"Row {index+1}: {', '.join(row_items)}")

            if lines:
                pages.append({
                    "text": f"Sheet: {sheet_name}\n" + "\n".join(lines),
                    "page": sheet_name  # In Excel, the sheet name serves as the page reference
                })

        if not pages:
            raise ValueError("Excel file contains no sheets or data.")
        return pages
    except Exception as e:
        logger.error(f"Error parsing XLSX file {file_path}: {e}", exc_info=True)
        raise ValueError(f"Could not extract text from XLSX file: {e}")


def parse_txt(file_path: Path) -> List[Dict]:
    """Parse UTF-8 plain text file."""
    try:
        logger.info(f"Parsing TXT file: {file_path}")
        text = file_path.read_text(encoding="utf-8", errors="ignore").strip()
        if not text:
            raise ValueError("TXT file is empty.")
        return [{"text": text, "page": 1}]
    except Exception as e:
        logger.error(f"Error parsing TXT file {file_path}: {e}", exc_info=True)
        raise ValueError(f"Could not read TXT file: {e}")


def chunk_document(parsed_pages: List[Dict], chunk_size: int = settings.CHUNK_SIZE_CHAR, chunk_overlap: int = settings.CHUNK_OVERLAP_CHAR) -> List[Dict]:
    """
    Split parsed pages using a character-based sliding window.
    Ensures structural chunks keep a reference to their source page/sheet.
    """
    chunks = []
    for page_data in parsed_pages:
        text = page_data["text"]
        page_ref = page_data["page"]

        if len(text) <= chunk_size:
            chunks.append({
                "text": text,
                "page": page_ref
            })
            continue

        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk_text = text[start:end]
            # Verify the chunk contains content
            if chunk_text.strip():
                chunks.append({
                    "text": chunk_text.strip(),
                    "page": page_ref
                })

            start += chunk_size - chunk_overlap
            # Exit loop if overlap prevents forward progress
            if chunk_size <= chunk_overlap:
                break
    return chunks


def chunk_text(text: str, chunk_size: int = 200) -> List[str]:
    """
    Split text into word-based chunks for backward compatibility with testing suite.
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


def parse_and_chunk_file(file_path: Path) -> List[Dict]:
    """
    Utility router that takes a local file path, validates it, selects the correct parser,
    and returns a list of text chunks with page coordinates.
    """
    # Quick sanity size verification before starting full parse
    validate_file(file_path.name, file_path.stat().st_size)

    ext = file_path.suffix.lower()
    if ext == ".pdf":
        pages = parse_pdf(file_path)
    elif ext == ".docx":
        pages = parse_docx(file_path)
    elif ext == ".xlsx":
        pages = parse_xlsx(file_path)
    elif ext == ".txt":
        pages = parse_txt(file_path)
    else:
        raise ValueError(f"Unhandled file extension '{ext}'")

    return chunk_document(pages)


def load_documents(kb_dir: Path) -> List[Dict]:
    """
    Read every .txt file in kb_dir and return a list of document dicts.
    Required for compatibility with baseline testing configurations.
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


def ingest(kb_dir: Path = settings.KNOWLEDGE_BASE_DIR) -> List[Dict]:
    """
    Ingest all files in a configured knowledge base folder.
    Maintains compatibility with baseline CLI indexing commands.
    """
    logger.info(f"Starting legacy folder ingestion from: {kb_dir}")
    if not kb_dir.exists():
        logger.warning(f"Directory {kb_dir} does not exist.")
        return []

    all_chunks = []
    for file_path in sorted(kb_dir.iterdir()):
        if file_path.suffix.lower() == ".txt":
            try:
                # Use legacy word-based chunking to align with evaluation and unit tests
                text = file_path.read_text(encoding="utf-8", errors="ignore").strip()
                chunks_list = chunk_text(text, chunk_size=200)
                for idx, chunk_text_content in enumerate(chunks_list):
                    all_chunks.append({
                        "text": chunk_text_content,
                        "source": file_path.name,
                        "page": 1,
                        "chunk_id": idx
                    })
            except Exception as e:
                logger.error(f"Failed to ingest legacy text file {file_path.name}: {e}")
        elif file_path.suffix.lower() in ALLOWED_EXTENSIONS:
            try:
                chunks = parse_and_chunk_file(file_path)
                for idx, chunk in enumerate(chunks):
                    all_chunks.append({
                        "text": chunk["text"],
                        "source": file_path.name,
                        "page": chunk["page"],
                        "chunk_id": idx
                    })
            except Exception as e:
                logger.error(f"Failed to ingest file {file_path.name}: {e}")

    logger.info(f"Legacy folder ingestion produced {len(all_chunks)} chunks.")
    return all_chunks


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Testing document ingestion module...")
    # Create sample TXT file in knowledge base directory for local manual validation
    sample_dir = settings.KNOWLEDGE_BASE_DIR
    sample_dir.mkdir(parents=True, exist_ok=True)
    sample_file = sample_dir / "sample_doc.txt"
    sample_file.write_text("This is a sample document for testing multi-format parser flow.\nVPN access instructions...", encoding="utf-8")
    
    chunks = ingest(sample_dir)
    logger.info(f"Sample chunks count: {len(chunks)}")
    for c in chunks[:2]:
        logger.info(f"Chunk from {c['source']} page {c['page']}: {c['text']}")
