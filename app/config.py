from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    # App
    app_name: str = "Learnobot Backend"
    version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"
    
    # Database
    database_url: str
    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # CORS
    allowed_origins: str = "http://localhost:3000"
    
    # File Storage
    upload_dir: str = "uploads"
    max_file_size: int = 10485760  # 10MB
    
    # OCR
    tesseract_path: str = "/usr/bin/tesseract"
    
    # Translation
    google_translate_api_key: Optional[str] = None
    
    @validator('allowed_origins')
    def parse_cors_origins(cls, v: str) -> List[str]:
        return [origin.strip() for origin in v.split(',')]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
