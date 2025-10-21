# app/ai/chains/hebrew_mediation_chain.py
from langchain.chains.base import Chain
from langchain.chains.router import LLMRouterChain, MultiRouteChain
from langchain.chains import ConversationChain
from langchain.memory import ConversationSummaryBufferMemory
from langchain.prompts import PromptTemplate
from typing import Dict, List, Optional, Any
from app.ai.multi_llm_manager import multi_llm_manager
from app.ai.prompts.hebrew_prompts import (
    HEBREW_BREAKDOWN_PROMPT, HEBREW_EXAMPLE_PROMPT, HEBREW_EXPLAIN_PROMPT,
    HEBREW_ENCOURAGEMENT, get_encouragement
)
import json
import re
import logging

logger = logging.getLogger(__name__)

class ConversationStateMemory:
    """Enhanced memory that tracks mediation state and strategy attempts"""
    
    def __init__(self, **kwargs):
        self.failed_strategies = []
        self.comprehension_indicators = []
        self.attempt_count = 0
        self.conversation_history = []
        
    def add_strategy_attempt(self, strategy: str, success: bool):
        """Track attempted strategies and their success"""
        if not success:
            self.failed_strategies.append(strategy)
        self.attempt_count += 1
        
    def get_failed_strategies(self) -> List[str]:
        return self.failed_strategies.copy()
    
    def assess_comprehension(self, student_response: str) -> str:
        """Analyze Hebrew student response for comprehension indicators"""
        response_lower = student_response.lower().strip()
        
        # If response is empty or just greetings, treat as initial
        if not response_lower or response_lower in ["", "היי", "שלום", "הי", "שלום שלום"]:
            return "initial"
        
        # Emotional indicators - check first (expanded for better recognition)
        emotional_phrases = [
            # Sadness indicators
            "אני עצוב", "אני עצובה", "עצוב", "עצובה", "עצובים", "עצובות", "עצוב לי", "בוכה", "בוכים", "אני בוכה",

            # Anger indicators
            "אני כועס", "אני כועסת", "כועס", "כועסת", "כועסים", "כועסות", "כועס על", "נרגז", "נרגזת", "מעצבן", "אני נרגז",

            # Fear indicators
            "אני מפחד", "אני מפחדת", "מפחד", "מפחדת", "מפחדים", "מפחדות", "פחד", "מפחיד", "מפחידה",

            # Anxiety indicators
            "אני חרד", "אני חרדה", "חרד", "חרדה", "חרדים", "חרדות", "מלחיץ", "מלחיצה", "לחוץ", "אני לחוץ",

            # Worry indicators
            "אני דואג", "אני דואגת", "דואג", "דואגת", "דואגים", "דואגות", "מודאג", "מודאגת", "דאגה",

            # Frustration indicators
            "אני מתוסכל", "אני מתוסכלת", "מתוסכל", "מתוסכלת", "תסכול", "נמאס לי", "נמאס", "מעצבן",

            # Discouragement indicators
            "לא רוצה", "לא בא לי", "לא מתחשק לי", "מוותר", "לא יכול יותר", "אני לא רוצה", "אני מוותר",

            # General negative feelings
            "לא טוב לי", "רע לי", "לא בסדר", "לא טוב", "רע", "גרוע", "נורא", "זוועה", "אני לא מרגיש טוב"
        ]
        
        for phrase in emotional_phrases:
            if phrase in response_lower:
                self.comprehension_indicators.append("emotional")
                return "emotional"
        
        # Confusion indicators in Hebrew (including frustration-related confusion)
        confusion_phrases = [
            "לא הבין", "לא מבין", "מה זה אומר", "לא מצליח", "קשה לי",
            "לא יודע", "אל תבין", "מה זה", "איך עושים", "עזרה", 
            "לא מבין כלום", "זה יותר מדי קשה", "לא מצליח בכלל", "מה קורה פה",
            "זה לא הגיוני", "לא מבין בכלל", "מה זה הדבר הזה", "איך זה עובד",
            "confused", "confusing", "hard", "difficult", "don't understand",
            # Add more question patterns
            "?", "שאלה", "question", "תעזור", "תעזרי", "איך", "למה", "מתי", "איפה", "מי", "מה", "איזה",
            "help", "what is", "how", "why", "when", "where", "who", "what", "which"
        ]
        
        # Understanding indicators  
        understanding_phrases = [
            "הבנתי", "ברור", "יודע", "מבין", "אוקיי", "בסדר", "נכון", "כן"
        ]
        
        for phrase in confusion_phrases:
            if phrase in response_lower:
                self.comprehension_indicators.append("confused")
                return "confused"
                
        for phrase in understanding_phrases:
            if phrase in response_lower:
                self.comprehension_indicators.append("understood")
                return "understood"
        
        # If it's a substantial message (more than just a word), treat as confused/question
        if len(response_lower.split()) > 1:
            self.comprehension_indicators.append("confused")
            return "confused"
                
        # Default to partial understanding
        self.comprehension_indicators.append("partial")
        return "partial"

