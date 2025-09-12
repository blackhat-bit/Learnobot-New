# app/services/hebrew_mediation_service.py
from sqlalchemy.orm import Session
from app.models.conversation_state import ConversationState
from app.models.chat import ChatSession, InteractionMode
from app.ai.chains.hebrew_mediation_chain import create_hebrew_mediation_chain
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class HebrewMediationService:
    """Service for managing Hebrew conversation mediation"""
    
    def __init__(self):
        self.mediation_chains = {}  # Cache chains by session_id
    
    def get_or_create_conversation_state(self, db: Session, session_id: int) -> ConversationState:
        """Get existing conversation state or create new one"""
        
        state = db.query(ConversationState).filter(
            ConversationState.session_id == session_id
        ).first()
        
        if not state:
            state = ConversationState(session_id=session_id)
            db.add(state)
            db.commit()
            db.refresh(state)
            
        return state
    
    def get_mediation_chain(self, session_id: int, provider: str = None):
        """Get or create mediation chain for session"""
        
        if session_id not in self.mediation_chains:
            self.mediation_chains[session_id] = create_hebrew_mediation_chain(provider)
            
        return self.mediation_chains[session_id]
    
    def process_mediated_response(
        self, 
        db: Session,
        session_id: int,
        instruction: str,
        student_response: str = "",
        provider: str = None
    ) -> Dict[str, Any]:
        """Process message through Hebrew mediation system"""
        
        try:
            # Get session and student context
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if not session:
                raise ValueError(f"Session {session_id} not found")
            
            # Get or create conversation state
            conv_state = self.get_or_create_conversation_state(db, session_id)
            
            # Update conversation state with current instruction if new
            if conv_state.current_instruction != instruction:
                conv_state.reset_for_new_instruction()
                conv_state.current_instruction = instruction
                
            # Prepare student context
            student = session.student
            student_context = {
                "name": student.full_name,
                "grade": student.grade,
                "difficulty_level": student.difficulty_level,
                "difficulties": student.difficulties_description,
                "language_preference": student.user.language_preference
            }
            
            # Get mediation chain
            chain = self.get_mediation_chain(session_id, provider)
            
            # Prepare chain inputs
            chain_inputs = {
                "instruction": instruction,
                "student_response": student_response,
                "mode": session.mode.value,
                "student_context": student_context
            }
            
            # Execute mediation chain
            result = chain._call(chain_inputs)
            
            # Update conversation state based on result
            strategy_used = result.get("strategy_used", "unknown")
            comprehension_level = result.get("comprehension_level", "unknown")
            
            conv_state.current_strategy = strategy_used
            conv_state.attempt_count += 1
            conv_state.update_comprehension(comprehension_level)
            
            # Mark strategy as failed if student still confused
            if comprehension_level == "confused":
                conv_state.add_failed_strategy(strategy_used)
            
            # Save state updates
            db.commit()
            
            return {
                "response": result.get("response", "אני כאן לעזור לך"),
                "strategy_used": strategy_used,
                "comprehension_level": comprehension_level,
                "attempt_count": conv_state.attempt_count,
                "failed_strategies": conv_state.get_failed_strategies()
            }
            
        except Exception as e:
            logger.error(f"Error in Hebrew mediation service: {str(e)}")
            return {
                "response": "מצטער, נתקלתי בבעיה. אנא נסה שוב או פנה למורה.",
                "strategy_used": "error_fallback",
                "comprehension_level": "error",
                "attempt_count": 0,
                "failed_strategies": []
            }
    
    def should_use_mediation(self, session: ChatSession, assistance_type: str = None) -> bool:
        """Determine if Hebrew mediation should be used"""
        
        # Always use mediation for Practice mode in Agent Selection
        if session.mode == InteractionMode.PRACTICE and not assistance_type:
            return True
            
        # Use mediation for Test mode (limited attempts)
        if session.mode == InteractionMode.TEST:
            return True
            
        return False
    
    def reset_session_chain(self, session_id: int):
        """Reset mediation chain for new conversation"""
        if session_id in self.mediation_chains:
            self.mediation_chains[session_id].reset_conversation()
    
    def cleanup_session(self, session_id: int):
        """Cleanup session resources"""
        if session_id in self.mediation_chains:
            del self.mediation_chains[session_id]

# Global service instance
hebrew_mediation_service = HebrewMediationService()