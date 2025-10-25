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
from langchain.chat_models import ChatGooglePalm
from langchain.schema import HumanMessage

# Cloud provider imports
import anthropic
import openai
import cohere
import google.generativeai as genai

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
            base_url=settings.OLLAMA_BASE_URL,
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
    
    def process_image(self, image_data: bytes, prompt: str, **kwargs) -> str:
        """Process image with vision using GPT-4 Vision"""
        import time
        import logging
        import base64
        
        logger = logging.getLogger(__name__)
        start_time = time.time()
        
        try:
            from openai import OpenAI
            
            # Convert image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            client = OpenAI(
                api_key=self.api_key,
                timeout=120.0
            )
            
            # Use GPT-4 Vision model
            vision_model = "gpt-4-vision-preview" if "gpt-4" in self.model else self.model
            
            response = client.chat.completions.create(
                model=vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            response_text = response.choices[0].message.content
            response_time = time.time() - start_time
            
            logger.info(f"OpenAI {vision_model} Vision - Response: {response_time:.2f}s")
            
            return response_text
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"OpenAI Vision error after {response_time:.2f}s: {e}")
            raise ValueError(f"OpenAI Vision API error: {str(e)}")
    
    def process_multiple_images(self, images_data: list, prompt: str, **kwargs) -> str:
        """Process multiple images with OpenAI vision"""
        import time
        import logging
        import base64
        
        logger = logging.getLogger(__name__)
        start_time = time.time()
        
        try:
            from openai import OpenAI
            
            client = OpenAI(
                api_key=self.api_key,
                timeout=120.0
            )
            
            # Use GPT-4 Vision model
            vision_model = "gpt-4-vision-preview" if "gpt-4" in self.model else self.model
            
            # Build content array with multiple images
            content = [{"type": "text", "text": prompt}]
            
            for img_data in images_data:
                base64_image = base64.b64encode(img_data).decode('utf-8')
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                })
            
            response = client.chat.completions.create(
                model=vision_model,
                messages=[{"role": "user", "content": content}],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            response_text = response.choices[0].message.content
            response_time = time.time() - start_time
            
            logger.info(f"OpenAI {vision_model} Multi-Vision - Response: {response_time:.2f}s")
            
            return response_text
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"OpenAI Multi-Vision error after {response_time:.2f}s: {e}")
            raise ValueError(f"OpenAI Multi-Vision API error: {str(e)}")
    
    def get_info(self) -> Dict[str, Any]:
        return {
            "provider": "OpenAI",
            "type": "online",
            "model": self.model,
            "requires_api_key": True,
            "status": "configured",
            "supports_vision": True
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
    
    def process_image(self, image_data: bytes, prompt: str, **kwargs) -> str:
        """Process image with vision using Claude Vision"""
        import time
        import logging
        import httpx
        import base64
        
        logger = logging.getLogger(__name__)
        start_time = time.time()
        
        try:
            # Convert image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Detect image type
            if image_data.startswith(b'\xff\xd8\xff'):
                media_type = "image/jpeg"
            elif image_data.startswith(b'\x89PNG'):
                media_type = "image/png"
            elif image_data.startswith(b'GIF'):
                media_type = "image/gif"
            elif image_data.startswith(b'WEBP'):
                media_type = "image/webp"
            else:
                media_type = "image/jpeg"  # Default fallback
            
            client = anthropic.Anthropic(
                api_key=self.api_key,
                timeout=httpx.Timeout(120.0, connect=10.0)
            )
            
            response = client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )
            
            response_text = response.content[0].text
            response_time = time.time() - start_time
            
            logger.info(f"Anthropic {self.model} Vision - Response: {response_time:.2f}s")
            
            return response_text
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Anthropic Vision error after {response_time:.2f}s: {e}")
            raise ValueError(f"Anthropic Vision API error: {str(e)}")
    
    def process_multiple_images(self, images_data: list, prompt: str, **kwargs) -> str:
        """Process multiple images with Anthropic vision"""
        import time
        import logging
        import base64
        import anthropic
        import httpx
        
        logger = logging.getLogger(__name__)
        start_time = time.time()
        
        try:
            # Build content array with multiple images
            content = [{"type": "text", "text": prompt}]
            
            for img_data in images_data:
                image_base64 = base64.b64encode(img_data).decode('utf-8')
                
                # Detect image format
                if img_data.startswith(b'\xff\xd8\xff'):
                    media_type = "image/jpeg"
                elif img_data.startswith(b'\x89PNG'):
                    media_type = "image/png"
                elif img_data.startswith(b'GIF'):
                    media_type = "image/gif"
                elif img_data.startswith(b'WEBP'):
                    media_type = "image/webp"
                else:
                    media_type = "image/jpeg"  # Default fallback
                
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_base64
                    }
                })
            
            client = anthropic.Anthropic(
                api_key=self.api_key,
                timeout=httpx.Timeout(120.0, connect=10.0)
            )
            
            response = client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": content}]
            )
            
            response_text = response.content[0].text
            response_time = time.time() - start_time
            
            logger.info(f"Anthropic {self.model} Multi-Vision - Response: {response_time:.2f}s")
            
            return response_text
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Anthropic Multi-Vision error after {response_time:.2f}s: {e}")
            raise ValueError(f"Anthropic Multi-Vision API error: {str(e)}")
    
    def get_info(self) -> Dict[str, Any]:
        return {
            "provider": "Anthropic",
            "type": "online", 
            "model": self.model,
            "requires_api_key": True,
            "status": "configured",
            "supports_vision": True
        }
    
    def count_tokens(self, text: str) -> int:
        """Estimate token count for Anthropic models"""
        # Simple estimation: ~4 characters per token
        return len(text) // 4