class HebrewMediationRouter:
    """Implements Hebrew teacher-practice-based strategy routing"""
    
    def __init__(self):
        # Hierarchical strategy order based on Hebrew examples
        self.strategy_hierarchy = [
            "emotional_support",    # תמיכה רגשית
            "highlight_keywords",    # הדגשת מילות מפתח
            "guided_reading",       # הנחיה לקריאה בעיון
            "provide_example",      # מתן דוגמה
            "breakdown_steps",      # פירוק לשלבים
            "detailed_explanation", # הסבר מפורט
            "teacher_escalation"    # פנייה למורה
        ]
        
        # Simplified Hebrew strategy templates for fast responses
        self.strategy_templates = {
            "emotional_support": PromptTemplate(
                input_variables=["instruction"],
                template="""התלמיד אמר: {instruction}

תגיב בעברית בחמימות ותמיכה. תגיב לרגש של התלמיד, לא למשימה.
השתמש במילים כמו: "אני כאן בשבילך", "אני מבין", "בוא ננסה יחד", "אל תדאג", "אני אעזור לך".
תגיב בשפה חמה ומעודדת, 1-2 משפטים קצרים.
התאם את התגובה למה שהתלמיד אמר - אם התלמיד עצוב, תגיב בהבנה. אם התלמיד כועס, תגיב בסבלנות.
השתמש בשפה ניטרלית או התאם למין שהתלמיד הזכיר.

תגובה:"""
            ),
            
            "highlight_keywords": PromptTemplate(
                input_variables=["instruction"],
                template="""בוא נסתכל על המילים החשובות בהוראה: {instruction}

זהה 2-3 מילות מפתח חשובות בהוראה.
הסבר מה כל מילה אומרת במילים פשוטות.
השתמש במילים כמו: "המילה החשובה היא", "זה אומר", "הכוונה היא".
השתמש בשפה ניטרלית או התאם למין שהתלמיד הזכיר.

תגובה:"""
            ),

            "guided_reading": PromptTemplate(
                input_variables=["instruction"],
                template="""בוא נקרא את ההוראה יחד: {instruction}

קרא את ההוראה מילה אחר מילה.
שאל את התלמיד מה התלמיד חושב שמבקשים לעשות.
השתמש במילים כמו: "בוא נקרא יחד", "מה אתה/את חושב/ת", "מה מבקשים".
השתמש בשפה ניטרלית או התאם למין שהתלמיד הזכיר.

תגובה:"""
            ),

            "provide_example": PromptTemplate(
                input_variables=["instruction", "concept"],
                template="""הנה דוגמה פשוטה להבנת ההוראה: {instruction}

תן דוגמה קונקרטית מהחיים שמסבירה את ההוראה.
השתמש במילים כמו: "לדוגמה", "זה כמו", "תחשוב על זה כך".
הדוגמה צריכה להיות פשוטה ורלוונטית לתלמיד.
השתמש בשפה ניטרלית או התאם למין שהתלמיד הזכיר.

תגובה:"""
            ),

            "breakdown_steps": PromptTemplate(
                input_variables=["instruction"],
                template="""בוא נפרק את ההוראה לשלבים פשוטים: {instruction}

פרק את ההוראה ל-3-4 שלבים פשוטים וברורים.
כל שלב צריך להיות קצר וקל להבנה.
השתמש במילים כמו: "שלב ראשון", "אחר כך", "בסוף".
השתמש בשפה ניטרלית או התאם למין שהתלמיד הזכיר.

תגובה:"""
            ),

            "detailed_explanation": PromptTemplate(
                input_variables=["instruction"],
                template="""בוא נבין יחד מה ההוראה אומרת: {instruction}

הסבר את ההוראה במילים פשוטות וברורות.
כלול: מה צריך לעשות, איך לעשות את זה, איך לדעת שסיימת.
השתמש במילים כמו: "המטרה היא", "איך עושים את זה", "כשתסיים".
השתמש בשפה ניטרלית או התאם למין שהתלמיד הזכיר.

תגובה:"""
            )
        }

    def route_strategy(self, comprehension_level: str, failed_strategies: List[str],
                      mode: str = "practice", assistance_type: str = None) -> Optional[str]:
        """Route to next appropriate strategy based on Hebrew decision tree"""

        # Handle specific assistance type requests (Student Selection mode)
        if assistance_type:
            assistance_strategy_map = {
                "explain": "detailed_explanation",      # הסבר
                "breakdown": "breakdown_steps",        # פירוק לשלבים
                "example": "provide_example"           # מתן דוגמה
            }
            if assistance_type in assistance_strategy_map:
                return assistance_strategy_map[assistance_type]

        # Emotional responses get immediate emotional support
        if comprehension_level == "emotional":
            return "emotional_support"
        
        # Test mode: limit to 3 attempts
        if mode == "test" and len(failed_strategies) >= 3:
            return "teacher_escalation"
            
        # Find next strategy in hierarchy that hasn't failed
        for strategy in self.strategy_hierarchy:
            if strategy not in failed_strategies:
                return strategy
                
        # If all strategies tried, escalate to teacher
        return "teacher_escalation"

