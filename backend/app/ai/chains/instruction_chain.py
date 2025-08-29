# app/ai/chains/instruction_chain.py
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from app.ai.llm_manager import llm_manager
from app.ai.prompts.hebrew_prompts import (
    HEBREW_SYSTEM_PROMPT,
    HEBREW_BREAKDOWN_PROMPT,
    HEBREW_EXAMPLE_PROMPT,
    HEBREW_EXPLAIN_PROMPT,
    HEBREW_PRACTICE_PROMPT
)
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
    
    def _get_prompts_for_language(self, language_preference: str = 'he'):
        """
        Dynamically select prompts based on user language preference
        Default: Hebrew ('he') for Israeli educational system
        Only use English for explicitly international users
        """
        # Use English prompts ONLY if explicitly requested
        if language_preference and language_preference.lower() in ['en', 'english']:
            return {
                'practice': INSTRUCTION_ANALYSIS_PROMPT,
                'breakdown': PRACTICE_BREAKDOWN_PROMPT,
                'example': PRACTICE_EXAMPLE_PROMPT,
                'explain': PRACTICE_EXPLAIN_PROMPT,
                'analysis': INSTRUCTION_ANALYSIS_PROMPT
            }
        else:
            # Default to Hebrew (Israeli educational system)
            # Covers: 'he', 'hebrew', None, 'en' (changed to default Hebrew)
            return {
                'practice': HEBREW_PRACTICE_PROMPT,
                'breakdown': HEBREW_BREAKDOWN_PROMPT,
                'example': HEBREW_EXAMPLE_PROMPT,
                'explain': HEBREW_EXPLAIN_PROMPT,
                'analysis': HEBREW_PRACTICE_PROMPT
            }
    
    def analyze_instruction(self, instruction: str, student_context: dict) -> dict:
        """Analyze an instruction to understand what needs to be done"""
        # Get user language preference from context
        language_pref = student_context.get("language_preference", "he")
        prompts = self._get_prompts_for_language(language_pref)
        
        chain = LLMChain(
            llm=self.llm,
            prompt=prompts['analysis'],
            verbose=True
        )
        
        # Use appropriate parameters based on language
        if language_pref and language_pref.lower() in ['en', 'english']:
            result = chain.run(
                instruction=instruction,
                student_context=str(student_context)
            )
        else:
            result = chain.run(
                instruction=instruction,
                student_level=student_context.get("difficulty_level", 3),
                assistance_type="הסבר"
            )
        
        return {"analysis": result}
    
    def breakdown_instruction(self, instruction: str, student_level: int, language_preference: str = "he") -> str:
        """Break down instruction into simple steps"""
        prompts = self._get_prompts_for_language(language_preference)
        
        chain = LLMChain(
            llm=self.llm,
            prompt=prompts['breakdown'],
            verbose=True
        )
        
        return chain.run(
            instruction=instruction,
            student_level=student_level
        )
    
    def provide_example(self, instruction: str, concept: str, language_preference: str = "he") -> str:
        """Provide a relatable example"""
        prompts = self._get_prompts_for_language(language_preference)
        
        chain = LLMChain(
            llm=self.llm,
            prompt=prompts['example'],
            verbose=True
        )
        
        return chain.run(
            instruction=instruction,
            concept=concept
        )
    
    def explain_instruction(self, instruction: str, student_level: int, language_preference: str = "he") -> str:
        """Explain instruction in simple terms"""
        prompts = self._get_prompts_for_language(language_preference)
        
        chain = LLMChain(
            llm=self.llm,
            prompt=prompts['explain'],
            verbose=True
        )
        
        return chain.run(
            instruction=instruction,
            student_level=student_level
        )