class CohereProvider(BaseLLMProvider):
    def initialize(self, config: Dict[str, Any]):
        api_key = config.get("api_key") or os.getenv("COHERE_API_KEY")
        if not api_key:
            raise ValueError("Cohere API key is required")
        
        self.api_key = api_key
        self.model = config.get("model", "command")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 2048)
        
        # Initialize Cohere client
        self.client = cohere.Client(api_key)
        
        print(f"Cohere provider initialized with model: {self.model}")
        
    def generate(self, prompt: str, **kwargs) -> str:
        import time
        import logging
        
        logger = logging.getLogger(__name__)
        start_time = time.time()
        
        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            response_time = time.time() - start_time
            logger.info(f"Cohere {self.model} - Response: {response_time:.2f}s")
            
            if response_time > 30.0:
                logger.warning(f"Cohere {self.model} slow response: {response_time:.2f}s")
            
            return response.generations[0].text
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Cohere {self.model} error after {response_time:.2f}s: {e}")
            
            if "timeout" in str(e).lower() or "timed out" in str(e).lower():
                raise ValueError(f"Cohere API timeout: {str(e)}")
            elif "authentication" in str(e).lower() or "api key" in str(e).lower():
                raise ValueError(f"Invalid Cohere API key: {str(e)}")
            elif "rate limit" in str(e).lower():
                raise ValueError(f"Cohere rate limit exceeded: {str(e)}")
            else:
                raise ValueError(f"Cohere API error: {str(e)}")
    
    def get_info(self) -> Dict[str, Any]:
        return {
            "provider": "Cohere",
            "type": "online",
            "model": self.model,
            "requires_api_key": True,
            "status": "configured"
        }
    
    def count_tokens(self, text: str) -> int:
        """Estimate token count for Cohere models"""
        # Simple estimation: ~4 characters per token
        return len(text) // 4

