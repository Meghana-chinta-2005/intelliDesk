import os
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Resolve root directory of the project
ROOT_DIR = Path(__file__).parent.parent.parent.resolve()

# Load env variables from .env
load_dotenv(dotenv_path=ROOT_DIR / ".env")


class Settings(BaseModel):
    # API Configurations
    API_HOST: str = Field(default=os.getenv("API_HOST", "0.0.0.0"))
    API_PORT: int = Field(default=int(os.getenv("API_PORT", "8000")))

    # LLM Configurations
    GROQ_API_KEY: str = Field(default=os.getenv("GROQ_API_KEY", ""))
    LLM_MODEL: str = Field(default=os.getenv("LLM_MODEL", "llama-3.1-8b-instant"))
    LLM_TEMPERATURE: float = Field(default=float(os.getenv("LLM_TEMPERATURE", "0.2")))
    LLM_MAX_TOKENS: int = Field(default=int(os.getenv("LLM_MAX_TOKENS", "512")))

    # RAG / Vector Store Configurations
    EMBEDDING_MODEL_NAME: str = Field(
        default=os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
    )
    KNOWLEDGE_BASE_DIR: Path = Field(
        default=Path(
            os.getenv("KNOWLEDGE_BASE_DIR", str(ROOT_DIR / "data" / "knowledge_base"))
        )
    )
    CHUNK_SIZE_WORDS: int = Field(default=int(os.getenv("CHUNK_SIZE_WORDS", "200")))
    TOP_K: int = Field(default=int(os.getenv("TOP_K", "3")))
    DISTANCE_THRESHOLD: float = Field(
        default=float(os.getenv("DISTANCE_THRESHOLD", "0.8"))
    )

    # Storage Paths
    INDEX_PATH: Path = Field(
        default=Path(os.getenv("INDEX_PATH", str(ROOT_DIR / "faiss_index.bin")))
    )
    CHUNKS_PATH: Path = Field(
        default=Path(os.getenv("CHUNKS_PATH", str(ROOT_DIR / "chunks.pkl")))
    )

    # Logging
    LOG_LEVEL: str = Field(default=os.getenv("LOG_LEVEL", "INFO"))
    LOG_FILE: str = Field(default=os.getenv("LOG_FILE", "app.log"))

    # Frontend / Connection settings
    API_URL: str = Field(default=os.getenv("API_URL", "http://localhost:8000"))


settings = Settings()
