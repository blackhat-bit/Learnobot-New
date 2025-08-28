# app/ai/multi_llm_manager.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum
import os
from datetime import datetime

# LangChain imports
from langchain.llms import OpenAI, Anthropic, GooglePalm, Cohere, HuggingFaceHub, Ollama, LlamaCpp
from langchain.chat_models import ChatOpenAI, ChatAnthropic, ChatGooglePalm
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain.callbacks.base import BaseCallbackHandler

# For API key management
from app.config import settings
from app.models.llm_config import LLMProvider, LLMConfig
from sqlalchemy.orm import Session
import json

class LLMProviderType(str, Enum):
    # Local models
    OLLAMA = "ollama"
    LLAMACPP = "llamacpp"
    
    # Online models
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"

class ResponseLogger(BaseCallbackHandler):
    """Logs all LLM responses for comparison"""
    def __init__(self, provider: str, session_id: int, db: Session):
        self.provider = provider
        self.session_id = session_id
        self.db = db
        self.start_time = None
        
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs) -> None:
        self.start_time = datetime.utcnow()
        
    def on_llm_end(self, response, **kwargs) -> None:
        if self.start_time:
            response_time = (datetime.utcnow() - self.start_time).total_seconds()
            # Log to database for analysis
            from app.models.llm_config import LLMTestLog
            log = LLMTestLog(
                session_id=self.session_id,
                provider=self.provider,
                response_time=response_time,
                response_text=str(response),
                timestamp=datetime.utcnow()
            )
            self.db.add(log)
            self.db.commit()

class BaseLLMProvider(ABC):
    """Base class for all LLM providers"""
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]):
        pass
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        pass
    
    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        pass

class OllamaProvider(BaseLLMProvider):
    def initialize(self, config: Dict[str, Any]):
        self.llm = Ollama(
            model=config.get("model", settings.LLM_MODEL_NAME),
            temperature=config.get("temperature", 0.7),
            top_p=config.get("top_p", 0.9),
        )
        
    def generate(self, prompt: str, **kwargs) -> str:
        return self.llm(prompt)
    
    def get_info(self) -> Dict[str, Any]:
        return {
            "provider": "Ollama",
            "type": "local",
            "model": self.llm.model,
            "requires_api_key": False
        }

class OpenAIProvider(BaseLLMProvider):
    def initialize(self, config: Dict[str, Any]):
        api_key = config.get("api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is required")
            
        self.llm = ChatOpenAI(
            model_name=config.get("model", "gpt-4"),
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens", 2048),
            openai_api_key=api_key
        )
        
    def generate(self, prompt: str, **kwargs) -> str:
        messages = [HumanMessage(content=prompt)]
        response = self.llm(messages)
        return response.content
    
    def get_info(self) -> Dict[str, Any]:
        return {
            "provider": "OpenAI",
            "type": "online",
            "model": self.llm.model_name,
            "requires_api_key": True
        }

class AnthropicProvider(BaseLLMProvider):
    def initialize(self, config: Dict[str, Any]):
        api_key = config.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Anthropic API key is required")
            
        self.llm = ChatAnthropic(
            model=config.get("model", "claude-3-opus-20240229"),
            temperature=config.get("temperature", 0.7),
            max_tokens_to_sample=config.get("max_tokens", 2048),
            anthropic_api_key=api_key
        )
        
    def generate(self, prompt: str, **kwargs) -> str:
        messages = [HumanMessage(content=prompt)]
        response = self.llm(messages)
        return response.content
    
    def get_info(self) -> Dict[str, Any]:
        return {
            "provider": "Anthropic",
            "type": "online", 
            "model": self.llm.model,
            "requires_api_key": True
        }

class GoogleProvider(BaseLLMProvider):
    def initialize(self, config: Dict[str, Any]):
        api_key = config.get("api_key") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Google API key is required")
            
        self.llm = ChatGooglePalm(
            model_name=config.get("model", "models/chat-bison-001"),
            temperature=config.get("temperature", 0.7),
            max_output_tokens=config.get("max_tokens", 2048),
            google_api_key=api_key
        )
        
    def generate(self, prompt: str, **kwargs) -> str:
        messages = [HumanMessage(content=prompt)]
        response = self.llm(messages)
        return response.content
    
    def get_info(self) -> Dict[str, Any]:
        return {
            "provider": "Google",
            "type": "online",
            "model": self.llm.model_name,
            "requires_api_key": True
        }

class MultiProviderLLMManager:
    """Manages multiple LLM providers for testing and comparison"""
    
    def __init__(self):
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.active_provider: Optional[str] = None
        self._initialize_providers()
        
    def _initialize_providers(self):
        """Initialize all configured providers"""
        # Always initialize local providers
        try:
            ollama_provider = OllamaProvider()
            ollama_provider.initialize({"model": settings.LLM_MODEL_NAME})
            self.providers["ollama"] = ollama_provider
            self.active_provider = "ollama"  # Default to local
        except Exception as e:
            print(f"Failed to initialize Ollama: {e}")
            
        # Initialize online providers if API keys are available
        from app.config import settings
        
        if settings.OPENAI_API_KEY:
            try:
                openai_provider = OpenAIProvider()
                openai_provider.initialize({"api_key": settings.OPENAI_API_KEY})
                self.providers["openai"] = openai_provider
            except Exception as e:
                print(f"Failed to initialize OpenAI: {e}")
                
        if settings.ANTHROPIC_API_KEY:
            try:
                anthropic_provider = AnthropicProvider()
                anthropic_provider.initialize({"api_key": settings.ANTHROPIC_API_KEY})
                self.providers["anthropic"] = anthropic_provider
            except Exception as e:
                print(f"Failed to initialize Anthropic: {e}")
                
        if settings.GOOGLE_API_KEY:
            try:
                google_provider = GoogleProvider()
                google_provider.initialize({"api_key": settings.GOOGLE_API_KEY})
                self.providers["google"] = google_provider
            except Exception as e:
                print(f"Failed to initialize Google: {e}")
    
    def set_active_provider(self, provider_name: str):
        """Switch to a different provider"""
        if provider_name not in self.providers:
            raise ValueError(f"Provider {provider_name} not available")
        self.active_provider = provider_name
        
    def get_available_providers(self) -> List[Dict[str, Any]]:
        """Get list of all available providers"""
        return [
            {
                "name": name,
                "info": provider.get_info(),
                "active": name == self.active_provider
            }
            for name, provider in self.providers.items()
        ]
    
    def generate(self, prompt: str, provider: Optional[str] = None, **kwargs) -> str:
        """Generate response using specified or active provider"""
        provider_name = provider or self.active_provider
        if not provider_name or provider_name not in self.providers:
            raise ValueError(f"Provider {provider_name} not available")
            
        return self.providers[provider_name].generate(prompt, **kwargs)
    
    def compare_providers(self, prompt: str, providers: List[str] = None) -> Dict[str, Any]:
        """Run the same prompt through multiple providers for comparison"""
        if providers is None:
            providers = list(self.providers.keys())
            
        results = {}
        for provider_name in providers:
            if provider_name in self.providers:
                try:
                    start_time = datetime.utcnow()
                    response = self.providers[provider_name].generate(prompt)
                    end_time = datetime.utcnow()
                    
                    results[provider_name] = {
                        "response": response,
                        "response_time": (end_time - start_time).total_seconds(),
                        "success": True,
                        "error": None
                    }
                except Exception as e:
                    results[provider_name] = {
                        "response": None,
                        "response_time": None,
                        "success": False,
                        "error": str(e)
                    }
                    
        return results

# Singleton instance
multi_llm_manager = MultiProviderLLMManager()