class GoogleProvider(BaseLLMProvider):
    def initialize(self, config: Dict[str, Any]):
        api_key = config.get("api_key") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Google API key is required")
        
        self.api_key = api_key
        # Default to gemini-2.5-flash (latest stable fast model)
        self.model = config.get("model", "gemini-2.5-flash")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 2048)
        
        # Use the newer Google AI SDK (recommended by Google)
        try:
            import google.generativeai as genai
            
            # Configure with API key
            genai.configure(api_key=api_key)
            
            # Map old model names to new Gemini 2.x models (as of 2025)
            # Google completely deprecated 1.5 models - now using 2.x series
            model_mapping = {
                "gemini-1.5-pro": "models/gemini-2.5-pro",
                "gemini-1.5-flash": "models/gemini-2.5-flash",
                "gemini-pro": "models/gemini-2.5-pro",
                "gemini-flash": "models/gemini-2.5-flash",
                "gemini-2.5-pro": "models/gemini-2.5-pro",
                "gemini-2.5-flash": "models/gemini-2.5-flash",
                "gemini-2.0-flash": "models/gemini-2.0-flash",
            }
            
            # Get model name with 'models/' prefix (required by new API)
            model_name = model_mapping.get(self.model, "models/gemini-2.5-flash")
            
            # Ensure models/ prefix
            if not model_name.startswith("models/"):
                model_name = f"models/{model_name}"
                
            self.client = genai.GenerativeModel(model_name)
            self.actual_model = model_name  # Store actual model name
            
            print(f"✅ Google AI SDK initialized with model: {model_name}")
            
        except Exception as e:
            print(f"Google AI SDK initialization failed: {e}")
            print("This might be due to API restrictions. Please check your Google Cloud Console settings.")
            raise ValueError(f"Failed to initialize Google provider: {e}")
        
    def generate(self, prompt: str, **kwargs) -> str:
        import time
        import logging
        
        logger = logging.getLogger(__name__)
        start_time = time.time()
        
        try:
            # Use Google AI SDK
            import google.generativeai as genai
            
            generation_config = genai.types.GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
            )
            
            response = self.client.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            # Handle multi-part responses (structured content)
            try:
                response_text = response.text
            except ValueError:
                # Response has multiple parts, concatenate them
                response_text = ""
                for candidate in response.candidates:
                    for part in candidate.content.parts:
                        response_text += part.text
            
            response_time = time.time() - start_time
            actual_model = getattr(self, 'actual_model', self.model)
            logger.info(f"Google {actual_model} - Response: {response_time:.2f}s")
            
            if response_time > 30.0:
                logger.warning(f"Google {actual_model} slow response: {response_time:.2f}s")
            
            return response_text
            
        except Exception as e:
            response_time = time.time() - start_time
            actual_model = getattr(self, 'actual_model', self.model)
            logger.error(f"Google {actual_model} error after {response_time:.2f}s: {e}")
            
            if "timeout" in str(e).lower() or "timed out" in str(e).lower():
                raise ValueError(f"Google API timeout: {str(e)}")
            elif "authentication" in str(e).lower() or "api key" in str(e).lower():
                raise ValueError(f"Invalid Google API key: {str(e)}")
            elif "rate limit" in str(e).lower():
                raise ValueError(f"Google rate limit exceeded: {str(e)}")
            else:
                raise ValueError(f"Google API error: {str(e)}")
    
    def process_image(self, image_data: bytes, prompt: str, **kwargs) -> str:
        """Process image with vision using Google Gemini"""
        import time
        import logging
        import base64
        
        logger = logging.getLogger(__name__)
        start_time = time.time()
        
        try:
            import google.generativeai as genai
            from PIL import Image
            import io
            
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Use vision-capable model configuration
            generation_config = genai.types.GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
            )
            
            # Create vision prompt with image
            response = self.client.generate_content(
                [prompt, image],
                generation_config=generation_config
            )
            
            # Handle multi-part responses (structured content)
            try:
                response_text = response.text
            except ValueError:
                # Response has multiple parts, concatenate them
                response_text = ""
                for candidate in response.candidates:
                    for part in candidate.content.parts:
                        response_text += part.text
            response_time = time.time() - start_time
            
            actual_model = getattr(self, 'actual_model', self.model)
            logger.info(f"Google {actual_model} Vision - Response: {response_time:.2f}s")
            
            return response_text
            
        except Exception as e:
            response_time = time.time() - start_time
            actual_model = getattr(self, 'actual_model', self.model)
            logger.error(f"Google {actual_model} Vision error after {response_time:.2f}s: {e}")
            raise ValueError(f"Google Vision API error: {str(e)}")
    
    def process_multiple_images(self, images_data: list, prompt: str, **kwargs) -> str:
        """Process multiple images with Google vision"""
        import time
        import logging
        import PIL.Image
        import io
        
        logger = logging.getLogger(__name__)
        start_time = time.time()
        
        try:
            import google.generativeai as genai
            
            # Convert images to PIL Images
            pil_images = []
            for img_data in images_data:
                pil_images.append(PIL.Image.open(io.BytesIO(img_data)))
            
            # Build content with text and multiple images
            content = [prompt] + pil_images
            
            generation_config = genai.types.GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
            )
            
            response = self.client.generate_content(
                content,
                generation_config=generation_config
            )
            
            # Handle multi-part responses (structured content)
            try:
                response_text = response.text
            except ValueError:
                # Response has multiple parts, concatenate them
                response_text = ""
                for candidate in response.candidates:
                    for part in candidate.content.parts:
                        response_text += part.text
            
            response_time = time.time() - start_time
            actual_model = getattr(self, 'actual_model', self.model)
            logger.info(f"Google {actual_model} Multi-Vision - Response: {response_time:.2f}s")
            
            return response_text
            
        except Exception as e:
            response_time = time.time() - start_time
            actual_model = getattr(self, 'actual_model', self.model)
            logger.error(f"Google {actual_model} Multi-Vision error after {response_time:.2f}s: {e}")
            raise ValueError(f"Google Multi-Vision API error: {str(e)}")
    
    def get_info(self) -> Dict[str, Any]:
        return {
            "provider": "Google",
            "type": "online",
            "model": self.model,
            "requires_api_key": True,
            "status": "configured",
            "supports_vision": True
        }
    
    def count_tokens(self, text: str) -> int:
        """Estimate token count for Google models"""
        # Simple estimation: ~4 characters per token
        return len(text) // 4

