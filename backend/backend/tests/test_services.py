import pytest
from unittest.mock import Mock, patch, AsyncMock

from app.services.auth_service import AuthService
from app.services.chat_service import ChatService
from app.services.ocr_service import OCRService
from app.services.translation_service import TranslationService
from app.models.user import User, UserRole
from app.models.chat import Chat


class TestAuthService:
    """Test authentication service."""
    
    def test_register_user(self, db_session):
        """Test user registration through service."""
        auth_service = AuthService(db_session)
        
        user_data = Mock()
        user_data.email = "test@example.com"
        user_data.username = "testuser"
        user_data.full_name = "Test User"
        user_data.password = "testpassword"
        user_data.role = UserRole.STUDENT
        user_data.language_preference = "en"
        user_data.timezone = "UTC"
        
        user = auth_service.register_user(user_data)
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.role == UserRole.STUDENT
        assert user.is_active is True
    
    def test_authenticate_user_success(self, db_session, test_user):
        """Test successful user authentication."""
        auth_service = AuthService(db_session)
        
        authenticated_user = auth_service.authenticate_user(
            test_user.username, "testpassword"
        )
        
        assert authenticated_user is not None
        assert authenticated_user.id == test_user.id
    
    def test_authenticate_user_wrong_password(self, db_session, test_user):
        """Test authentication with wrong password."""
        auth_service = AuthService(db_session)
        
        authenticated_user = auth_service.authenticate_user(
            test_user.username, "wrongpassword"
        )
        
        assert authenticated_user is None
    
    def test_authenticate_user_nonexistent(self, db_session):
        """Test authentication with nonexistent user."""
        auth_service = AuthService(db_session)
        
        authenticated_user = auth_service.authenticate_user(
            "nonexistent", "password"
        )
        
        assert authenticated_user is None
    
    def test_get_user_by_id(self, db_session, test_user):
        """Test getting user by ID."""
        auth_service = AuthService(db_session)
        
        found_user = auth_service.get_user_by_id(test_user.id)
        
        assert found_user is not None
        assert found_user.id == test_user.id
    
    def test_get_user_by_username(self, db_session, test_user):
        """Test getting user by username."""
        auth_service = AuthService(db_session)
        
        found_user = auth_service.get_user_by_username(test_user.username)
        
        assert found_user is not None
        assert found_user.username == test_user.username


class TestChatService:
    """Test chat service."""
    
    def test_create_chat(self, db_session, test_user):
        """Test chat creation through service."""
        chat_service = ChatService(db_session)
        
        chat = chat_service.create_chat(
            user_id=test_user.id,
            title="Test Chat",
            subject="Mathematics"
        )
        
        assert chat.id is not None
        assert chat.user_id == test_user.id
        assert chat.title == "Test Chat"
        assert chat.subject == "Mathematics"
    
    def test_get_user_chats(self, db_session, test_user):
        """Test getting user's chats."""
        chat_service = ChatService(db_session)
        
        # Create test chats
        chat1 = chat_service.create_chat(test_user.id, "Chat 1")
        chat2 = chat_service.create_chat(test_user.id, "Chat 2")
        
        chats = chat_service.get_user_chats(test_user.id)
        
        assert len(chats) == 2
        chat_titles = [chat.title for chat in chats]
        assert "Chat 1" in chat_titles
        assert "Chat 2" in chat_titles
    
    def test_get_chat_by_id(self, db_session, test_user):
        """Test getting chat by ID."""
        chat_service = ChatService(db_session)
        
        created_chat = chat_service.create_chat(test_user.id, "Test Chat")
        found_chat = chat_service.get_chat_by_id(created_chat.id, test_user.id)
        
        assert found_chat is not None
        assert found_chat.id == created_chat.id
        assert found_chat.title == "Test Chat"
    
    def test_add_user_message(self, db_session, test_user):
        """Test adding user message."""
        chat_service = ChatService(db_session)
        
        chat = chat_service.create_chat(test_user.id, "Test Chat")
        message = chat_service.add_user_message(
            chat.id, "Hello, this is a test message"
        )
        
        assert message.id is not None
        assert message.chat_id == chat.id
        assert message.content == "Hello, this is a test message"
        assert message.role == "user"
    
    @patch('app.ai.llm_manager.LLMManager.generate_response')
    async def test_get_ai_response(self, mock_generate_response, db_session, test_user):
        """Test getting AI response."""
        mock_generate_response.return_value = {
            "content": "This is an AI response",
            "model_used": "gpt-4",
            "tokens_used": 25,
            "confidence_score": "high"
        }
        
        chat_service = ChatService(db_session)
        chat = chat_service.create_chat(test_user.id, "Test Chat")
        
        # Mock LLM config
        with patch.object(chat_service, '_get_llm_config_for_chat') as mock_config:
            mock_config.return_value = Mock()
            
            response = await chat_service.get_ai_response(chat.id, "Test message")
            
            assert response.content == "This is an AI response"
            assert response.model_used == "gpt-4"
            assert response.tokens_used == 25


class TestOCRService:
    """Test OCR service."""
    
    def test_ocr_service_initialization(self):
        """Test OCR service initialization."""
        ocr_service = OCRService()
        assert ocr_service is not None
    
    def test_is_valid_image_type(self):
        """Test image type validation."""
        ocr_service = OCRService()
        
        assert ocr_service._is_valid_image_type("image/jpeg") is True
        assert ocr_service._is_valid_image_type("image/png") is True
        assert ocr_service._is_valid_image_type("text/plain") is False
        assert ocr_service._is_valid_image_type(None) is False
    
    def test_detect_language(self):
        """Test language detection."""
        ocr_service = OCRService()
        
        # Test English text
        english_text = "The quick brown fox jumps over the lazy dog"
        language = ocr_service._detect_language(english_text)
        assert language == "en"
        
        # Test empty text
        empty_language = ocr_service._detect_language("")
        assert empty_language == "unknown"
    
    def test_get_supported_formats(self):
        """Test getting supported formats."""
        ocr_service = OCRService()
        formats = ocr_service.get_supported_formats()
        
        assert isinstance(formats, list)
        assert "JPEG" in formats
        assert "PNG" in formats


class TestTranslationService:
    """Test translation service."""
    
    def test_translation_service_initialization(self):
        """Test translation service initialization."""
        translation_service = TranslationService()
        assert translation_service is not None
        assert translation_service.supported_languages is not None
    
    def test_get_supported_languages(self):
        """Test getting supported languages."""
        translation_service = TranslationService()
        languages = translation_service.get_supported_languages()
        
        assert isinstance(languages, dict)
        assert "en" in languages
        assert "es" in languages
        assert "fr" in languages
        assert languages["en"] == "English"
    
    def test_get_popular_languages(self):
        """Test getting popular languages."""
        translation_service = TranslationService()
        popular = translation_service.get_popular_languages()
        
        assert isinstance(popular, list)
        assert len(popular) > 0
        
        # Check structure
        first_lang = popular[0]
        assert "code" in first_lang
        assert "name" in first_lang
    
    @patch('googletrans.Translator.translate')
    async def test_translate_text(self, mock_translate, db_session):
        """Test text translation."""
        mock_result = Mock()
        mock_result.text = "Hola"
        mock_result.src = "en"
        mock_result.confidence = 1.0
        mock_translate.return_value = mock_result
        
        translation_service = TranslationService()
        
        result = await translation_service.translate_text("Hello", "es", "en")
        
        assert result["original_text"] == "Hello"
        assert result["translated_text"] == "Hola"
        assert result["source_language"] == "en"
        assert result["target_language"] == "es"
