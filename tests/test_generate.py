import pytest
import os
from unittest.mock import patch, MagicMock
from src.services.generate import generate


@patch("src.services.generate.Groq")
def test_generate_with_context(mock_groq_class):
    """generate should call the Groq client with formatted context and return the response."""
    # Setup mock Groq client
    mock_client = MagicMock()
    mock_groq_class.return_value = mock_client

    # Setup mock chat completion response
    mock_completion = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "Mocked grounded answer. Sources: doc1.txt"
    mock_completion.choices = [MagicMock(message=mock_message)]
    mock_client.chat.completions.create.return_value = mock_completion

    chunks = [
        {
            "text": "Company wifi password is 123.",
            "source": "wifi.txt",
            "chunk_id": 0,
        }
    ]

    with patch.dict(os.environ, {"GROQ_API_KEY": "fake_api_key"}):
        # We need to temporarily mock settings.GROQ_API_KEY so it doesn't fail validation
        from src.config.config import settings

        with patch.object(settings, "GROQ_API_KEY", "fake_api_key"):
            answer = generate("What is the wifi password?", chunks)

    assert answer == "Mocked grounded answer. Sources: doc1.txt"
    mock_client.chat.completions.create.assert_called_once()
    call_kwargs = mock_client.chat.completions.create.call_args[1]
    assert call_kwargs["model"] == "llama-3.1-8b-instant"
    assert call_kwargs["temperature"] == 0.2
    assert len(call_kwargs["messages"]) == 2


@patch("src.services.generate.Groq")
def test_generate_without_context(mock_groq_class):
    """generate should handle empty context chunks and query the LLM appropriately."""
    mock_client = MagicMock()
    mock_groq_class.return_value = mock_client

    mock_completion = MagicMock()
    mock_message = MagicMock()
    mock_message.content = (
        "I could not find relevant information in the knowledge base."
    )
    mock_completion.choices = [MagicMock(message=mock_message)]
    mock_client.chat.completions.create.return_value = mock_completion

    with patch.dict(os.environ, {"GROQ_API_KEY": "fake_api_key"}):
        from src.config.config import settings

        with patch.object(settings, "GROQ_API_KEY", "fake_api_key"):
            answer = generate("Unknown query", [])

    assert answer == "I could not find relevant information in the knowledge base."
    mock_client.chat.completions.create.assert_called_once()


def test_generate_raises_environment_error_when_no_api_key():
    """generate should raise EnvironmentError if GROQ_API_KEY is not configured."""
    from src.config.config import settings

    with patch.object(settings, "GROQ_API_KEY", ""):
        with pytest.raises(EnvironmentError) as exc_info:
            generate("test question", [])
        assert "GROQ_API_KEY environment variable not set" in str(exc_info.value)
