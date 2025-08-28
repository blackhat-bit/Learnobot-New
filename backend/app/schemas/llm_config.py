# app/schemas/llm_config.py
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class LLMProviderInfo(BaseModel):
    name: str
    info: Dict[str, Any]
    active: bool

class LLMConfigCreate(BaseModel):
    name: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 0.9
    system_prompt: str

class LLMConfigUpdate(BaseModel):
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    system_prompt: Optional[str] = None

class ProviderComparison(BaseModel):
    prompt: str
    providers: List[str]

class SystemPromptUpdate(BaseModel):
    system: str
    temperature: float
    maxTokens: int

class APIKeyUpdate(BaseModel):
    provider_name: str  # "openai", "anthropic", "google"
    api_key: str
    
class APIKeyResponse(BaseModel):
    provider_name: str
    has_key: bool  # Don't return actual key for security
    key_length: Optional[int] = None  # Just show length for verification
    
class ProviderStatus(BaseModel):
    name: str
    type: str
    is_available: bool
    has_api_key: bool
    is_active: bool
    info: Dict[str, Any]