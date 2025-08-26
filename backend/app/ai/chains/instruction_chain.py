# app/ai/chains/instruction_chain.py
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from app.ai.llm_manager import llm_manager
from app.ai.prompts.base_prompts import (
    INSTRUCTION_ANALYSIS_PROMPT,
    PRACTICE_BREAKDOWN_PROMPT,
    PRACTICE_EXAMPLE_PROMPT,
    PRACTICE_EXPLAIN_PROMPT
)
import logging

logger = logging.getLogger(__name__)

class InstructionProcessor:
    def __init__(self):
        self.llm = llm_manager.get_llm()
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
    
    def analyze_instruction(self, instruction: str, student_context: dict) -> dict:
        """Analyze an instruction to understand what needs to be done"""
        chain = LLMChain(
            llm=self.llm,
            prompt=INSTRUCTION_ANALYSIS_PROMPT,
            verbose=True
        )
        
        result = chain.run(
            instruction=instruction,
            student_context=str(student_context)
        )
        
        return {"analysis": result}
    
    def breakdown_instruction(self, instruction: str, student_level: int) -> str:
        """Break down instruction into simple steps"""
        chain = LLMChain(
            llm=self.llm,
            prompt=PRACTICE_BREAKDOWN_PROMPT,
            verbose=True
        )
        
        return chain.run(
            instruction=instruction,
            student_level=student_level
        )
    
    def provide_example(self, instruction: str, concept: str) -> str:
        """Provide a relatable example"""
        chain = LLMChain(
            llm=self.llm,
            prompt=PRACTICE_EXAMPLE_PROMPT,
            verbose=True
        )
        
        return chain.run(
            instruction=instruction,
            concept=concept
        )
    
    def explain_instruction(self, instruction: str, student_level: int) -> str:
        """Explain instruction in simple terms"""
        chain = LLMChain(
            llm=self.llm,
            prompt=PRACTICE_EXPLAIN_PROMPT,
            verbose=True
        )
        
        return chain.run(
            instruction=instruction,
            student_level=student_level
        )