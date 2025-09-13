# app/ai/multi_llm_manager.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum
import os
import requests
from datetime import datetime

# LangChain imports (only for Ollama and legacy support)
from langchain.llms import Ollama
from langchain.callbacks.base import BaseCallbackHandler

# For API key management
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
    def __init__(self):
        self.model_name = None
        self.llm = None
    
    def initialize(self, config: Dict[str, Any]):
        from app.config import settings  # Import here to avoid circular imports
        self.model_name = config.get("model", settings.LLM_MODEL_NAME)
        self.llm = Ollama(
            model=self.model_name,
            temperature=config.get("temperature", 0.7),
            top_p=config.get("top_p", 0.9),
        )
        
    def generate(self, prompt: str, **kwargs) -> str:
        import time
        import logging
        
        logger = logging.getLogger(__name__)
        start_time = time.time()
        prompt_length = len(prompt)
        
        try:
            response = self.llm(prompt)
            response_time = time.time() - start_time
            
            logger.info(f"Ollama {self.model_name} - Prompt: {prompt_length} chars, Response: {response_time:.2f}s")
            
            # Log performance warning if slow
            if response_time > 10.0:
                logger.warning(f"Ollama {self.model_name} slow response: {response_time:.2f}s for {prompt_length} chars")
                
            return response
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Ollama {self.model_name} error after {response_time:.2f}s: {e}")
            raise
    
    def get_info(self) -> Dict[str, Any]:
        return {
            "provider": "Ollama",
            "type": "local",
            "model": self.model_name or (self.llm.model if self.llm else "unknown"),
            "requires_api_key": False
        }
    
    def count_tokens(self, text: str) -> int:
        """Estimate token count for Ollama models"""
        # Simple estimation: ~4 characters per token
        return len(text) // 4
    
    @staticmethod
    def get_available_models() -> List[str]:
        """Get list of available Ollama models"""
        try:
            from app.config import settings
            response = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            else:
                print(f"Failed to fetch Ollama models: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error fetching Ollama models: {e}")
            return []

class OpenAIProvider(BaseLLMProvider):
    def initialize(self, config: Dict[str, Any]):
        api_key = config.get("api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is required")
        
        self.api_key = api_key
        self.model = config.get("model", "gpt-4")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 2048)
        
        print(f"OpenAI provider initialized with key: {api_key[:15]}...")
        
    def generate(self, prompt: str, **kwargs) -> str:
        import time
        import logging
        
        logger = logging.getLogger(__name__)
        start_time = time.time()
        
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=self.api_key,
                timeout=120.0  # 2 minute timeout
            )
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            response_time = time.time() - start_time
            logger.info(f"OpenAI {self.model} - Response: {response_time:.2f}s")
            
            if response_time > 30.0:
                logger.warning(f"OpenAI {self.model} slow response: {response_time:.2f}s")
            
            return response.choices[0].message.content
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"OpenAI {self.model} error after {response_time:.2f}s: {e}")
            
            if "timeout" in str(e).lower() or "timed out" in str(e).lower():
                raise ValueError(f"OpenAI API timeout after 2 minutes: {str(e)}")
            elif "authentication" in str(e).lower() or "api key" in str(e).lower():
                raise ValueError(f"Invalid OpenAI API key: {str(e)}")
            elif "rate limit" in str(e).lower():
                raise ValueError(f"OpenAI rate limit exceeded: {str(e)}")
            else:
                raise ValueError(f"OpenAI API error: {str(e)}")
    
    def get_info(self) -> Dict[str, Any]:
        return {
            "provider": "OpenAI",
            "type": "online",
            "model": self.model,
            "requires_api_key": True,
            "status": "configured"
        }
    
    def count_tokens(self, text: str) -> int:
        """Estimate token count for OpenAI models"""
        # Simple estimation: ~4 characters per token
        return len(text) // 4

