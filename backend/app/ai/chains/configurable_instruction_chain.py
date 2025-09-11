# app/ai/chains/configurable_instruction_chain.py
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from app.ai.multi_llm_manager import multi_llm_manager
from app.models.llm_config import LLMConfig
from sqlalchemy.orm import Session
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class ConfigurableInstructionProcessor:
    """Instruction processor that uses saved configurations"""
    
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
    
    def get_config_for_mode(self, mode: str) -> Optional[LLMConfig]:
        """Get saved configuration for a specific mode"""
        return self.db.query(LLMConfig).filter(
            LLMConfig.name == f"{mode}_mode",
            LLMConfig.created_by == self.user_id
        ).first()
    
    def process_with_mode(self, instruction: str, mode: str = "practice", provider: str = None) -> str:
        """Process instruction using mode-specific configuration"""
        config = self.get_config_for_mode(mode)
        
        if config:
            system_prompt = config.system_prompt
            temperature = config.temperature
            max_tokens = config.max_tokens
        else:
            # Use defaults
            if mode == "practice":
                system_prompt = """You are LearnoBot, an AI assistant designed to help students with learning disabilities.
                Be patient, encouraging, and break down complex instructions into simple steps."""
                temperature = 0.7
                max_tokens = 2048
            else:  # test mode
                system_prompt = """You are in test mode. Provide minimal assistance only.
                Maximum 3 attempts to help."""
                temperature = 0.5
                max_tokens = 1024
        
        # Construct full prompt
        full_prompt = f"{system_prompt}\n\nStudent question: {instruction}"
        
        # Generate response using selected provider
        response = multi_llm_manager.generate(
            prompt=full_prompt,
            provider=provider,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response
