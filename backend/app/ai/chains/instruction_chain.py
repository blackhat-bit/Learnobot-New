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
    
    def _get_custom_system_prompt(self, mode: str = "practice"):
        """Load saved custom system prompt from manager configuration"""
        try:
            from app.core.database import SessionLocal
            from app.models.llm_config import LLMConfig
            
            db = SessionLocal()
            try:
                mode_name = f"{mode}_mode"
                saved_config = db.query(LLMConfig).filter(
                    LLMConfig.name == mode_name
                ).order_by(LLMConfig.updated_at.desc()).first()
                
                if saved_config and saved_config.system_prompt:
                    logger.info(f"✅ Using manager custom prompt for {mode_name}")
                    return saved_config.system_prompt
                return None
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error loading custom prompt: {e}")
            return None
    
    def _has_task(self, instruction: str, student_context: dict) -> bool:
        """Detect if message contains a task (question/image) vs pure emotional expression"""
        # Has uploaded image
        if student_context.get('has_image'):
            return True
        
        # Contains question marks or task keywords
        task_keywords = ['עזרה', 'שאלה', 'לא מבין', 'איך', 'מה', 'למה', 'תעזור']
        if '?' in instruction or any(word in instruction for word in task_keywords):
            return True
        
        # Check for pure emotional expression
        emotional_phrases = ['עצוב', 'עייף', 'כועס', 'מפחד', 'חרד', 'עצובה', 'עייפה', 
                           'כועסת', 'מפחדת', 'חרדה', 'נמאס', 'לא בא לי']
        has_emotion = any(phrase in instruction.lower() for phrase in emotional_phrases)
        
        if has_emotion:
            # If it's emotional but has task content (question or longer message), show suggestions
            return '?' in instruction or len(instruction.split()) > 5
        
        # Default: show suggestions for most messages
        return True
        
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
        
        # For cloud models, use efficient prompt with system guidance
        if provider and not provider.startswith("ollama-"):
            # Load saved custom prompt from manager if available
            custom_system_prompt = self._get_custom_system_prompt("practice")
            
            # Get conversation history
            conversation_history = student_context.get("conversation_history", "")

            # Check for typos/gibberish that might mean Hebrew assistance words
            instruction_clean = instruction.lower()
            # Common typos for Hebrew assistance words
            if any(typo in instruction_clean for typo in ['xchr', 'xsbir', 'hsbr', 'explain']):
                instruction_interpretation = "הסבר"
            elif any(typo in instruction_clean for typo in ['breakdown', 'steps', 'pirok']):
                instruction_interpretation = "פירוק לשלבים"
            elif any(typo in instruction_clean for typo in ['example', 'dugma', 'דוגמא']):
                instruction_interpretation = "דוגמה"
            else:
                instruction_interpretation = instruction

            # Check if this is first message in conversation
            is_first_message = not conversation_history or conversation_history.strip() == ""
            
            # Check if message has a task (for showing suggestions)
            has_task = self._has_task(instruction_interpretation, student_context)
            
            # Short, efficient prompt - guide student to choose assistance type
            if is_first_message:
                # First message - include greeting
                if has_task:
                    default_prompt = f"""אתה לרנובוט, עוזר AI שעוזר לתלמידים. תענה ישירות לתלמיד.

התלמיד שאל: "{instruction_interpretation}"

אני יכול לעזור בשלוש דרכים:
🔍 הסבר - הסבר מה זה אומר
📝 פירוק לשלבים - לחלק למשימות קטנות
💡 דוגמה - לתת דוגמה מהחיים

איך תרצה שאעזור לך?"""
                else:
                    # Pure emotional message - no suggestions
                    default_prompt = f"""אתה לרנובוט, עוזר AI שעוזר לתלמידים. תענה ישירות לתלמיד.

התלמיד אמר: "{instruction_interpretation}"

תגיב בחמימות ותמיכה רגשית. אל תציע אפשרויות עזרה."""
            else:
                # Continuing conversation - NO greeting, just help
                if has_task:
                    # Check if context was recently provided (student sent text after being asked)
                    context_was_provided = len(instruction_interpretation) > 50 or any(
                        keyword in conversation_history.lower() 
                        for keyword in ['אני צריך לראות', 'אפשר לשלוח', 'תמונה או להקליד']
                    )
                    
                    if context_was_provided:
                        # Context was provided - give actual help
                        default_prompt = f"""התלמיד שאל: "{instruction_interpretation}"

היסטוריה: {conversation_history}

חוקים:
- תן תשובה מועילה ומפורטת
- אל תמציא מידע
- עזור לתלמיד להבין את המשימה

עכשיו תן עזרה אמיתית לתלמיד. אם הוא שיתף טקסט או הסביר את המשימה, עזור לו עכשיו:
🔍 הסבר 📝 פירוק לשלבים 💡 דוגמה"""
                    else:
                        # No context yet
                        default_prompt = f"""התלמיד שאל: "{instruction_interpretation}"

היסטוריה: {conversation_history}

חוקים:
- אל תיתן תשובות מוכנות
- אל תמציא מידע
- אל תחזור על טקסט שהתלמיד שלח

אם התלמיד שאל על טקסט וטרם סיפק אותו:
תגיד: "אני צריך לראות את הטקסט. אפשר לשלוח תמונה או להקליד?"

אחרת, שאל איך לעזור:
🔍 הסבר 📝 פירוק לשלבים 💡 דוגמה"""
                else:
                    # Pure emotional message - no suggestions
                    default_prompt = f"""התלמיד אמר: "{instruction_interpretation}"

היסטוריה: {conversation_history}

תגיב בחמימות ותמיכה רגשית. אל תציע אפשרויות עזרה."""
            
            # If custom prompt exists, prepend it to the default prompt
            if custom_system_prompt:
                prompt_text = f"""{custom_system_prompt}

{default_prompt}"""
            else:
                prompt_text = default_prompt
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
        
        # Validate that response is not empty and makes sense
        if not result or not result.strip():
            logger.warning("Empty response from LLM, using fallback")
            result = "אני כאן לעזור לך! איך תרצה שאעזור?\n\n🔍 הסבר - הסבר מה זה אומר\n📝 פירוק לשלבים - לחלק למשימות קטנות\n💡 דוגמה - לתת דוגמה מהחיים"
        elif self._is_nonsensical_response(result):
            logger.warning("Nonsensical response from LLM, using fallback")
            result = "אני כאן לעזור לך! איך תרצה שאעזור?\n\n🔍 הסבר - הסבר מה זה אומר\n📝 פירוק לשלבים - לחלק למשימות קטנות\n💡 דוגמה - לתת דוגמה מהחיים"
        
        return {"analysis": result}
    
    def _is_nonsensical_response(self, response: str) -> bool:
        """Check if the response is nonsensical or corrupted"""
        response_lower = response.lower().strip()
        
        # Check for repeated characters (like "LLLLLLI")
        if len(set(response_lower)) <= 3 and len(response_lower) > 10:
            return True
            
        # Check for gibberish patterns
        gibberish_patterns = [
            'כל הלידה ערהויך מד החיוך',  # The specific weird response from the image
            'heh lang',  # Another pattern from the image
            'havant meycal',  # Another pattern from the image
        ]
        
        for pattern in gibberish_patterns:
            if pattern in response_lower:
                return True
                
        # Check for too many repeated characters
        if any(char * 5 in response_lower for char in 'abcdefghijklmnopqrstuvwxyz'):
            return True
            
        # Check for responses that are too short and don't contain Hebrew or meaningful words
        if len(response.strip()) < 20 and not any(word in response_lower for word in ['אני', 'אתה', 'זה', 'זהו', 'הנה', 'כאן']):
            return True
            
        return False
    
    def breakdown_instruction(self, instruction: str, student_level: int, language_preference: str = "he", provider: str = None, student_context: dict = None) -> str:
        """Break down instruction into simple steps"""
        import logging
        logger = logging.getLogger(__name__)
        
        # For cloud models, use efficient short prompt WITH conversation history
        if provider and not provider.startswith("ollama-"):
            from app.ai.prompts.hebrew_prompts import HEBREW_BREAKDOWN_SHORT
            
            # Load custom system prompt from manager
            custom_system_prompt = self._get_custom_system_prompt("practice")
            
            # Get conversation history if available
            conversation_history = ""
            if student_context:
                conversation_history = student_context.get("conversation_history", "")
            
            # Include conversation history in prompt for context
            if conversation_history:
                default_prompt = f"""היסטוריית שיחה:
{conversation_history}

{HEBREW_BREAKDOWN_SHORT.format(instruction=instruction)}

התבסס על השיחה האחרונה כדי לתת פירוק רלוונטי."""
            else:
                default_prompt = HEBREW_BREAKDOWN_SHORT.format(instruction=instruction)
            
            # Prepend custom prompt if exists
            if custom_system_prompt:
                prompt_text = f"""{custom_system_prompt}

{default_prompt}"""
            else:
                prompt_text = default_prompt
            
            logger.info(f"🔧 BREAKDOWN - Provider: {provider}, Has history: {bool(conversation_history)}, Custom prompt: {bool(custom_system_prompt)}")
        else:
            # Use existing prompts for local models
            prompts = self._get_prompts_for_language(language_preference)
            prompt_text = prompts['breakdown'].format(
                instruction=instruction,
                student_level=student_level
            )
            logger.info(f"🔧 BREAKDOWN - Provider: {provider}, Using local prompts")
        
        response = multi_llm_manager.generate(prompt_text, provider=provider)
        logger.info(f"🔧 BREAKDOWN - Response length: {len(response) if response else 0}, Content: {response[:200] if response else 'EMPTY!'}")
        
        # Validate that response is not empty and makes sense
        if not response or not response.strip():
            logger.warning("Empty response from LLM in breakdown, using fallback")
            response = "אני אעזור לך לפרק את המשימה לשלבים פשוטים. בואו נתחיל!"
        elif self._is_nonsensical_response(response):
            logger.warning("Nonsensical response from LLM in breakdown, using fallback")
            response = "אני אעזור לך לפרק את המשימה לשלבים פשוטים. בואו נתחיל!"
        
        return response
    
    def provide_example(self, instruction: str, concept: str, language_preference: str = "he", provider: str = None, student_context: dict = None) -> str:
        """Provide a relatable example"""
        
        # For cloud models, use efficient short prompt WITH conversation history
        if provider and not provider.startswith("ollama-"):
            from app.ai.prompts.hebrew_prompts import HEBREW_EXAMPLE_SHORT
            
            # Load custom system prompt from manager
            custom_system_prompt = self._get_custom_system_prompt("practice")
            
            # Get conversation history if available
            conversation_history = ""
            if student_context:
                conversation_history = student_context.get("conversation_history", "")
            
            # Include conversation history in prompt for context
            if conversation_history:
                default_prompt = f"""היסטוריית שיחה:
{conversation_history}

{HEBREW_EXAMPLE_SHORT.format(instruction=instruction)}

התבסס על השיחה האחרונה כדי לתת דוגמה רלוונטית."""
            else:
                default_prompt = HEBREW_EXAMPLE_SHORT.format(instruction=instruction)
            
            # Prepend custom prompt if exists
            if custom_system_prompt:
                prompt_text = f"""{custom_system_prompt}

{default_prompt}"""
            else:
                prompt_text = default_prompt
        else:
            # Use existing prompts for local models
            prompts = self._get_prompts_for_language(language_preference)
            prompt_text = prompts['example'].format(
                instruction=instruction,
                concept=concept
            )
        
        response = multi_llm_manager.generate(prompt_text, provider=provider)
        
        # Validate that response is not empty and makes sense
        if not response or not response.strip():
            logger.warning("Empty response from LLM in example, using fallback")
            response = "אני אתן לך דוגמה טובה שתעזור לך להבין את הנושא!"
        elif self._is_nonsensical_response(response):
            logger.warning("Nonsensical response from LLM in example, using fallback")
            response = "אני אתן לך דוגמה טובה שתעזור לך להבין את הנושא!"
        
        return response
    
    def explain_instruction(self, instruction: str, student_level: int, language_preference: str = "he", provider: str = None, student_context: dict = None) -> str:
        """Explain instruction in simple terms"""
        
        # For cloud models, use efficient short prompt WITH conversation history
        if provider and not provider.startswith("ollama-"):
            from app.ai.prompts.hebrew_prompts import HEBREW_EXPLAIN_SHORT
            
            # Load custom system prompt from manager
            custom_system_prompt = self._get_custom_system_prompt("practice")
            
            # Get conversation history if available
            conversation_history = ""
            if student_context:
                conversation_history = student_context.get("conversation_history", "")
            
            # Include conversation history in prompt for context
            if conversation_history:
                default_prompt = f"""היסטוריית שיחה:
{conversation_history}

{HEBREW_EXPLAIN_SHORT.format(instruction=instruction)}

התבסס על השיחה האחרונה כדי לתת הסבר רלוונטי."""
            else:
                default_prompt = HEBREW_EXPLAIN_SHORT.format(instruction=instruction)
            
            # Prepend custom prompt if exists
            if custom_system_prompt:
                prompt_text = f"""{custom_system_prompt}

{default_prompt}"""
            else:
                prompt_text = default_prompt
        else:
            # Use existing prompts for local models
            prompts = self._get_prompts_for_language(language_preference)
            prompt_text = prompts['explain'].format(
                instruction=instruction,
                student_level=student_level
            )
        
        response = multi_llm_manager.generate(prompt_text, provider=provider)
        
        # Validate that response is not empty and makes sense
        if not response or not response.strip():
            logger.warning("Empty response from LLM in explain, using fallback")
            response = "אני אסביר לך את הנושא בצורה פשוטה וברורה!"
        elif self._is_nonsensical_response(response):
            logger.warning("Nonsensical response from LLM in explain, using fallback")
            response = "אני אסביר לך את הנושא בצורה פשוטה וברורה!"
        
        return response
