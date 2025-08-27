# app/ai/llm_manager.py
from langchain.llms import LlamaCpp, GPT4All, Ollama
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.embeddings import HuggingFaceEmbeddings
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class LLMManager:
    def __init__(self):
        self.llm = None
        self.embeddings = None
        self._initialize_llm()
        self._initialize_embeddings()
    
    def _initialize_llm(self):
        """Initialize the local LLM based on configuration"""
        callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
        
        if settings.LLM_TYPE == "llamacpp":
            # Using LlamaCpp for local Llama models
            self.llm = LlamaCpp(
                model_path=settings.LLM_MODEL_PATH,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
                n_ctx=2048,
                callback_manager=callback_manager,
                verbose=True,
            )
        elif settings.LLM_TYPE == "gpt4all":
            # Using GPT4All for local models
            self.llm = GPT4All(
                model=settings.LLM_MODEL_PATH,
                max_tokens=settings.LLM_MAX_TOKENS,
                temp=settings.LLM_TEMPERATURE,
                callback_manager=callback_manager,
            )
        elif settings.LLM_TYPE == "ollama":
            # Using Ollama for local models
            self.llm = Ollama(
                model=settings.LLM_MODEL_NAME,  # Use configured model
                temperature=settings.LLM_TEMPERATURE,
                callback_manager=callback_manager,
            )
        else:
            raise ValueError(f"Unsupported LLM type: {settings.LLM_TYPE}")
        
        logger.info(f"Initialized {settings.LLM_TYPE} LLM")
    
    def _initialize_embeddings(self):
        """Initialize embeddings for semantic search if needed"""
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
    
    def get_llm(self):
        return self.llm
    
    def get_embeddings(self):
        return self.embeddings

# Singleton instance
llm_manager = LLMManager()