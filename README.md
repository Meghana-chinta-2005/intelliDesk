# 🧠 IntelliDesk — RAG-Based AI Support Ticket Resolver

IntelliDesk is an internal AI support assistant that answers employee questions
by retrieving relevant documents from a company knowledge base and generating
a grounded, source-cited answer using an LLM. It never halluccinates — if the
knowledge base doesn't contain an answer, it says so explicitly.

---

## Architecture

```
Employee Question
      │
      ▼
┌─────────────┐    POST /ask     ┌──────────────────────────────────────────────┐
│  Streamlit  │ ──────────────▶  │              FastAPI Backend                 │
│   (app.py)  │ ◀──────────────  │                (main.py)                     │
└─────────────┘    JSON answer   └──────────────────┬───────────────────────────┘
                                                    │
                                                    ▼
                                     ┌──────────────────────────┐
                                     │     src/pipeline.py      │
                                     │  (orchestrates RAG flow) │
                                     └──────┬───────────────────┘
                                            │
                     ┌──────────────────────┼────────────────────────┐
                     ▼                      ▼                        ▼
           ┌──────────────────┐  ┌──────────────────┐   ┌───────────────────┐
           │  src/ingest.py   │  │ src/retrieve.py   │   │  src/generate.py  │
           │  Load & chunk    │  │ FAISS vector      │   │  Groq LLM         │
           │  .txt documents  │  │ similarity search │   │  (grounded only)  │
           └──────────────────┘  └──────────────────┘   └───────────────────┘
                     │                    ▲
                     ▼                    │
           ┌──────────────────┐           │
           │ src/embed_store  │ ──────────┘
           │ sentence-xformers│
           │ FAISS IndexFlatL2│
           └──────────────────┘
                     │
           ┌──────────────────┐
           │ data/knowledge   │
           │ base/ (.txt docs)│
           └──────────────────┘
```

### Key Design Decisions

| Concern | Choice | Reason |
|---|---|---|
| Embeddings | all-MiniLM-L6-v2 | Small, fast, high quality for English |
| Vector Store | FAISS IndexFlatL2 | Simple, no server, great for <100k docs |
| LLM | Groq llama-3.1-8b-instant | Very fast inference, free tier available |
| Hallucination Guard | L2 distance threshold (0.8) | Rejects queries with no good match |
| Chunk size | ~200 words | Balances context richness vs. precision |

---

## Setup

### Prerequisites
- Python 3.11+
- A Groq API key ([get one free](https://console.groq.com))

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/intellidesk-rag.git
cd intellidesk-rag
```

### 2. Create a virtual environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### 5. Build the knowledge base index
```bash
python -m src.embed_store
```
This reads all `.txt` files in `data/knowledge_base/`, embeds them, and saves
`faiss_index.bin` and `chunks.pkl` to the project root.

---

## Running Locally

### Start the FastAPI backend
```bash
uvicorn main:app --reload --port 8000
```

### Start the Streamlit frontend (in a second terminal)
```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## API Reference

### `GET /health`
```bash
curl http://localhost:8000/health
# {"status": "ok", "service": "IntelliDesk"}
```

### `POST /ask`
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I reset my VPN password?"}'
```
Response:
```json
{
  "question": "How do I reset my VPN password?",
  "answer": "To reset your VPN password, visit the IT portal... Sources: vpn_access.txt"
}
```

---

## Running Tests
```bash
pytest tests/ -v
```

---

## Docker

### Build the image
```bash
docker build -t intellidesk:latest .
```

### Run the container
```bash
docker run -p 8000:8000 --env-file .env intellidesk:latest
```

---

## Project Structure

```
IntelliDesk/
├── data/
│   └── knowledge_base/       # Source .txt support documents (18-20 files)
├── src/
│   ├── ingest.py             # Load & chunk documents
│   ├── embed_store.py        # Embed + build/load FAISS index
│   ├── retrieve.py           # Vector similarity search with threshold guard
│   ├── generate.py           # Groq LLM call with grounding prompt
│   └── pipeline.py           # End-to-end RAG orchestrator
├── tests/
│   ├── test_ingest.py        # Ingestion unit tests
│   ├── test_api.py           # FastAPI endpoint tests
│   └── test_retrieval.py     # Retrieval accuracy evaluation
├── .github/
│   └── workflows/ci.yml      # GitHub Actions CI
├── main.py                   # FastAPI app
├── app.py                    # Streamlit UI
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

---

## Contributing
1. Fork the repo
2. Create a feature branch (`git checkout -b feature/my-change`)
3. Commit your changes (`git commit -m 'feat: describe change'`)
4. Push and open a Pull Request

---

*Built with ❤️ using FastAPI · FAISS · sentence-transformers · Groq*