# app/config.py
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "LearnoBot"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql://learnobot:password@localhost:5432/learnobot_db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # LLM Settings (for local model)
    LLM_MODEL_PATH: str = "./models/llama-2-7b-chat-hf"  # Or other local model
    LLM_TYPE: str = "llamacpp"  # Options: llamacpp, gpt4all, ollama
    LLM_MAX_TOKENS: int = 2048
    LLM_TEMPERATURE: float = 0.7
    
    # OCR Settings
    OCR_LANGUAGE: str = "heb+eng"
    
    # File upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    class Config:
        env_file = ".env"

settings = Settings()
