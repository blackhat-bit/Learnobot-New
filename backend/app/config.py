# app/config.py
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "LearnoBot"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql://learnobot:StrongPassword123!@localhost:5432/learnobot_db"
    
    # Security
    SECRET_KEY: str = "a1ef3997f59da47f4e2bd3feba6bb6a412213d77e892e510fa8b0341ee332788"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # LLM Settings
    LLM_TYPE: str = "ollama"  # Options: llamacpp, gpt4all, ollama
    LLM_MODEL_PATH: str = "./models/llama-2-7b-chat-hf"  # For local models
    LLM_MODEL_NAME: str = "llama3.1:8b"  # For Ollama
    LLM_MAX_TOKENS: int = 2048
    LLM_TEMPERATURE: float = 0.7
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    # API Keys for various LLM providers (loaded from .env or environment variables)
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    COHERE_API_KEY: Optional[str] = None
    
    # OCR Settings
    OCR_LANGUAGE: str = "heb+eng"
    
    # File upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Feature Flags
    ENABLE_ANALYTICS: bool = True
    ENABLE_MULTI_LLM: bool = True
    ENABLE_OCR: bool = True
    ENABLE_MANAGER_INTERFACE: bool = True
    
    class Config:
        env_file = ".env"

settings = Settings()