class AnthropicProvider(BaseLLMProvider):
    def initialize(self, config: Dict[str, Any]):
        api_key = config.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Anthropic API key is required")
        
        # Store API key for validation but don't initialize LangChain yet
        # This avoids the count_tokens issue during provider setup
        self.api_key = api_key
        self.model = config.get("model", "claude-3-opus-20240229")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 2048)
        
        # Simple API key format validation
        if not api_key.startswith("sk-ant-"):
            raise ValueError("Invalid Anthropic API key format")
        
        print(f"Anthropic provider initialized with key: {api_key[:15]}...")
        
    def generate(self, prompt: str, **kwargs) -> str:
        import time
        import logging
        import httpx
        
        logger = logging.getLogger(__name__)
        start_time = time.time()
        
        try:
            # Create client with timeout configuration
            client = anthropic.Anthropic(
                api_key=self.api_key,
                timeout=httpx.Timeout(120.0, connect=10.0)  # 2 minute timeout, 10 second connect
            )
            
            response = client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_time = time.time() - start_time
            logger.info(f"Anthropic {self.model} - Response: {response_time:.2f}s")
            
            if response_time > 30.0:
                logger.warning(f"Anthropic {self.model} slow response: {response_time:.2f}s")
            
            return response.content[0].text
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Anthropic {self.model} error after {response_time:.2f}s: {e}")
            
            # Return proper error messages for API issues
            if "timeout" in str(e).lower() or "timed out" in str(e).lower():
                raise ValueError(f"Anthropic API timeout after 2 minutes: {str(e)}")
            elif "authentication" in str(e).lower() or "api key" in str(e).lower():
                raise ValueError(f"Invalid Anthropic API key: {str(e)}")
            elif "rate limit" in str(e).lower():
                raise ValueError(f"Anthropic rate limit exceeded: {str(e)}")
            else:
                raise ValueError(f"Anthropic API error: {str(e)}")
    
    def get_info(self) -> Dict[str, Any]:
        return {
            "provider": "Anthropic",
            "type": "online", 
            "model": self.model,
            "requires_api_key": True,
            "status": "configured"
        }
    
    def count_tokens(self, text: str) -> int:
        """Estimate token count for Anthropic models"""
        # Simple estimation: ~4 characters per token
        return len(text) // 4

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
        self.deactivated_models: Dict[str, bool] = {}  # Track deactivated models
        self._initialize_providers()
        
    def _initialize_providers(self):
        """Initialize all configured providers"""
        # Initialize Ollama providers dynamically for each available model
        try:
            from app.config import settings  # Import here to avoid circular imports
            available_models = OllamaProvider.get_available_models()
            
            if available_models:
                # Initialize each available model as a separate provider
                for model_name in available_models:
                    try:
                        ollama_provider = OllamaProvider()
                        ollama_provider.initialize({"model": model_name})
                        provider_key = f"ollama-{model_name.replace(':', '_').replace('.', '_')}"
                        self.providers[provider_key] = ollama_provider
                        
                        # Set default active provider to the configured model or first available
                        if model_name == settings.LLM_MODEL_NAME:
                            self.active_provider = provider_key
                        elif self.active_provider is None:  # First model as fallback
                            self.active_provider = provider_key
                    except Exception as e:
                        print(f"Failed to initialize Ollama model {model_name}: {e}")
            else:
                # Fallback: initialize with the configured model name even if not detected
                ollama_provider = OllamaProvider()
                ollama_provider.initialize({"model": settings.LLM_MODEL_NAME})
                provider_key = f"ollama-{settings.LLM_MODEL_NAME.replace(':', '_').replace('.', '_')}"
                self.providers[provider_key] = ollama_provider
                self.active_provider = provider_key
        except Exception as e:
            print(f"Failed to initialize Ollama providers: {e}")
            
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
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of all available models grouped by provider type"""
        models = []
        
        # Ollama models
        ollama_models = []
        for name, provider in self.providers.items():
            if name.startswith("ollama-"):
                model_name = provider.get_info().get("model", "unknown")
                is_deactivated = self.deactivated_models.get(name, False)
                ollama_models.append({
                    "provider_key": name,
                    "model_name": model_name,
                    "display_name": model_name,
                    "active": name == self.active_provider,
                    "is_deactivated": is_deactivated
                })
        
        if ollama_models:
            models.append({
                "provider_type": "ollama",
                "provider_name": "Ollama (Local)",
                "models": ollama_models
            })
        
        # Online models
        online_models = []
        for name, provider in self.providers.items():
            if not name.startswith("ollama-"):
                info = provider.get_info()
                is_deactivated = self.deactivated_models.get(name, False)
                online_models.append({
                    "provider_key": name,
                    "model_name": info.get("model", "unknown"),
                    "display_name": f"{info.get('provider', 'Unknown')} - {info.get('model', 'unknown')}",
                    "active": name == self.active_provider,
                    "is_deactivated": is_deactivated
                })
        
        if online_models:
            models.append({
                "provider_type": "online",
                "provider_name": "Cloud Models",
                "models": online_models
            })
            
        return models
    
    def get_active_models(self) -> List[Dict[str, Any]]:
        """Get list of only active (non-deactivated) models for chat sessions"""
        all_models = self.get_available_models()
        active_models = []
        
        for provider_group in all_models:
            active_provider_models = []
            for model in provider_group["models"]:
                if not model.get("is_deactivated", False):
                    active_provider_models.append(model)
            
            if active_provider_models:
                provider_group_copy = provider_group.copy()
                provider_group_copy["models"] = active_provider_models
                active_models.append(provider_group_copy)
        
        return active_models
    
    def deactivate_model(self, model_key: str, deactivated: bool = True) -> bool:
        """Deactivate/activate a specific model"""
        if model_key in self.providers:
            self.deactivated_models[model_key] = deactivated
            
            # If deactivating the active provider, switch to a non-deactivated one
            if deactivated and model_key == self.active_provider:
                for provider_key in self.providers.keys():
                    if not self.deactivated_models.get(provider_key, False):
                        self.active_provider = provider_key
                        break
                else:
                    self.active_provider = None  # No active providers available
            
            return True
        return False
    
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
    
    # Admin API Key Management Methods
    
    def _has_api_key(self, provider_name: str) -> bool:
        """Check if provider has API key available"""
        from app.config import settings
        
        api_key_map = {
            "openai": settings.OPENAI_API_KEY,
            "anthropic": settings.ANTHROPIC_API_KEY,
            "google": settings.GOOGLE_API_KEY,
            "cohere": settings.COHERE_API_KEY,
        }
        
        key = api_key_map.get(provider_name.lower())
        return key is not None and len(key.strip()) > 0
    
    def add_api_key(self, provider_name: str, api_key: str) -> bool:
        """Dynamically add API key and initialize provider"""
        try:
            provider_name = provider_name.lower()
            
            # Update settings (in-memory for this session)
            from app.config import settings
            if provider_name == "openai":
                settings.OPENAI_API_KEY = api_key
                provider_class = OpenAIProvider
            elif provider_name == "anthropic":
                settings.ANTHROPIC_API_KEY = api_key
                provider_class = AnthropicProvider
            elif provider_name == "google":
                settings.GOOGLE_API_KEY = api_key
                provider_class = GoogleProvider
            elif provider_name == "cohere":
                settings.COHERE_API_KEY = api_key
                provider_class = CoherProvider
            else:
                return False
            
            # Initialize the provider
            print(f"🔍 Creating provider instance: {provider_class}")
            provider_instance = provider_class()
            print(f"🔍 Provider instance created: {type(provider_instance)}")
            print(f"🔍 Initializing with API key...")
            provider_instance.initialize({"api_key": api_key})
            # Check if provider has llm attribute (some use lazy loading)
            if hasattr(provider_instance, 'llm'):
                print(f"🔍 Provider initialized. LLM type: {type(provider_instance.llm)}")
            else:
                print(f"🔍 Provider initialized. Using lazy loading for LLM.")
            
            # Add to active providers
            self.providers[provider_name] = provider_instance
            
            # Sync to database
            # self._sync_provider_to_db(provider_name, provider_instance)  # Temporarily disabled for debugging
            
            print(f"Added {provider_name} provider with API key")
            return True
            
        except Exception as e:
            print(f"Failed to add {provider_name} provider: {e}")
            return False
    
    def remove_api_key(self, provider_name: str) -> bool:
        """Remove API key and deactivate provider"""
        try:
            provider_name = provider_name.lower()
            
            # Update settings (in-memory for this session)
            from app.config import settings
            if provider_name == "openai":
                settings.OPENAI_API_KEY = None
            elif provider_name == "anthropic":
                settings.ANTHROPIC_API_KEY = None
            elif provider_name == "google":
                settings.GOOGLE_API_KEY = None
            elif provider_name == "cohere":
                settings.COHERE_API_KEY = None
            else:
                return False
            
            # Remove from active providers
            if provider_name in self.providers:
                del self.providers[provider_name]
            
            # If this was the active provider, switch to ollama
            if self.active_provider == provider_name:
                self.active_provider = "ollama"
            
            print(f"Removed {provider_name} provider")
            return True
            
        except Exception as e:
            print(f"Failed to remove {provider_name} provider: {e}")
            return False
    
    def _sync_provider_to_db(self, provider_name: str, provider_instance):
        """Helper to sync individual provider to database"""
        try:
            from app.core.database import SessionLocal
            from app.models.llm_config import LLMProvider
            
            db = SessionLocal()
            try:
                # Check if provider already exists
                existing = db.query(LLMProvider).filter(LLMProvider.name == provider_name).first()
                
                if not existing:
                    # Create new provider entry
                    provider_info = provider_instance.get_info()
                    new_provider = LLMProvider(
                        name=provider_name,
                        type=provider_info.get("type", "unknown"),
                        is_active=True,
                        config=provider_info
                    )
                    db.add(new_provider)
                    db.commit()
                    print(f"📝 Synced {provider_name} to database")
                    
            finally:
                db.close()
                
        except Exception as e:
            print(f"⚠️ Failed to sync {provider_name} to database: {e}")

# Singleton instance
multi_llm_manager = MultiProviderLLMManager()