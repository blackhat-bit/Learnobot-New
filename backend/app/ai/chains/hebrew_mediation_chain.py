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
        
        # Emotional indicators - check first
        emotional_phrases = [
            "עצוב", "עצובה", "עצובים", "עצובות", "sad", "sadness",
            "כועס", "כועסת", "כועסים", "כועסות", "angry", "anger",
            "מפחד", "מפחדת", "מפחדים", "מפחדות", "scared", "afraid",
            "חרד", "חרדה", "חרדים", "חרדות", "anxious", "anxiety",
            "דואג", "דואגת", "דואגים", "דואגות", "worried", "worry",
            "לא רוצה", "לא בא לי", "לא מתחשק לי", "don't want", "don't feel like",
            "לא טוב לי", "רע לי", "לא בסדר", "לא טוב", "feel bad"
        ]
        
        for phrase in emotional_phrases:
            if phrase in response_lower:
                self.comprehension_indicators.append("emotional")
                return "emotional"
        
        # Confusion indicators in Hebrew
        confusion_phrases = [
            "לא הבין", "לא מבין", "מה זה אומר", "לא מצליח", "קשה לי",
            "לא יודע", "אל תבין", "מה זה", "איך עושים", "עזרה"
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

זהו מצב רגשי. תגיב בעברית עם תמיכה ועידוד. אל תנתח את המילים או המשפט. תגיב לרגש בלבד.

דוגמאות לתגובות טובות:
- "אני מבין שאתה מרגיש עצוב. זה בסדר להרגיש כך. אני כאן בשבילך."
- "אני רואה שאתה כועס. בוא נדבר על זה."
- "זה בסדר לפחד. אני כאן כדי לעזור לך."

תגיב עכשיו:"""
            ),
            
            "highlight_keywords": PromptTemplate(
                input_variables=["instruction"],
                template="""ענה בעברית במשפט קצר: בוא נסתכל על המילים החשובות: {instruction}
איזו מילה הכי חשובה כאן?"""
            ),
            
            "guided_reading": PromptTemplate(
                input_variables=["instruction"],
                template="""ענה בעברית במשפט קצר: {instruction}
מה מבקשים ממך לעשות? (רק הפעולה)"""
            ),
            
            "provide_example": PromptTemplate(
                input_variables=["instruction", "concept"],
                template="""תן דוגמה פשוטה בעברית: {instruction}
דוגמה קצרה מחיי היומיום:"""
            ),
            
            "breakdown_steps": PromptTemplate(
                input_variables=["instruction"],
                template="""פרק בעברית ל-3 שלבים פשוטים: {instruction}
1. 
2. 
3."""
            )
        }

    def route_strategy(self, comprehension_level: str, failed_strategies: List[str], 
                      mode: str = "practice") -> Optional[str]:
        """Route to next appropriate strategy based on Hebrew decision tree"""
        
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
    
    def __init__(self, provider: str = None):
        super().__init__(provider=provider)
        self.router = HebrewMediationRouter()
        self.memory = ConversationStateMemory()
    
    @property
    def input_keys(self) -> List[str]:
        return ["instruction", "student_response", "mode", "student_context"]
    
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
            
            # Assess student comprehension from their response
            if student_response:
                comprehension = self.memory.assess_comprehension(student_response)
            else:
                comprehension = "initial"  # First interaction
            
            # Get failed strategies from memory
            failed_strategies = self.memory.get_failed_strategies()
            
            # Route to appropriate strategy
            strategy = self.router.route_strategy(comprehension, failed_strategies, mode)
            
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
        
        # Direct emotional response mapping for local models
        emotional_responses = {
            "עצוב": "אני מבין שאתה מרגיש עצוב. זה בסדר להרגיש כך. אני כאן בשבילך. איך אני יכול לעזור לך להרגיש יותר טוב? 💙",
            "עצובה": "אני מבין שאתה מרגיש עצובה. זה בסדר להרגיש כך. אני כאן בשבילך. איך אני יכול לעזור לך להרגיש יותר טובה? 💙",
            "כועס": "אני רואה שאתה כועס. זה בסדר להרגיש כך. בוא נדבר על מה שמפריע לך. אני כאן להקשיב. 💪",
            "כועסת": "אני רואה שאתה כועסת. זה בסדר להרגיש כך. בוא נדבר על מה שמפריע לך. אני כאן להקשיב. 💪",
            "מפחד": "אני מבין שאתה מפחד. זה בסדר לפחד. אני כאן כדי לעזור לך להרגיש בטוח יותר. איך אני יכול לתמוך בך? 🤗",
            "מפחדת": "אני מבין שאתה מפחדת. זה בסדר לפחד. אני כאן כדי לעזור לך להרגיש בטוחה יותר. איך אני יכול לתמוך בך? 🤗",
            "דואג": "אני רואה שאתה דואג. זה טבעי לדאוג לפעמים. אני כאן כדי לעזור לך. בוא נדבר על מה שמדאיג אותך. 💙",
            "דואגת": "אני רואה שאתה דואגת. זה טבעי לדאוג לפעמים. אני כאן כדי לעזור לך. בוא נדבר על מה שמדאיג אותך. 💙",
            "לא רוצה": "אני מבין שאתה לא רוצה לעשות את זה עכשיו. זה בסדר. אולי נוכל לנסות משהו אחר או לחזור לזה מאוחר יותר? 😊",
            "לא בא לי": "אני מבין שאתה לא מרגיש מוכן לזה עכשיו. זה בסדר. איך אני יכול לעזור לך להרגיש יותר מוכן? 🌟",
            "לא טוב לי": "אני מבין שאתה לא מרגיש טוב. זה בסדר. אני כאן כדי לעזור לך. איך אני יכול לתמוך בך? 💙",
            "רע לי": "אני מבין שאתה מרגיש רע. זה בסדר להרגיש כך. אני כאן בשבילך. איך אני יכול לעזור לך להרגיש יותר טוב? 💙"
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
            
            # Add encouraging tone
            encouragement = get_encouragement()
            full_prompt = f"{formatted_prompt}\n\n{encouragement}"
            
            logger.info(f"Generating response for strategy: {strategy}")
            
            response = multi_llm_manager.generate(
                prompt=full_prompt,
                provider=self.provider,
                temperature=0.3,  # Lower temperature for faster, focused responses
                max_tokens=150    # Much shorter responses for speed
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
def create_hebrew_mediation_chain(provider: str = None) -> HebrewMediationChain:
    """Create configured Hebrew mediation chain"""
    return HebrewMediationChain(provider=provider)