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