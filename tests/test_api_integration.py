from fastapi.testclient import TestClient
from unittest.mock import patch

from src.api.endpoints import app
from src.models.db_models import User, Document, Conversation, Message

client = TestClient(app)


def test_register_and_login(db_session):
    """Test user registration and successful JWT login flow."""
    # 1. Register
    reg_response = client.post(
        "/api/auth/register",
        json={"username": "testuser", "password": "testpassword"}
    )
    assert reg_response.status_code == 201
    reg_data = reg_response.json()
    assert reg_data["username"] == "testuser"
    assert reg_data["is_admin"] is False

    # Try duplicate registration
    dup_response = client.post(
        "/api/auth/register",
        json={"username": "testuser", "password": "anotherpassword"}
    )
    assert dup_response.status_code == 400

    # 2. Login
    login_response = client.post(
        "/api/auth/login",
        json={"username": "testuser", "password": "testpassword"}
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"


def test_auth_me_endpoint(db_session):
    """Test retrieving user profile information with a valid JWT token."""
    # Create user
    user = User(username="me_user", hashed_password="hashed_placeholder", is_admin=False)
    db_session.add(user)
    db_session.commit()

    # Generate token
    from src.utils.auth import create_access_token
    token = create_access_token({"sub": user.username, "user_id": user.id})

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "me_user"
    assert data["id"] == user.id


def test_ask_endpoint(db_session):
    """Test RAG Ask endpoint, verifying conversation creation and cited responses."""
    user = User(username="chat_user", hashed_password="hashed_placeholder", is_admin=False)
    db_session.add(user)
    db_session.commit()

    from src.utils.auth import create_access_token
    token = create_access_token({"sub": user.username, "user_id": user.id})

    # Test ask question (first time, creates conversation)
    response = client.post(
        "/api/chat/ask",
        headers={"Authorization": f"Bearer {token}"},
        json={"question": "Where is the documentation for VPN resets?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "conversation_id" in data
    assert len(data["sources"]) > 0
    assert data["sources"][0]["filename"] == "test.pdf"

    # Test ask with conversation ID
    conv_id = data["conversation_id"]
    response2 = client.post(
        "/api/chat/ask",
        headers={"Authorization": f"Bearer {token}"},
        json={"question": "What else is covered?", "conversation_id": conv_id}
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["conversation_id"] == conv_id


def test_list_conversations_and_history(db_session):
    """Test fetching conversation listing and message thread details."""
    user = User(username="conv_user", hashed_password="hashed_placeholder", is_admin=False)
    db_session.add(user)
    db_session.commit()

    conv = Conversation(user_id=user.id, title="Test Chat Session")
    db_session.add(conv)
    db_session.commit()

    msg = Message(conversation_id=conv.id, sender="user", text="Hello")
    db_session.add(msg)
    db_session.commit()

    from src.utils.auth import create_access_token
    token = create_access_token({"sub": user.username, "user_id": user.id})

    # List conversations
    list_res = client.get("/api/chat/conversations", headers={"Authorization": f"Bearer {token}"})
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1
    assert list_res.json()[0]["title"] == "Test Chat Session"

    # Get conversation messages
    detail_res = client.get(f"/api/chat/conversations/{conv.id}", headers={"Authorization": f"Bearer {token}"})
    assert detail_res.status_code == 200
    assert detail_res.json()["title"] == "Test Chat Session"
    assert len(detail_res.json()["messages"]) == 1
    assert detail_res.json()["messages"][0]["text"] == "Hello"


def test_document_list_and_evict(db_session):
    """Test listing files and deleting document records."""
    user = User(username="doc_user", hashed_password="hashed_placeholder", is_admin=False)
    db_session.add(user)
    db_session.commit()

    doc = Document(
        user_id=user.id,
        filename="test_policy.pdf",
        file_path="data/uploads/user_doc_test_policy.pdf",
        file_size=1024,
        chunk_count=5
    )
    db_session.add(doc)
    db_session.commit()

    from src.utils.auth import create_access_token
    token = create_access_token({"sub": user.username, "user_id": user.id})

    # List
    response = client.get("/api/documents", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["filename"] == "test_policy.pdf"

    # Delete
    with patch("src.api.endpoints.delete_document_chunks") as mock_delete:
        del_response = client.delete(f"/api/documents/{doc.id}", headers={"Authorization": f"Bearer {token}"})
        assert del_response.status_code == 204
        mock_delete.assert_called_once_with(doc.id)

    # Check deleted from DB
    assert db_session.query(Document).filter(Document.id == doc.id).first() is None


def test_admin_dashboard_guards(db_session):
    """Verify that standard agents are restricted, and administrators can fetch metrics."""
    # 1. Create a regular user
    user = User(username="agent_user", hashed_password="hashed_placeholder", is_admin=False)
    db_session.add(user)
    db_session.commit()

    # 2. Create an admin user
    admin = User(username="admin_user", hashed_password="hashed_placeholder", is_admin=True)
    db_session.add(admin)
    db_session.commit()

    from src.utils.auth import create_access_token
    agent_token = create_access_token({"sub": user.username, "user_id": user.id})
    admin_token = create_access_token({"sub": admin.username, "user_id": admin.id})

    # Try regular user (should be Forbidden HTTP 403)
    response = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {agent_token}"})
    assert response.status_code == 403

    # Try admin user (should succeed HTTP 200)
    response_admin = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
    assert response_admin.status_code == 200
    data = response_admin.json()
    assert "total_users" in data
    assert "total_documents" in data
    assert "total_queries" in data
    assert "avg_response_time" in data
