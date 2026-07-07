from fastapi.testclient import TestClient
from unittest.mock import patch


def test_health_endpoint():
    """GET /health should return 200 with status=ok."""
    # Patch pipeline so tests don't need FAISS index or Groq API
    with patch("src.services.pipeline._ensure_loaded"):
        from main import app

        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_ask_empty_question():
    """POST /ask with empty question should return 400."""
    with patch("src.services.pipeline._ensure_loaded"):
        from main import app

        client = TestClient(app)
        response = client.post("/ask", json={"question": ""})
        assert response.status_code == 400


def test_ask_endpoint_structure():
    """POST /ask should return question and answer keys."""
    with patch("src.api.endpoints.run_pipeline", return_value="Mocked answer."):
        with patch("src.services.pipeline._ensure_loaded"):
            from main import app

            client = TestClient(app)
            response = client.post("/ask", json={"question": "Test question"})
            assert response.status_code == 200
            data = response.json()
            assert "question" in data
            assert "answer" in data
