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

class ConversationStateMemory(ConversationSummaryBufferMemory):
    """Enhanced memory that tracks mediation state and strategy attempts"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.failed_strategies = []
        self.comprehension_indicators = []
        self.attempt_count = 0
        
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
            "highlight_keywords",    # הדגשת מילות מפתח
            "guided_reading",       # הנחיה לקריאה בעיון
            "provide_example",      # מתן דוגמה
            "breakdown_steps",      # פירוק לשלבים
            "detailed_explanation", # הסבר מפורט
            "teacher_escalation"    # פנייה למורה
        ]
        
        # Hebrew strategy templates
        self.strategy_templates = {
            "highlight_keywords": PromptTemplate(
                input_variables=["instruction"],
                template="""בוא נסתכל על המילים החשובות בהוראה:

הוראה: {instruction}

זה מה שחשוב לשים לב אליו:
• מילות פעולה (מה לעשות): 
• מילות שאלה (מה מחפשים):
• מילים מיוחדות שחשובות להבין:

איזו מילה נראית לך הכי חשובה כדי להבין מה צריך לעשות?"""
            ),
            
            "guided_reading": PromptTemplate(
                input_variables=["instruction"],
                template="""בוא נקרא שוב את ההוראה בזהירות, מילה אחר מילה:

{instruction}

עכשיו, בוא נחלק את זה לחלקים:
1. מה מבקשים ממך לעשות? (הפעולה)
2. על מה או על מי? (הנושא)  
3. איך אמורה להראות התשובה? (הפורמט)

קרא עוד פעם ונסה לענות על השאלה הראשונה: מה הפעולה שאתה צריך לעשות?"""
            ),
            
            "provide_example": PromptTemplate(
                input_variables=["instruction", "concept"],
                template="""אני אתן לך דוגמה שתעזור להבין:

בהוראה שלך: {instruction}

בוא נחשוב על זה ככה - זה כמו ש{concept}

דוגמה מחיי היומיום:
[דוגמה פשוטה ורלוונטית]

עכשיו, כשאתה מבין את הדוגמה, נסה לחזור להוראה המקורית. מה אתה צריך לעשות?"""
            ),
            
            "breakdown_steps": PromptTemplate(
                input_variables=["instruction"],
                template="""בוא נפרק את המשימה לחלקים קטנים וקלים:

ההוראה: {instruction}

השלבים:
1. צעד ראשון: [פעולה פשוטה ראשונה]
2. צעד שני: [פעולה פשוטה שנייה]  
3. צעד שלישי: [פעולה פשוטה שלישית]

בוא נתחיל עם הצעד הראשון בלבד. מה אתה צריך לעשות בשלב הראשון?"""
            )
        }

    def route_strategy(self, comprehension_level: str, failed_strategies: List[str], 
                      mode: str = "practice") -> Optional[str]:
        """Route to next appropriate strategy based on Hebrew decision tree"""
        
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
    
    input_keys = ["instruction", "student_response", "mode", "student_context"]
    output_keys = ["response", "strategy_used", "comprehension_level"]
    
    def __init__(self, provider: str = None):
        super().__init__()
        self.provider = provider
        self.router = HebrewMediationRouter()
        self.memory = ConversationStateMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
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
            return {
                "response": "אני כאן כדי לעזור לך. בוא ננסה שוב - איך אני יכול לעזור לך עם המשימה?",
                "strategy_used": "fallback",
                "comprehension_level": "error"
            }
    
    def _execute_strategy(self, strategy: str, instruction: str, student_context: Dict) -> str:
        """Execute specific mediation strategy"""
        
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
        formatted_prompt = template.format(**template_vars)
        
        # Add encouraging tone
        encouragement = get_encouragement()
        
        response = multi_llm_manager.generate(
            prompt=f"{formatted_prompt}\n\n{encouragement}",
            provider=self.provider,
            temperature=0.7,
            max_tokens=1024
        )
        
        return response
    
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
        self.memory = ConversationStateMemory(
            memory_key="chat_history", 
            return_messages=True
        )

# Factory function for easy integration
def create_hebrew_mediation_chain(provider: str = None) -> HebrewMediationChain:
    """Create configured Hebrew mediation chain"""
    return HebrewMediationChain(provider=provider)