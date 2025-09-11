import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.models.chat import Chat, ChatMessage


class TestChat:
    """Test chat endpoints."""
    
    def test_create_chat(self, client: TestClient, auth_headers, sample_chat_data):
        """Test creating a new chat."""
        response = client.post(
            "/api/v1/chat/",
            headers=auth_headers,
            json=sample_chat_data
        )
        assert response.status_code == 201
        
        data = response.json()
        assert data["title"] == sample_chat_data["title"]
        assert data["subject"] == sample_chat_data["subject"]
        assert data["difficulty_level"] == sample_chat_data["difficulty_level"]
        assert data["is_active"] is True
    
    def test_create_chat_unauthorized(self, client: TestClient, sample_chat_data):
        """Test creating chat without authentication."""
        response = client.post("/api/v1/chat/", json=sample_chat_data)
        assert response.status_code == 403
    
    def test_get_user_chats(self, client: TestClient, auth_headers, test_user, db_session):
        """Test getting user's chats."""
        # Create test chats
        chat1 = Chat(user_id=test_user.id, title="Chat 1", subject="Math")
        chat2 = Chat(user_id=test_user.id, title="Chat 2", subject="Science")
        db_session.add_all([chat1, chat2])
        db_session.commit()
        
        response = client.get("/api/v1/chat/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        assert any(chat["title"] == "Chat 1" for chat in data)
        assert any(chat["title"] == "Chat 2" for chat in data)
    
    def test_get_specific_chat(self, client: TestClient, auth_headers, test_user, db_session):
        """Test getting a specific chat with messages."""
        chat = Chat(user_id=test_user.id, title="Test Chat", subject="Math")
        db_session.add(chat)
        db_session.commit()
        db_session.refresh(chat)
        
        # Add messages
        message1 = ChatMessage(chat_id=chat.id, content="Hello", role="user")
        message2 = ChatMessage(chat_id=chat.id, content="Hi there!", role="assistant")
        db_session.add_all([message1, message2])
        db_session.commit()
        
        response = client.get(f"/api/v1/chat/{chat.id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == chat.id
        assert data["title"] == "Test Chat"
        assert len(data["messages"]) == 2
    
    def test_get_chat_not_found(self, client: TestClient, auth_headers):
        """Test getting non-existent chat."""
        response = client.get("/api/v1/chat/999", headers=auth_headers)
        assert response.status_code == 404
    
    def test_update_chat(self, client: TestClient, auth_headers, test_user, db_session):
        """Test updating a chat."""
        chat = Chat(user_id=test_user.id, title="Original Title", subject="Math")
        db_session.add(chat)
        db_session.commit()
        db_session.refresh(chat)
        
        update_data = {"title": "Updated Title", "subject": "Science"}
        response = client.put(
            f"/api/v1/chat/{chat.id}",
            headers=auth_headers,
            json=update_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["subject"] == "Science"
    
    def test_delete_chat(self, client: TestClient, auth_headers, test_user, db_session):
        """Test deleting a chat."""
        chat = Chat(user_id=test_user.id, title="To Delete", subject="Math")
        db_session.add(chat)
        db_session.commit()
        db_session.refresh(chat)
        
        response = client.delete(f"/api/v1/chat/{chat.id}", headers=auth_headers)
        assert response.status_code == 200
        
        # Verify chat is deleted
        deleted_chat = db_session.query(Chat).filter(Chat.id == chat.id).first()
        assert deleted_chat is None
    
    @patch('app.services.chat_service.ChatService.get_ai_response')
    def test_send_message(self, mock_ai_response, client: TestClient, auth_headers, test_user, db_session):
        """Test sending a message in chat."""
        # Mock AI response
        mock_ai_response.return_value = AsyncMock(return_value={
            "content": "This is an AI response",
            "model_used": "gpt-4",
            "tokens_used": 25,
            "confidence_score": "high"
        })
        
        chat = Chat(user_id=test_user.id, title="Test Chat", subject="Math")
        db_session.add(chat)
        db_session.commit()
        db_session.refresh(chat)
        
        message_data = {
            "content": "What is 2 + 2?",
            "message_type": "text"
        }
        
        response = client.post(
            f"/api/v1/chat/{chat.id}/messages",
            headers=auth_headers,
            json=message_data
        )
        assert response.status_code == 201
        
        data = response.json()
        assert data["content"] == "This is an AI response"
        assert data["model_used"] == "gpt-4"
        assert data["tokens_used"] == 25
    
    def test_get_chat_messages(self, client: TestClient, auth_headers, test_user, db_session):
        """Test getting messages from a chat."""
        chat = Chat(user_id=test_user.id, title="Test Chat", subject="Math")
        db_session.add(chat)
        db_session.commit()
        db_session.refresh(chat)
        
        # Add messages
        messages = [
            ChatMessage(chat_id=chat.id, content="Message 1", role="user"),
            ChatMessage(chat_id=chat.id, content="Response 1", role="assistant"),
            ChatMessage(chat_id=chat.id, content="Message 2", role="user"),
        ]
        db_session.add_all(messages)
        db_session.commit()
        
        response = client.get(f"/api/v1/chat/{chat.id}/messages", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 3
        assert data[0]["content"] == "Message 1"
        assert data[0]["role"] == "user"
    
    def test_update_message_feedback(self, client: TestClient, auth_headers, test_user, db_session):
        """Test updating message feedback."""
        chat = Chat(user_id=test_user.id, title="Test Chat", subject="Math")
        db_session.add(chat)
        db_session.commit()
        db_session.refresh(chat)
        
        message = ChatMessage(chat_id=chat.id, content="Test message", role="assistant")
        db_session.add(message)
        db_session.commit()
        db_session.refresh(message)
        
        feedback_data = {
            "feedback_rating": 5,
            "understanding_level": "excellent"
        }
        
        response = client.put(
            f"/api/v1/chat/{chat.id}/messages/{message.id}",
            headers=auth_headers,
            json=feedback_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["feedback_rating"] == 5
        assert data["understanding_level"] == "excellent"
    
    def test_get_chat_analytics(self, client: TestClient, auth_headers, test_user, db_session):
        """Test getting chat analytics."""
        chat = Chat(user_id=test_user.id, title="Test Chat", subject="Math")
        db_session.add(chat)
        db_session.commit()
        db_session.refresh(chat)
        
        # Add some messages
        messages = [
            ChatMessage(chat_id=chat.id, content="User message 1", role="user"),
            ChatMessage(chat_id=chat.id, content="AI response 1", role="assistant"),
            ChatMessage(chat_id=chat.id, content="User message 2", role="user"),
        ]
        db_session.add_all(messages)
        db_session.commit()
        
        response = client.get(f"/api/v1/chat/{chat.id}/analytics", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_messages"] == 3
        assert data["user_messages"] == 2
        assert data["ai_messages"] == 1
        assert "topics_discussed" in data
        assert "learning_progress" in data
