import logging
from typing import List, Dict, Tuple, Any
from sqlalchemy.orm import Session

from src.models.db_models import Message
from src.vector_store.retrieve import retrieve
from src.services.generate import generate

logger = logging.getLogger(__name__)


def run_pipeline(
    db: Session,
    user_id: int,
    conversation_id: int,
    question: str
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Orchestrate the multi-tenant RAG process:
    1. Load recent conversation history context from PostgreSQL.
    2. Retrieve semantically matching document chunks from ChromaDB (isolated to user_id).
    3. Invoke Groq LLM (Llama 3.1) to generate a grounded, cited answer.
    
    Returns:
        (answer_text, retrieved_chunks_metadata)
    """
    logger.info(f"Pipeline: Running for user_id={user_id}, conv_id={conversation_id}, query={question!r}")
    
    try:
        # 1. Retrieve last 8 messages of conversation history to inject as context
        history_msgs = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .all()
        )
        
        # Format for Groq system structure
        history = []
        for msg in history_msgs[-8:]:  # Take the last 8 messages (4 turns) to stay within safe token limits
            role = "user" if msg.sender == "user" else "assistant"
            history.append({"role": role, "content": msg.text})
            
        logger.info(f"Pipeline: Injected {len(history)} messages from conversation history.")

        # 2. Perform metadata-isolated similarity search
        relevant_chunks = retrieve(user_id=user_id, query=question)
        logger.info(f"Pipeline: Retrieved {len(relevant_chunks)} chunks below similarity cutoff.")

        # 3. Request LLM completion
        answer = generate(query=question, chunks=relevant_chunks, history=history)
        
        return answer, relevant_chunks

    except Exception as exc:
        logger.error(
            f"Pipeline: Execution failed for user_id={user_id}, query={question!r}: {exc}",
            exc_info=True
        )
        raise


def _ensure_loaded():
    """Dummy loader function required for backwards compatibility in baseline testing."""
    pass

