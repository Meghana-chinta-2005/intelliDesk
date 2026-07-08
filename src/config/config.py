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
    # Character-based sliding window parameters
    CHUNK_SIZE_CHAR: int = Field(default=int(os.getenv("CHUNK_SIZE_CHAR", "800")))
    CHUNK_OVERLAP_CHAR: int = Field(default=int(os.getenv("CHUNK_OVERLAP_CHAR", "100")))
    TOP_K: int = Field(default=int(os.getenv("TOP_K", "5")))
    DISTANCE_THRESHOLD: float = Field(
        default=float(os.getenv("DISTANCE_THRESHOLD", "0.8"))
    )

    # ChromaDB Configurations
    CHROMADB_DIR: Path = Field(
        default=Path(os.getenv("CHROMADB_DIR", str(ROOT_DIR / "chroma_db")))
    )
    CHROMA_COLLECTION_NAME: str = Field(
        default=os.getenv("CHROMA_COLLECTION_NAME", "intellidesk_documents")
    )

    # PostgreSQL Configurations
    POSTGRES_USER: str = Field(default=os.getenv("POSTGRES_USER", "postgres"))
    POSTGRES_PASSWORD: str = Field(default=os.getenv("POSTGRES_PASSWORD", "postgres"))
    POSTGRES_HOST: str = Field(default=os.getenv("POSTGRES_HOST", "localhost"))
    POSTGRES_PORT: str = Field(default=os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = Field(default=os.getenv("POSTGRES_DB", "intellidesk"))

    @property
    def DATABASE_URL(self) -> str:
        url = os.getenv("DATABASE_URL")
        if url:
            return url
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # JWT Authentication Configurations
    JWT_SECRET_KEY: str = Field(
        default=os.getenv("JWT_SECRET_KEY", "b3c7d6c6e7a2b979435b546377e8a9f02c61e27a6f23e4d9c7921a8d052b6510")
    )
    JWT_ALGORITHM: str = Field(default=os.getenv("JWT_ALGORITHM", "HS256"))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
    )

    # Rate Limiting
    RATE_LIMIT_ASK_PER_MIN: int = Field(
        default=int(os.getenv("RATE_LIMIT_ASK_PER_MIN", "30"))
    )

    # Logging
    LOG_LEVEL: str = Field(default=os.getenv("LOG_LEVEL", "INFO"))
    LOG_FILE: str = Field(default=os.getenv("LOG_FILE", "app.log"))

    # Frontend / Connection settings
    API_URL: str = Field(default=os.getenv("API_URL", "http://localhost:3000"))

    # File validation constraints
    ALLOWED_EXTENSIONS: list = Field(default=[".pdf", ".docx", ".xlsx", ".txt"])
    MAX_FILE_SIZE_MB: int = Field(default=int(os.getenv("MAX_FILE_SIZE_MB", "10")))

    # Default seeding credentials
    DEFAULT_ADMIN_USERNAME: str = Field(default=os.getenv("DEFAULT_ADMIN_USERNAME", "admin"))
    DEFAULT_ADMIN_PASSWORD: str = Field(default=os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123"))


settings = Settings()
