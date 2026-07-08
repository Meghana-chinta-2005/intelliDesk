# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock, patch

from src.database import Base, get_db
from src.api.endpoints import app

# In-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    """Create a clean in-memory database schema for each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Fixture to obtain a SQLAlchemy session for test verification."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function", autouse=True)
def mock_external_services(request):
    """Mock database setup, chroma client, and Groq SDK globally for unit tests."""
    if "test_retrieval_accuracy" in request.node.name:
        # Avoid mocking any resources for the real FAISS retrieval evaluation
        yield {}
        return
    with (
        patch("src.vector_store.embed_store.get_chroma_client"),
        patch("src.vector_store.embed_store.get_collection") as mock_chroma_coll,
        patch("src.vector_store.retrieve.get_chroma_client"),
        patch("src.vector_store.retrieve.get_collection") as mock_retrieve_coll,
        patch("src.vector_store.embed_store.get_embedding_model") as mock_embed_model,
        patch("src.vector_store.retrieve.get_embedding_model") as mock_retrieve_model,
        patch("src.services.generate.Groq") as mock_groq,
    ):
        
        # Setup mocks
        import numpy as np
        mock_model_inst = MagicMock()
        mock_model_inst.encode.return_value = np.array([[0.1] * 384])
        mock_embed_model.return_value = mock_model_inst
        mock_retrieve_model.return_value = mock_model_inst

        # Mock ChromaDB collections query
        mock_coll_inst = MagicMock()
        mock_coll_inst.query.return_value = {
            "ids": [["chunk_1"]],
            "distances": [[0.35]],
            "metadatas": [[{"source": "test.pdf", "page": "3", "user_id": 1}]],
            "documents": [["Test parsed chunk text content"]]
        }
        mock_chroma_coll.return_value = mock_coll_inst
        mock_retrieve_coll.return_value = mock_coll_inst

        # Mock Groq Client completions API
        mock_groq_inst = MagicMock()
        mock_completions = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Grounded response answering the query. Sources: test.pdf — Page 3"
        mock_completions.choices = [mock_choice]
        mock_groq_inst.chat.completions.create.return_value = mock_completions
        mock_groq.return_value = mock_groq_inst

        yield {
            "chroma_collection": mock_coll_inst,
            "groq_client": mock_groq_inst,
            "embedding_model": mock_model_inst
        }


@pytest.fixture(scope="function", autouse=True)
def override_db_dependency(db_session):
    """Override FastAPI dependency injection to use the test SQLite DB."""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)
