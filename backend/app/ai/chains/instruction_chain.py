# app/ai/chains/instruction_chain.py
import logging
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from app.ai.llm_manager import llm_manager
from app.ai.multi_llm_manager import multi_llm_manager
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

logger = logging.getLogger(__name__)

class InstructionProcessor:
    def __init__(self):
        self.llm = llm_manager.get_llm()  # Fallback LLM
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
    def _get_llm_for_provider(self, provider: str = None):
        """Get LLM instance for specified provider"""
        if provider and provider in multi_llm_manager.providers:
            provider_instance = multi_llm_manager.providers[provider]
            # Handle different provider types
            if hasattr(provider_instance, 'llm'):
                return provider_instance.llm
            elif hasattr(provider_instance, 'client'):
                # For Google and other providers that use 'client' instead of 'llm'
                return provider_instance
            else:
                return None
        return self.llm  # Fallback to default
    
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
    
    def analyze_instruction(self, instruction: str, student_context: dict, provider: str = None) -> dict:
        """Analyze an instruction to understand what needs to be done"""
        
        # For cloud models, use educational guidance prompts with structured formats
        if provider and not provider.startswith("ollama-"):
            # Educational guidance prompt for cloud models
            prompt_text = f"""אתה מורה חכם וסבלני שמסייע לתלמידים ללמוד. התלמיד שאל: "{instruction}"

המטרה שלך היא לעזור לתלמיד ללמוד ולהבין, לא לתת תשובות ישירות.

השתמש באחת מהפורמטים החינוכיים הבאים:

**פורמט "הסבר"** - אם התלמיד שואל על משמעות או מושג:
- הסבר במילים פשוטות מה זה אומר
- תן דוגמה מהחיים
- שאל שאלה מנחה: "עכשיו אתה מבין? איך זה קשור למה שאתה לומד?"

**פורמט "פירוק לשלבים"** - אם התלמיד מבקש עזרה במשימה:
- פרק את המשימה ל-3-4 שלבים פשוטים
- כל שלב צריך להיות קצר וברור
- השתמש במילים: "שלב ראשון", "אחר כך", "בסוף"
- שאל: "איזה שלב אתה רוצה להתחיל איתו?"

**פורמט "דוגמה"** - אם התלמיד צריך להבין איך לעשות משהו:
- תן דוגמה קונקרטית מהחיים
- השתמש במילים: "לדוגמה", "זה כמו", "תחשוב על זה כך"
- שאל: "עכשיו אתה יכול לחשוב על דוגמה משלך?"

**פורמט "תמיכה רגשית"** - אם התלמיד עצוב או מתוסכל:
- תן תמיכה רגשית: "אני מבין שזה קשה"
- עזור לו להבין שזה בסדר להתקשות
- הצע דרך פשוטה להתחיל

תמיד השתמש בשפה חמה, ניטרלית ומעודדת. תגיב ב-2-3 משפטים.

תגובה:"""
        else:
            # Use existing complex prompts for local models
            language_pref = student_context.get("language_preference", "he")
            prompts = self._get_prompts_for_language(language_pref)
            
            # Format the prompt with variables
            if language_pref and language_pref.lower() in ['en', 'english']:
                prompt_text = prompts['analysis'].format(
                    instruction=instruction,
                    student_context=str(student_context)
                )
            else:
                prompt_text = prompts['analysis'].format(
                    instruction=instruction,
                    student_level=student_context.get("difficulty_level", 3),
                    assistance_type="הסבר"
                )
        
        # Use multi_llm_manager to generate response
        result = multi_llm_manager.generate(prompt_text, provider=provider)
        
        return {"analysis": result}
    
    def breakdown_instruction(self, instruction: str, student_level: int, language_preference: str = "he", provider: str = None) -> str:
        """Break down instruction into simple steps"""
        
        # For cloud models, use structured breakdown format
        if provider and not provider.startswith("ollama-"):
            prompt_text = f"""אתה מורה חכם שמסייע לתלמידים ללמוד. התלמיד מבקש עזרה במשימה: "{instruction}"

השתמש בפורמט "פירוק לשלבים":
- פרק את המשימה ל-3-4 שלבים פשוטים
- כל שלב צריך להיות קצר וברור
- השתמש במילים: "שלב ראשון", "אחר כך", "בסוף"
- שאל: "איזה שלב אתה רוצה להתחיל איתו?"

תמיד השתמש בשפה חמה, ניטרלית ומעודדת. תגיב ב-2-3 משפטים.

תגובה:"""
        else:
            # Use existing prompts for local models
            prompts = self._get_prompts_for_language(language_preference)
            prompt_text = prompts['breakdown'].format(
                instruction=instruction,
                student_level=student_level
            )
        
        return multi_llm_manager.generate(prompt_text, provider=provider)
    
    def provide_example(self, instruction: str, concept: str, language_preference: str = "he", provider: str = None) -> str:
        """Provide a relatable example"""
        
        # For cloud models, use structured example format
        if provider and not provider.startswith("ollama-"):
            prompt_text = f"""אתה מורה חכם שמסייע לתלמידים ללמוד. התלמיד מבקש דוגמה: "{instruction}"

השתמש בפורמט "דוגמה":
- תן דוגמה קונקרטית מהחיים
- השתמש במילים: "לדוגמה", "זה כמו", "תחשוב על זה כך"
- שאל: "עכשיו אתה יכול לחשוב על דוגמה משלך?"

תמיד השתמש בשפה חמה, ניטרלית ומעודדת. תגיב ב-2-3 משפטים.

תגובה:"""
        else:
            # Use existing prompts for local models
            prompts = self._get_prompts_for_language(language_preference)
            prompt_text = prompts['example'].format(
                instruction=instruction,
                concept=concept
            )
        
        return multi_llm_manager.generate(prompt_text, provider=provider)
    
    def explain_instruction(self, instruction: str, student_level: int, language_preference: str = "he", provider: str = None) -> str:
        """Explain instruction in simple terms"""
        
        # For cloud models, use structured explain format
        if provider and not provider.startswith("ollama-"):
            prompt_text = f"""אתה מורה חכם שמסייע לתלמידים ללמוד. התלמיד מבקש הסבר: "{instruction}"

השתמש בפורמט "הסבר":
- הסבר במילים פשוטות מה זה אומר
- תן דוגמה מהחיים
- שאל שאלה מנחה: "עכשיו אתה מבין? איך זה קשור למה שאתה לומד?"

תמיד השתמש בשפה חמה, ניטרלית ומעודדת. תגיב ב-2-3 משפטים.

תגובה:"""
        else:
            # Use existing prompts for local models
            prompts = self._get_prompts_for_language(language_preference)
            prompt_text = prompts['explain'].format(
                instruction=instruction,
                student_level=student_level
            )
        
        return multi_llm_manager.generate(prompt_text, provider=provider)
