# 🧠 IntelliDesk — Production RAG-Based AI Support Assistant

IntelliDesk is an enterprise-grade internal AI support assistant that answers employee questions by retrieving relevant documents from a company knowledge base and generating grounded, source-cited answers using an LLM. 

By employing a strict semantic distance threshold guard, IntelliDesk prevents LLM hallucinations. If the knowledge base does not contain the answer, the assistant flags it explicitly rather than generating false information.

---

## 🏗️ Clean System Architecture

IntelliDesk is built with a production-ready clean layered architecture under `src/`:

```
Employee Question
      │
      ▼
┌─────────────┐    POST /ask     ┌──────────────────────────────────────────────┐
│  Streamlit  │ ──────────────▶  │              FastAPI Backend                 │
│   (app.py)  │ ◀──────────────  │            (main.py -> src/api/)             │
└─────────────┘    JSON answer   └──────────────────┬───────────────────────────┘
                                                    │
                                                    ▼
                                     ┌──────────────────────────┐
                                     │  src/services/pipeline   │
                                     │  (orchestrates RAG flow) │
                                     └──────┬───────────────────┘
                                            │
                     ┌──────────────────────┼────────────────────────┐
                     ▼                      ▼                        ▼
           ┌──────────────────┐  ┌──────────────────┐   ┌───────────────────┐
           │ src/vector_store/│  │ src/vector_store/│   │   src/services/   │
           │    ingest.py     │  │   retrieve.py    │   │    generate.py    │
           │  Load & chunk    │  │ FAISS vector     │   │  Groq LLM         │
           │  .txt documents  │  │ similarity search│   │  (grounded only)  │
           └──────────────────┘  └──────────────────┘   └───────────────────┘
                     │                    ▲
                     ▼                    │
           ┌──────────────────┐           │
           │ src/vector_store/│ ──────────┘
           │  embed_store.py  │
           │ sentence-xformers│
           │ FAISS IndexFlatL2│
           └──────────────────┘
                     │
           ┌──────────────────┐
           │ data/knowledge   │
           │ base/ (.txt docs)│
           └──────────────────┘
```

### Modular Repository Structure
```
IntelliDesk/
├── .github/workflows/ci.yml  # Automated CI (formatting, linting, testing)
├── data/knowledge_base/      # Support documents (.txt)
├── src/
│   ├── api/                  # FastAPI routers and routes
│   ├── config/               # Settings & environment variables validation
│   ├── models/               # Pydantic request/response models
│   ├── services/             # LLM orchestration and generation pipeline
│   ├── utils/                # Logging setup
│   └── vector_store/         # Document ingestion, indexing, and retrieval
├── tests/                    # Unit & integration tests
├── .env.example              # Configuration template
├── .gitignore                # Git ignore files
├── app.py                    # Streamlit UI (Frontend)
├── Dockerfile                # Production Docker multi-stage container
├── main.py                   # FastAPI backend launcher (Entrypoint)
└── README.md                 # System documentation
```

---

## ⚙️ Configuration & Environment Variables

IntelliDesk uses a central configuration system (`src/config/config.py`) powered by Pydantic models. You can configure the system by creating a `.env` file in the root directory.

| Variable | Description | Default |
| :--- | :--- | :--- |
| `GROQ_API_KEY` | **[Required]** API Key for Groq Cloud LLM | *None* |
| `API_HOST` | FastAPI host interface address | `0.0.0.0` |
| `API_PORT` | FastAPI network port | `8000` |
| `LLM_MODEL` | Groq LLM model name | `llama-3.1-8b-instant` |
| `LLM_TEMPERATURE` | Generation temperature | `0.2` |
| `LLM_MAX_TOKENS` | Maximum tokens for response | `512` |
| `EMBEDDING_MODEL_NAME`| Sentence Transformer model name | `all-MiniLM-L6-v2` |
| `CHUNK_SIZE_WORDS` | Word limit per text chunk | `200` |
| `TOP_K` | Number of context chunks to retrieve | `3` |
| `DISTANCE_THRESHOLD` | FAISS L2 similarity distance cutoff limit | `0.8` |
| `LOG_LEVEL` | Level of debug log granularity | `INFO` |
| `LOG_FILE` | Log file path | `app.log` |
| `API_URL` | Streamlit target API address | `http://localhost:8000` |

---

## 🚀 Installation & Local Run

### 1. Set Up Environment
Create a virtual environment and install dependencies:
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Credentials
Copy `.env.example` to `.env` and fill in your Groq API key:
```bash
cp .env.example .env
```

### 3. Build the FAISS Vector Store Index
Run the ingestion pipeline to parse documents and compile the semantic index:
```bash
python -m src.vector_store.embed_store
```
This reads all text files in `data/knowledge_base/`, creates embeddings, and outputs:
- `faiss_index.bin` (FAISS database)
- `chunks.pkl` (chunk metadata)

### 4. Run the API Server
Start the FastAPI server:
```bash
python main.py
```

### 5. Run the Streamlit Interface
In a separate terminal, launch the Streamlit frontend:
```bash
streamlit run app.py
```
Access the UI at `http://localhost:8501`.

---

## 🧪 Quality Control & Testing

### Running Tests
Execute the pytest suite (covers ingestion, semantic retrieval, generation mocking, and API routes):
```bash
pytest tests/ -v
```

### Linting and Formatting
IntelliDesk uses `Ruff` to enforce strict formatting and linting.
```bash
# Run lint check
ruff check .

# Run format check
ruff format --check .

# Auto-fix lint problems and format
ruff check --fix . && ruff format .
```

---

## 🛠️ GitHub Actions CI Pipeline

On every push or pull request to the `main` branch, the CI pipeline (`.github/workflows/ci.yml`) executes:
1. **Ruff Linter Check** (`ruff check .`)
2. **Ruff Formatter Check** (`ruff format --check .`)
3. **FAISS Index Build** (`python -m src.vector_store.embed_store`)
4. **Pytest Run** (`pytest tests/ -v`)

---

## 🐳 Docker Deployment

### 1. Build Docker Image
```bash
docker build -t intellidesk:latest .
```

### 2. Run Docker Container
```bash
docker run -p 8000:8000 --env-file .env intellidesk:latest
```
The FastAPI documentation will be available at `http://localhost:8000/docs`.