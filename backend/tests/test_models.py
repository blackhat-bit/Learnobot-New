import pytest
from datetime import datetime

from app.models.user import User, UserRole
from app.models.chat import Chat, ChatMessage
from app.models.task import Task, TaskSubmission, TaskType, TaskStatus, SubmissionStatus
from app.models.llm_config import LLMConfig


class TestModels:
    """Test database models."""
    
    def test_user_model(self, db_session):
        """Test User model creation and relationships."""
        user = User(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            hashed_password="hashedpassword",
            role=UserRole.STUDENT
        )
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.role == UserRole.STUDENT
        assert user.is_active is True
        assert user.is_verified is False
        assert user.created_at is not None
    
    def test_chat_model(self, db_session, test_user):
        """Test Chat model creation and relationships."""
        chat = Chat(
            user_id=test_user.id,
            title="Test Chat",
            subject="Mathematics",
            difficulty_level="intermediate"
        )
        
        db_session.add(chat)
        db_session.commit()
        db_session.refresh(chat)
        
        assert chat.id is not None
        assert chat.user_id == test_user.id
        assert chat.title == "Test Chat"
        assert chat.subject == "Mathematics"
        assert chat.is_active is True
        assert chat.created_at is not None
        
        # Test relationship
        assert chat.user == test_user
    
    def test_chat_message_model(self, db_session, test_user):
        """Test ChatMessage model creation and relationships."""
        chat = Chat(user_id=test_user.id, title="Test Chat")
        db_session.add(chat)
        db_session.commit()
        db_session.refresh(chat)
        
        message = ChatMessage(
            chat_id=chat.id,
            content="Hello, this is a test message",
            role="user",
            message_type="text"
        )
        
        db_session.add(message)
        db_session.commit()
        db_session.refresh(message)
        
        assert message.id is not None
        assert message.chat_id == chat.id
        assert message.content == "Hello, this is a test message"
        assert message.role == "user"
        assert message.message_type == "text"
        assert message.created_at is not None
        
        # Test relationship
        assert message.chat == chat
    
    def test_task_model(self, db_session, test_teacher):
        """Test Task model creation and relationships."""
        task = Task(
            title="Test Assignment",
            description="This is a test assignment",
            task_type=TaskType.ASSIGNMENT,
            status=TaskStatus.PUBLISHED,
            teacher_id=test_teacher.id,
            max_points=100,
            subject="Mathematics"
        )
        
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        
        assert task.id is not None
        assert task.title == "Test Assignment"
        assert task.task_type == TaskType.ASSIGNMENT
        assert task.status == TaskStatus.PUBLISHED
        assert task.teacher_id == test_teacher.id
        assert task.max_points == 100
        assert task.created_at is not None
        
        # Test relationship
        assert task.teacher == test_teacher
    
    def test_task_submission_model(self, db_session, test_user, test_teacher):
        """Test TaskSubmission model creation and relationships."""
        task = Task(
            title="Test Task",
            description="Test description",
            teacher_id=test_teacher.id,
            max_points=100
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        
        submission = TaskSubmission(
            task_id=task.id,
            student_id=test_user.id,
            content="This is my submission",
            status=SubmissionStatus.SUBMITTED,
            max_score=100
        )
        
        db_session.add(submission)
        db_session.commit()
        db_session.refresh(submission)
        
        assert submission.id is not None
        assert submission.task_id == task.id
        assert submission.student_id == test_user.id
        assert submission.content == "This is my submission"
        assert submission.status == SubmissionStatus.SUBMITTED
        assert submission.attempt_number == 1
        assert submission.ai_hints_used == 0
        
        # Test relationships
        assert submission.task == task
        assert submission.student == test_user
    
    def test_llm_config_model(self, db_session):
        """Test LLMConfig model creation."""
        config = LLMConfig(
            name="Test GPT-4",
            provider="openai",
            model_name="gpt-4",
            temperature=0.7,
            max_tokens=1000,
            system_prompt="You are a helpful assistant",
            is_active=True,
            is_default=False
        )
        
        db_session.add(config)
        db_session.commit()
        db_session.refresh(config)
        
        assert config.id is not None
        assert config.name == "Test GPT-4"
        assert config.provider == "openai"
        assert config.model_name == "gpt-4"
        assert config.temperature == 0.7
        assert config.max_tokens == 1000
        assert config.is_active is True
        assert config.is_default is False
        assert config.created_at is not None
    
    def test_user_repr(self, test_user):
        """Test User __repr__ method."""
        repr_str = repr(test_user)
        assert "User(id=" in repr_str
        assert "username='testuser'" in repr_str
        assert "role='student'" in repr_str
    
    def test_chat_repr(self, db_session, test_user):
        """Test Chat __repr__ method."""
        chat = Chat(user_id=test_user.id, title="Test Chat")
        db_session.add(chat)
        db_session.commit()
        db_session.refresh(chat)
        
        repr_str = repr(chat)
        assert "Chat(id=" in repr_str
        assert "title='Test Chat'" in repr_str
        assert f"user_id={test_user.id}" in repr_str