class MultiProviderLLMManager:
    """Manages multiple LLM providers for testing and comparison"""
    
    def __init__(self):
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.active_provider: Optional[str] = None
        self.deactivated_models: Dict[str, bool] = {}  # Track deactivated models
        self._initialize_providers()
        
    def _initialize_providers(self):
        """Initialize all configured providers - DATABASE FIRST, then .env fallback for first-time setup"""
        from app.config import settings  # Import here to avoid circular imports
        from app.core.database import SessionLocal
        from app.models.llm_config import LLMProvider as LLMProviderDB

        # Step 1: Load DB state FIRST to check which providers should be active
        db = SessionLocal()
        db_providers_map = {}
        try:
            db_providers = db.query(LLMProviderDB).filter(LLMProviderDB.type == "cloud").all()
            db_providers_map = {p.name.lower(): p for p in db_providers}
            print(f"🔍 Loaded {len(db_providers_map)} cloud providers from database")
        except Exception as e:
            print(f"⚠️  Could not load providers from database: {e}")
        finally:
            db.close()

        # Step 2: Initialize Ollama providers (always available, no API key needed)
        try:
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

        # Step 3: Initialize cloud providers - DATABASE PRECEDENCE ENFORCED
        # Only initialize if:
        # 1. DB has NO record (first time setup from .env)
        # 2. DB has record WITH api_key AND is_active=True AND is_deactivated=False

        # OpenAI
        if settings.OPENAI_API_KEY:
            db_provider = db_providers_map.get("openai")
            should_initialize = False

            if db_provider is None:
                # First time setup - .env takes precedence
                print(f"🆕 OpenAI: No DB record found, initializing from .env (first-time setup)")
                should_initialize = True
            elif db_provider.api_key is None or db_provider.is_deactivated:
                # DB says "deleted" - IGNORE .env
                print(f"🚫 OpenAI: DB says deactivated/deleted, ignoring .env key")
                settings.OPENAI_API_KEY = None  # Clear from settings
                should_initialize = False
            else:
                # DB has key - it will be loaded in main.py startup
                print(f"✅ OpenAI: Will be loaded from database")
                should_initialize = False

            if should_initialize:
                try:
                    openai_provider = OpenAIProvider()
                    openai_provider.initialize({"api_key": settings.OPENAI_API_KEY})
                    self.providers["openai"] = openai_provider
                except Exception as e:
                    print(f"Failed to initialize OpenAI: {e}")

        # Anthropic
        if settings.ANTHROPIC_API_KEY:
            db_provider = db_providers_map.get("anthropic")
            should_initialize = False

            if db_provider is None:
                print(f"🆕 Anthropic: No DB record found, initializing from .env (first-time setup)")
                should_initialize = True
            elif db_provider.api_key is None or db_provider.is_deactivated:
                print(f"🚫 Anthropic: DB says deactivated/deleted, ignoring .env key")
                settings.ANTHROPIC_API_KEY = None
                should_initialize = False
            else:
                print(f"✅ Anthropic: Will be loaded from database")
                should_initialize = False

            if should_initialize:
                try:
                    anthropic_provider = AnthropicProvider()
                    anthropic_provider.initialize({"api_key": settings.ANTHROPIC_API_KEY})
                    self.providers["anthropic"] = anthropic_provider
                except Exception as e:
                    print(f"Failed to initialize Anthropic: {e}")

        # Google - handle multiple model variants with DB precedence
        if settings.GOOGLE_API_KEY:
            # Check DB for ANY Google model variant
            google_model_keys = [
                "google-gemini_2_5_flash",
                "google-gemini_2_5_pro",
                "google-gemini_2_0_flash",
            ]

            # Check if any Google model exists in DB
            any_google_in_db = any(key in db_providers_map for key in google_model_keys)
            any_google_deactivated = False

            if any_google_in_db:
                # Check if ALL are deactivated
                any_google_deactivated = all(
                    db_providers_map.get(key) and
                    (db_providers_map[key].api_key is None or db_providers_map[key].is_deactivated)
                    for key in google_model_keys
                    if key in db_providers_map
                )

            should_initialize = False

            if not any_google_in_db:
                # First time setup
                print(f"🆕 Google: No DB records found, initializing from .env (first-time setup)")
                should_initialize = True
            elif any_google_deactivated:
                # All Google models deactivated
                print(f"🚫 Google: DB says all models deactivated/deleted, ignoring .env key")
                settings.GOOGLE_API_KEY = None
                should_initialize = False
            else:
                # Google models will be loaded from DB
                print(f"✅ Google: Will be loaded from database")
                should_initialize = False

            if should_initialize:
                # Initialize multiple Google models (like Ollama does)
                google_models = [
                    ("gemini-2.5-flash", "Google Gemini 2.5 Flash"),
                    ("gemini-2.5-pro", "Google Gemini 2.5 Pro"),
                    ("gemini-2.0-flash", "Google Gemini 2.0 Flash"),
                ]

                for model_key, display_name in google_models:
                    try:
                        google_provider = GoogleProvider()
                        google_provider.initialize({
                            "api_key": settings.GOOGLE_API_KEY,
                            "model": model_key
                        })
                        provider_key = f"google-{model_key.replace('.', '_').replace('-', '_')}"
                        self.providers[provider_key] = google_provider
                        print(f"✅ Initialized {display_name}")
                    except Exception as e:
                        print(f"Failed to initialize {display_name}: {e}")

        # Cohere
        if settings.COHERE_API_KEY:
            db_provider = db_providers_map.get("cohere")
            should_initialize = False

            if db_provider is None:
                print(f"🆕 Cohere: No DB record found, initializing from .env (first-time setup)")
                should_initialize = True
            elif db_provider.api_key is None or db_provider.is_deactivated:
                print(f"🚫 Cohere: DB says deactivated/deleted, ignoring .env key")
                settings.COHERE_API_KEY = None
                should_initialize = False
            else:
                print(f"✅ Cohere: Will be loaded from database")
                should_initialize = False

            if should_initialize:
                try:
                    cohere_provider = CohereProvider()
                    cohere_provider.initialize({"api_key": settings.COHERE_API_KEY})
                    self.providers["cohere"] = cohere_provider
                except Exception as e:
                    print(f"Failed to initialize Cohere: {e}")
    
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
        
        # Google models (separate group like Ollama)
        google_models = []
        for name, provider in self.providers.items():
            if name.startswith("google-") or name == "google":
                info = provider.get_info()
                is_deactivated = self.deactivated_models.get(name, False)
                model_name = info.get("model", "unknown")
                
                # Skip the backward compatibility "google" key in the list
                if name == "google":
                    continue
                    
                # Create clean display names
                display_name = model_name.replace("models/", "").replace("gemini-", "Gemini ")
                
                google_models.append({
                    "provider_key": name,
                    "model_name": model_name,
                    "display_name": display_name,
                    "active": name == self.active_provider,
                    "is_deactivated": is_deactivated
                })
        
        if google_models:
            models.append({
                "provider_type": "google",
                "provider_name": "Google Gemini",
                "models": google_models
            })
        
        # Other online models (OpenAI, Anthropic, Cohere)
        online_models = []
        for name, provider in self.providers.items():
            if not name.startswith("ollama-") and not name.startswith("google-") and name != "google":
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
                "provider_name": "Other Cloud Models",
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
                provider_class = CohereProvider
            else:
                return False

            # Encrypt API key before storing in database
            from app.core.encryption import get_encryption_service
            try:
                encryption_service = get_encryption_service()
                encrypted_key = encryption_service.encrypt(api_key)
            except RuntimeError:
                # Encryption service not initialized - store plain text (dev mode)
                print("⚠️  Encryption service not available - storing API key in plain text")
                encrypted_key = api_key

            # Store encrypted API key in database
            from app.core.database import SessionLocal
            from app.models.llm_config import LLMProvider

            db = SessionLocal()
            try:
                # For Google provider, we need to handle multiple model variants
                if provider_name == "google":
                    # Store all Google model variants in DB
                    google_models = [
                        "google-gemini_2_5_flash",
                        "google-gemini_2_5_pro",
                        "google-gemini_2_0_flash",
                    ]

                    for model_key in google_models:
                        provider_db = db.query(LLMProvider).filter(
                            LLMProvider.name == model_key
                        ).first()

                        if provider_db:
                            # Update existing provider
                            provider_db.api_key = encrypted_key
                            provider_db.is_active = True
                            provider_db.is_deactivated = False
                        else:
                            # Create new provider entry
                            provider_db = LLMProvider(
                                name=model_key,
                                type="cloud",
                                is_active=True,
                                is_deactivated=False,
                                api_key=encrypted_key
                            )
                            db.add(provider_db)

                    db.commit()
                    print(f"✅ Stored encrypted API key for all Google models in database")
                else:
                    # Single provider (OpenAI, Anthropic, Cohere)
                    provider_db = db.query(LLMProvider).filter(
                        LLMProvider.name == provider_name
                    ).first()

                    if provider_db:
                        # Update existing provider
                        provider_db.api_key = encrypted_key
                        provider_db.is_active = True
                        provider_db.is_deactivated = False
                    else:
                        # Create new provider entry
                        provider_db = LLMProvider(
                            name=provider_name,
                            type="cloud",
                            is_active=True,
                            is_deactivated=False,
                            api_key=encrypted_key
                        )
                        db.add(provider_db)

                    db.commit()
                    print(f"✅ Stored encrypted API key for {provider_name} in database")
            finally:
                db.close()

            # Store in Secret Manager if enabled
            if settings.USE_SECRET_MANAGER:
                self._store_secret_in_manager(provider_name, api_key)

            # Initialize provider instances (in-memory only)
            if provider_name == "google":
                # Initialize multiple Google models (like startup does)
                google_models = [
                    ("gemini-2.5-flash", "Google Gemini 2.5 Flash"),
                    ("gemini-2.5-pro", "Google Gemini 2.5 Pro"),
                    ("gemini-2.0-flash", "Google Gemini 2.0 Flash"),
                ]

                for model_key, display_name in google_models:
                    try:
                        google_provider = GoogleProvider()
                        google_provider.initialize({
                            "api_key": api_key,
                            "model": model_key
                        })
                        provider_key = f"google-{model_key.replace('.', '_').replace('-', '_')}"
                        self.providers[provider_key] = google_provider
                        print(f"✅ Initialized {display_name}")
                    except Exception as e:
                        print(f"⚠️  Failed to initialize {display_name}: {e}")

                print(f"✅ Added Google provider with {len(google_models)} model variants")
            else:
                # Single provider initialization
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

                print(f"✅ Added {provider_name} provider with API key")

            return True

        except Exception as e:
            print(f"❌ Failed to add {provider_name} provider: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def remove_api_key(self, provider_name: str) -> bool:
        """Remove API key but keep provider row in database"""
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

            # Update provider in database - keep row but mark inactive
            from app.core.database import SessionLocal
            from app.models.llm_config import LLMProvider

            db = SessionLocal()
            try:
                if provider_name == "google":
                    # Handle all Google model variants
                    google_models = [
                        "google-gemini_2_5_flash",
                        "google-gemini_2_5_pro",
                        "google-gemini_2_0_flash",
                    ]

                    for model_key in google_models:
                        provider_db = db.query(LLMProvider).filter(
                            LLMProvider.name == model_key
                        ).first()

                        if provider_db:
                            # Keep provider row but clear key and mark inactive
                            provider_db.api_key = None
                            provider_db.is_active = False
                            provider_db.is_deactivated = True

                        # Remove from active providers (in-memory)
                        if model_key in self.providers:
                            del self.providers[model_key]

                        # If this was the active provider, switch to a non-deactivated one
                        if self.active_provider == model_key:
                            for provider_key in self.providers.keys():
                                if not self.deactivated_models.get(provider_key, False):
                                    self.active_provider = provider_key
                                    break
                            else:
                                self.active_provider = None

                    db.commit()
                    print(f"✅ Cleared API key for all Google models and marked inactive")
                else:
                    # Single provider
                    provider_db = db.query(LLMProvider).filter(
                        LLMProvider.name == provider_name
                    ).first()

                    if provider_db:
                        # Keep provider row but clear key and mark inactive
                        provider_db.api_key = None
                        provider_db.is_active = False
                        provider_db.is_deactivated = True
                        db.commit()
                        print(f"✅ Cleared {provider_name} API key and marked inactive")
                    else:
                        print(f"⚠️ Provider {provider_name} not found in database")

                    # Remove from active providers
                    if provider_name in self.providers:
                        del self.providers[provider_name]

                    # If this was the active provider, switch to a non-deactivated one
                    if self.active_provider == provider_name:
                        for provider_key in self.providers.keys():
                            if not self.deactivated_models.get(provider_key, False):
                                self.active_provider = provider_key
                                break
                        else:
                            self.active_provider = None

            finally:
                db.close()

            # Note: We use Fernet encryption for API keys in database, not Secret Manager

            print(f"✅ Deactivated {provider_name} provider (kept in database)")
            return True

        except Exception as e:
            print(f"❌ Failed to remove {provider_name} provider: {e}")
            return False
    
    def _store_secret_in_manager(self, provider_name: str, api_key: str):
        """Store API key in Google Secret Manager"""
        try:
            from app.services.secrets_service import secrets_service
            
            secret_name = f"{provider_name}-api-key"
            success = secrets_service.update_secret(secret_name, api_key)
            
            if not success:
                # Try to create if update failed
                success = secrets_service.create_secret(secret_name, api_key)
            
            if success:
                print(f"✅ Stored {provider_name} API key in Secret Manager")
            else:
                print(f"⚠️ Failed to store {provider_name} API key in Secret Manager")
                
        except Exception as e:
            print(f"⚠️ Error storing secret in Secret Manager: {e}")
    
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