class HebrewMediationChain(Chain):
    """Main chain implementing Hebrew teacher-practice conversation flow"""
    
    # Define allowed fields for Pydantic
    provider: Optional[str] = None
    router: HebrewMediationRouter = None
    memory: ConversationStateMemory = None
    custom_system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    
    def __init__(self, provider: str = None, custom_system_prompt: str = None,
                 temperature: float = 0.7, max_tokens: int = 2048):
        super().__init__(provider=provider, custom_system_prompt=custom_system_prompt,
                        temperature=temperature, max_tokens=max_tokens)
        self.router = HebrewMediationRouter()
        self.memory = ConversationStateMemory()
    
    @property
    def input_keys(self) -> List[str]:
        return ["instruction", "student_response", "mode", "student_context", "assistance_type"]
    
    @property
    def output_keys(self) -> List[str]:
        return ["response", "strategy_used", "comprehension_level"]
        
    def _call(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Hebrew mediation conversation flow"""
        
        try:
            instruction = inputs.get("instruction", "")
            student_response = inputs.get("student_response", "")
            mode = inputs.get("mode", "practice")
            student_context = inputs.get("student_context", {})
            assistance_type = inputs.get("assistance_type")
            
            # Assess student comprehension from their response
            if student_response:
                comprehension = self.memory.assess_comprehension(student_response)
            else:
                comprehension = "initial"  # First interaction
            
            # Get failed strategies from memory
            failed_strategies = self.memory.get_failed_strategies()
            
            # Handle initial conversation with proper greeting (from Hebrew document)
            # Only show greeting if this is truly the first message (empty or just greeting)
            if (comprehension == "initial" and 
                (not student_response or 
                 student_response.strip() in ["", "היי", "שלום", "הי", "שלום שלום"])):
                return {
                    "response": "היי, אני לרנובוט, ואני פה כדי לעזור לך להבין את המשימות שלך. מה שלומך? 😊",
                    "strategy_used": "initial_greeting",
                    "comprehension_level": comprehension
                }

            # Route to appropriate strategy (considering assistance type)
            strategy = self.router.route_strategy(comprehension, failed_strategies, mode, assistance_type)

            if not strategy:
                return {
                    "response": "בוא ננסה גישה אחרת. איך אתה מרגיש עם המשימה הזו?",
                    "strategy_used": "open_question",
                    "comprehension_level": comprehension
                }

            # Generate response based on strategy
            response = self._execute_strategy(strategy, instruction, student_context)
            
            # Track strategy attempt (will be marked as failed if student still confused)
            success = comprehension in ["understood", "partial"]
            self.memory.add_strategy_attempt(strategy, success)
            
            return {
                "response": response,
                "strategy_used": strategy,
                "comprehension_level": comprehension
            }
            
        except Exception as e:
            logger.error(f"Error in Hebrew mediation chain: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
            return {
                "response": "אני כאן כדי לעזור לך עם המשימה! 😊 איך אני יכול לעזור?",
                "strategy_used": "error_fallback",
                "comprehension_level": "initial"
            }
    
    def _get_direct_emotional_response(self, instruction: str) -> str:
        """Get direct emotional response for local models (bypasses LLM generation)"""
        instruction_lower = instruction.lower().strip()
        
        # Direct emotional response mapping for immediate responses (no LLM generation needed)
        emotional_responses = {
            "אני עצוב": "אני מבין שאתה מרגיש עצוב. זה בסדר להרגיש כך. אני כאן בשבילך. איך אני יכול לעזור לך להרגיש יותר טוב? 💙",
            "אני עצובה": "אני מבינה שאת מרגישה עצובה. זה בסדר להרגיש כך. אני כאן בשבילך. איך אני יכול לעזור לך להרגיש יותר טובה? 💙",
            "עצוב": "אני מבין שאתה מרגיש עצוב. זה בסדר להרגיש כך. אני כאן בשבילך. איך אני יכול לעזור לך להרגיש יותר טוב? 💙",
            "עצובה": "אני מבינה שאת מרגישה עצובה. זה בסדר להרגיש כך. אני כאן בשבילך. איך אני יכול לעזור לך להרגיש יותר טובה? 💙",
            "אני כועס": "אני רואה שאתה כועס. זה בסדר להרגיש כך. בוא נדבר על מה שמפריע לך. אני כאן להקשיב. 💪",
            "אני כועסת": "אני רואה שאת כועסת. זה בסדר להרגיש כך. בואי נדבר על מה שמפריע לך. אני כאן להקשיב. 💪",
            "כועס": "אני רואה שאתה כועס. זה בסדר להרגיש כך. בוא נדבר על מה שמפריע לך. אני כאן להקשיב. 💪",
            "כועסת": "אני רואה שאת כועסת. זה בסדר להרגיש כך. בואי נדבר על מה שמפריע לך. אני כאן להקשיב. 💪",
            "אני מפחד": "אני מבין שאתה מפחד. זה בסדר לפחד. אני כאן כדי לעזור לך להרגיש בטוח יותר. איך אני יכול לתמוך בך? 🤗",
            "אני מפחדת": "אני מבינה שאת מפחדת. זה בסדר לפחד. אני כאן כדי לעזור לך להרגיש בטוחה יותר. איך אני יכול לתמוך בך? 🤗",
            "מפחד": "אני מבין שאתה מפחד. זה בסדר לפחד. אני כאן כדי לעזור לך להרגיש בטוח יותר. איך אני יכול לתמוך בך? 🤗",
            "מפחדת": "אני מבינה שאת מפחדת. זה בסדר לפחד. אני כאן כדי לעזור לך להרגיש בטוחה יותר. איך אני יכול לתמוך בך? 🤗",
            "אני דואג": "אני רואה שאתה דואג. זה טבעי לדאוג לפעמים. אני כאן כדי לעזור לך. בוא נדבר על מה שמדאיג אותך. 💙",
            "אני דואגת": "אני רואה שאת דואגת. זה טבעי לדאוג לפעמים. אני כאן כדי לעזור לך. בואי נדבר על מה שמדאיג אותך. 💙",
            "דואג": "אני רואה שאתה דואג. זה טבעי לדאוג לפעמים. אני כאן כדי לעזור לך. בוא נדבר על מה שמדאיג אותך. 💙",
            "דואגת": "אני רואה שאת דואגת. זה טבעי לדאוג לפעמים. אני כאן כדי לעזור לך. בואי נדבר על מה שמדאיג אותך. 💙",
            "לא רוצה": "אני מבין שאתה לא רוצה לעשות את זה עכשיו. זה בסדר. אולי נוכל לנסות משהו אחר או לחזור לזה מאוחר יותר? 😊",
            "אני לא רוצה": "אני מבין שאתה לא רוצה לעשות את זה עכשיו. זה בסדר. אולי נוכל לנסות משהו אחר או לחזור לזה מאוחר יותר? 😊",
            "לא בא לי": "אני מבין שאתה לא מרגיש מוכן לזה עכשיו. זה בסדר. איך אני יכול לעזור לך להרגיש יותר מוכן? 🌟",
            "לא טוב לי": "אני מבין שאתה לא מרגיש טוב. זה בסדר. אני כאן כדי לעזור לך. איך אני יכול לתמוך בך? 💙",
            "רע לי": "אני מבין שאתה מרגיש רע. זה בסדר להרגיש כך. אני כאן בשבילך. איך אני יכול לעזור לך להרגיש יותר טוב? 💙",
            "אני לא מרגיש טוב": "אני מבין שאתה לא מרגיש טוב. זה בסדר. אני כאן כדי לעזור לך. איך אני יכול לתמוך בך? 💙"
        }
        
        # Check for emotional keywords
        for keyword, response in emotional_responses.items():
            if keyword in instruction_lower:
                return response
                
        return None  # No direct response found, use LLM generation

    def _execute_strategy(self, strategy: str, instruction: str, student_context: Dict) -> str:
        """Execute specific mediation strategy"""
        
        # For emotional support, try direct response first (better for local models)
        if strategy == "emotional_support":
            direct_response = self._get_direct_emotional_response(instruction)
            if direct_response:
                return direct_response
        
        if strategy == "teacher_escalation":
            return ("נראה לי שהמשימה הזו מורכבת. "
                   "בוא נפנה למורה שלך לעזרה נוספת. "
                   "אתה יכול ללחוץ על כפתור 'קריאה למורה' 👩‍🏫")
        
        # Get strategy template
        if strategy not in self.router.strategy_templates:
            strategy = "breakdown_steps"  # fallback
            
        template = self.router.strategy_templates[strategy]
        
        # Prepare template variables
        template_vars = {"instruction": instruction}
        
        if strategy == "provide_example":
            # Extract main concept from instruction for example
            concept = self._extract_main_concept(instruction)
            template_vars["concept"] = concept
            
        # Generate response using multi_llm_manager
        try:
            formatted_prompt = template.format(**template_vars)
            
            # Prepend custom system prompt if manager configured one
            if self.custom_system_prompt:
                formatted_prompt = f"{self.custom_system_prompt}\n\n{formatted_prompt}"
                logger.info(f"Using custom system prompt for strategy: {strategy}")

            logger.info(f"Generating response for strategy: {strategy}")

            # Use custom temperature and max_tokens if set by manager
            response = multi_llm_manager.generate(
                prompt=formatted_prompt,
                provider=self.provider,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            logger.info(f"Successfully generated response for strategy: {strategy}")
            return response
            
        except Exception as e:
            logger.error(f"Error generating response for strategy {strategy}: {str(e)}")
            
            # Fallback to simple Hebrew response
            fallback_responses = {
                "emotional_support": "אני מבין שאתה מרגיש עצוב. זה בסדר להרגיש כך. אני כאן בשבילך. איך אני יכול לעזור לך להרגיש יותר טוב? 💙",
                "highlight_keywords": "בוא נסתכל על המילים החשובות בהוראה. איזו מילה נראית לך הכי חשובה?",
                "guided_reading": "בוא נקרא שוב את ההוראה בזהירות, מילה אחר מילה.",
                "provide_example": "אני אתן לך דוגמה שתעזור להבין את המשימה.",
                "breakdown_steps": "בוא נפרק את המשימה לחלקים קטנים וקלים.",
                "detailed_explanation": "אני אסביר לך במילים פשוטות מה צריך לעשות."
            }
            
            return fallback_responses.get(strategy, "אני כאן לעזור לך. איך אני יכול לעזור?") + " 😊"
    
    def _extract_main_concept(self, instruction: str) -> str:
        """Extract main concept from Hebrew instruction for examples"""
        
        # Simple concept extraction based on common Hebrew educational terms
        concepts_map = {
            "חישוב": "חשבון במתמטיקה",
            "קריאה": "קריאת טקסט",
            "כתיבה": "כתיבת משפטים",
            "ציור": "ציור או רישום",
            "השוואה": "השוואה בין דברים",
            "מיון": "סידור לפי קטגוריות",
            "הסבר": "הסבר של רעיון"
        }
        
        instruction_lower = instruction.lower()
        for keyword, concept in concepts_map.items():
            if keyword in instruction_lower:
                return concept
                
        return "משימה כללית"
    
    @property
    def _chain_type(self) -> str:
        return "hebrew_mediation_chain"
    
    def reset_conversation(self):
        """Reset conversation state for new session"""
        self.memory = ConversationStateMemory()

# Factory function for easy integration
def create_hebrew_mediation_chain(provider: str = None, custom_system_prompt: str = None,
                                 temperature: float = 0.7, max_tokens: int = 2048) -> HebrewMediationChain:
    """Create configured Hebrew mediation chain with optional custom config"""
    return HebrewMediationChain(provider=provider, custom_system_prompt=custom_system_prompt,
                               temperature=temperature, max_tokens=max_tokens)