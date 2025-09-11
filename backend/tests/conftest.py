import pytest
import asyncio
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import create_app
from app.core.database import get_db, Base
from app.models.user import User
from app.core.security import get_password_hash, create_access_token
from app.config import settings

# Test database URL (use SQLite in memory for testing)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency override."""
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def test_user(db_session):
    """Create a test user in the database."""
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password=get_password_hash("testpassword"),
        role="student",
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_teacher(db_session):
    """Create a test teacher in the database."""
    teacher = User(
        email="teacher@example.com",
        username="testteacher",
        full_name="Test Teacher",
        hashed_password=get_password_hash("teacherpassword"),
        role="teacher",
        is_active=True,
        is_verified=True
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)
    return teacher


@pytest.fixture
def test_admin(db_session):
    """Create a test admin in the database."""
    admin = User(
        email="admin@example.com",
        username="testadmin",
        full_name="Test Admin",
        hashed_password=get_password_hash("adminpassword"),
        role="admin",
        is_active=True,
        is_verified=True
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def user_token(test_user):
    """Create an access token for the test user."""
    return create_access_token(subject=test_user.id)


@pytest.fixture
def teacher_token(test_teacher):
    """Create an access token for the test teacher."""
    return create_access_token(subject=test_teacher.id)


@pytest.fixture
def admin_token(test_admin):
    """Create an access token for the test admin."""
    return create_access_token(subject=test_admin.id)


@pytest.fixture
def auth_headers(user_token):
    """Create authorization headers for API requests."""
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def teacher_auth_headers(teacher_token):
    """Create authorization headers for teacher API requests."""
    return {"Authorization": f"Bearer {teacher_token}"}


@pytest.fixture
def admin_auth_headers(admin_token):
    """Create authorization headers for admin API requests."""
    return {"Authorization": f"Bearer {admin_token}"}


# Test data fixtures
@pytest.fixture
def sample_chat_data():
    """Sample chat creation data."""
    return {
        "title": "Test Chat",
        "subject": "Mathematics",
        "difficulty_level": "intermediate",
        "learning_objectives": ["Learn algebra", "Solve equations"]
    }


@pytest.fixture
def sample_task_data():
    """Sample task creation data."""
    return {
        "title": "Test Assignment",
        "description": "This is a test assignment",
        "instructions": "Complete all questions",
        "task_type": "assignment",
        "subject": "Mathematics",
        "difficulty_level": "intermediate",
        "max_points": 100,
        "due_date": "2024-12-31T23:59:59"
    }


@pytest.fixture
def sample_user_data():
    """Sample user registration data."""
    return {
        "email": "newuser@example.com",
        "username": "newuser",
        "full_name": "New User",
        "password": "newpassword123",
        "confirm_password": "newpassword123",
        "role": "student"
    }


@pytest.fixture
def sample_llm_config_data():
    """Sample LLM configuration data."""
    return {
        "name": "Test GPT-4",
        "description": "Test configuration for GPT-4",
        "provider": "openai",
        "model_name": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 1000,
        "system_prompt": "You are a helpful AI tutor.",
        "use_cases": ["chat", "tutoring"],
        "subject_specializations": ["mathematics", "science"]
    }
