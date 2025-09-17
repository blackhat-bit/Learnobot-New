# app/config.py
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os

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
    
    # Google Cloud Settings
    GOOGLE_CLOUD_PROJECT_ID: Optional[str] = None
    GOOGLE_CLOUD_LOCATION: str = "us-central1"
    USE_SECRET_MANAGER: bool = False  # Set to True in production
    
    # API Keys for various LLM providers (loaded from .env, environment variables, or Secret Manager)
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
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_secrets_from_manager()
    
    def _load_secrets_from_manager(self):
        """Load secrets from Google Secret Manager if enabled"""
        if self.USE_SECRET_MANAGER:
            try:
                from app.services.secrets_service import secrets_service
                
                # Load API keys from Secret Manager
                self.OPENAI_API_KEY = secrets_service.get_secret("openai-api-key") or self.OPENAI_API_KEY
                self.ANTHROPIC_API_KEY = secrets_service.get_secret("anthropic-api-key") or self.ANTHROPIC_API_KEY
                self.GOOGLE_API_KEY = secrets_service.get_secret("google-api-key") or self.GOOGLE_API_KEY
                self.COHERE_API_KEY = secrets_service.get_secret("cohere-api-key") or self.COHERE_API_KEY
                
                # Load other sensitive settings
                secret_key = secrets_service.get_secret("secret-key")
                if secret_key:
                    self.SECRET_KEY = secret_key
                
                database_url = secrets_service.get_secret("database-url")
                if database_url:
                    self.DATABASE_URL = database_url
                    
                print("✅ Loaded secrets from Google Secret Manager")
                
            except Exception as e:
                print(f"⚠️ Failed to load secrets from Secret Manager: {e}")
                print("Falling back to environment variables")

settings = Settings()
