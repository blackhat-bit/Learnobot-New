from typing import Dict, Any, List, Optional
import openai
import asyncio
import time
from datetime import datetime

from app.models.llm_config import LLMConfig
from app.config import settings


class LLMManager:
    """Manager for Large Language Model interactions."""
    
    def __init__(self):
        self.openai_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize LLM clients."""
        
        if settings.openai_api_key:
            openai.api_key = settings.openai_api_key
            self.openai_client = openai
    
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        config: LLMConfig,
        chat_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a response using the specified LLM configuration."""
        
        start_time = time.time()
        
        try:
            if config.provider.lower() == "openai":
                response = await self._generate_openai_response(messages, config, chat_context)
            else:
                # Fallback for unsupported providers
                response = await self._generate_fallback_response(messages, config, chat_context)
            
            response["processing_time"] = time.time() - start_time
            return response
        
        except Exception as e:
            return {
                "content": "I apologize, but I'm experiencing technical difficulties. Please try again.",
                "model_used": "fallback",
                "tokens_used": 0,
                "error": str(e),
                "processing_time": time.time() - start_time
            }
    
    async def _generate_openai_response(
        self, 
        messages: List[Dict[str, str]], 
        config: LLMConfig,
        chat_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate response using OpenAI."""
        
        # Prepare system message based on context
        system_message = self._create_system_message(config, chat_context)
        
        # Prepare messages for OpenAI
        openai_messages = [{"role": "system", "content": system_message}]
        openai_messages.extend(messages)
        
        # Make API call
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: openai.ChatCompletion.create(
                model=config.model_name,
                messages=openai_messages,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                top_p=config.top_p,
                frequency_penalty=config.frequency_penalty,
                presence_penalty=config.presence_penalty
            )
        )
        
        # Extract response data
        content = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        
        # Generate additional features
        suggestions = self._generate_suggestions(content, chat_context)
        follow_up_questions = self._generate_follow_up_questions(content, chat_context)
        confidence_score = self._calculate_confidence_score(response)
        
        return {
            "content": content,
            "model_used": config.model_name,
            "tokens_used": tokens_used,
            "confidence_score": confidence_score,
            "suggestions": suggestions,
            "follow_up_questions": follow_up_questions
        }
    
    async def _generate_fallback_response(
        self, 
        messages: List[Dict[str, str]], 
        config: LLMConfig,
        chat_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a fallback response when the primary LLM is unavailable."""
        
        # Simple rule-based responses for common patterns
        user_message = messages[-1]["content"].lower() if messages else ""
        
        if any(word in user_message for word in ["hello", "hi", "hey"]):
            content = "Hello! I'm here to help you learn. What would you like to study today?"
        elif any(word in user_message for word in ["help", "how", "what"]):
            content = "I'd be happy to help! Could you tell me more specifically what you'd like to learn about?"
        elif "?" in user_message:
            content = "That's a great question! Let me think about that and provide you with a helpful explanation."
        else:
            content = "I understand you're looking to learn something new. Could you help me understand what specific topic you'd like to explore?"
        
        return {
            "content": content,
            "model_used": "fallback",
            "tokens_used": len(content.split()),
            "confidence_score": "low",
            "suggestions": ["Ask specific questions", "Provide more context", "Try different phrasing"],
            "follow_up_questions": ["What specific topic interests you?", "What's your current level?"]
        }
    
    def _create_system_message(self, config: LLMConfig, chat_context: Optional[Dict[str, Any]] = None) -> str:
        """Create system message based on configuration and context."""
        
        base_prompt = config.system_prompt or """You are an AI tutor designed to help students learn effectively. 
        Your role is to:
        - Provide clear, educational explanations
        - Encourage critical thinking
        - Adapt to the student's level
        - Ask follow-up questions to deepen understanding
        - Provide examples and practical applications
        - Be patient and supportive"""
        
        if chat_context:
            context_additions = []
            
            if chat_context.get("subject"):
                context_additions.append(f"Focus on {chat_context['subject']} topics.")
            
            if chat_context.get("difficulty_level"):
                level = chat_context["difficulty_level"]
                context_additions.append(f"Adapt explanations for {level} level students.")
            
            if chat_context.get("learning_objectives"):
                objectives = ", ".join(chat_context["learning_objectives"])
                context_additions.append(f"Help achieve these learning objectives: {objectives}")
            
            if context_additions:
                base_prompt += "\n\nAdditional context for this conversation:\n" + "\n".join(context_additions)
        
        return base_prompt
    
    def _generate_suggestions(self, content: str, chat_context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Generate helpful suggestions based on the response."""
        
        suggestions = []
        
        # Content-based suggestions
        if "example" in content.lower():
            suggestions.append("Ask for more examples")
        
        if "practice" in content.lower():
            suggestions.append("Request practice problems")
        
        if any(word in content.lower() for word in ["concept", "theory", "principle"]):
            suggestions.append("Ask for real-world applications")
        
        # Context-based suggestions
        if chat_context and chat_context.get("subject"):
            subject = chat_context["subject"]
            suggestions.append(f"Explore related {subject} topics")
        
        # Default suggestions
        if not suggestions:
            suggestions = [
                "Ask for clarification",
                "Request additional examples",
                "Explore related topics"
            ]
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    def _generate_follow_up_questions(self, content: str, chat_context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Generate follow-up questions to encourage deeper learning."""
        
        questions = []
        
        # Content-based questions
        if "because" in content.lower() or "due to" in content.lower():
            questions.append("Can you think of other factors that might be involved?")
        
        if "example" in content.lower():
            questions.append("Can you come up with your own example?")
        
        if any(word in content.lower() for word in ["process", "step", "method"]):
            questions.append("Which step do you think is most important and why?")
        
        # Subject-specific questions
        if chat_context and chat_context.get("subject"):
            subject = chat_context["subject"].lower()
            
            if "math" in subject:
                questions.append("Can you solve a similar problem?")
            elif "science" in subject:
                questions.append("What do you predict would happen if we changed one variable?")
            elif "history" in subject:
                questions.append("How do you think this event influenced what came after?")
            elif "language" in subject:
                questions.append("Can you use this in a sentence of your own?")
        
        # Default questions
        if not questions:
            questions = [
                "What questions do you have about this?",
                "How would you explain this to someone else?",
                "What would you like to explore next?"
            ]
        
        return questions[:2]  # Limit to 2 questions
    
    def _calculate_confidence_score(self, response: Any) -> str:
        """Calculate confidence score based on model response."""
        
        # This is a simplified implementation
        # In a real system, you might analyze various factors:
        # - Token probabilities
        # - Response length
        # - Presence of uncertainty markers
        
        try:
            # For OpenAI responses, we can use finish_reason as an indicator
            finish_reason = response.choices[0].finish_reason
            
            if finish_reason == "stop":
                return "high"
            elif finish_reason == "length":
                return "medium"
            else:
                return "low"
        
        except:
            return "medium"
    
    async def generate_educational_content(
        self, 
        topic: str, 
        difficulty_level: str, 
        content_type: str,
        config: LLMConfig
    ) -> Dict[str, Any]:
        """Generate educational content for a specific topic."""
        
        prompts = {
            "explanation": f"Provide a clear, {difficulty_level}-level explanation of {topic}.",
            "quiz": f"Create a {difficulty_level} quiz about {topic} with 5 questions.",
            "summary": f"Create a comprehensive summary of {topic} suitable for {difficulty_level} students.",
            "examples": f"Provide practical examples of {topic} with explanations."
        }
        
        prompt = prompts.get(content_type, prompts["explanation"])
        
        messages = [{"role": "user", "content": prompt}]
        
        return await self.generate_response(messages, config)
    
    async def provide_hint(
        self, 
        question: str, 
        student_answer: str, 
        hint_level: str,
        config: LLMConfig
    ) -> Dict[str, Any]:
        """Provide a hint for a student's question."""
        
        hint_prompts = {
            "low": "Provide a very subtle hint without giving away the answer.",
            "medium": "Provide a helpful hint that guides toward the solution.",
            "high": "Provide a detailed hint that clearly points toward the answer."
        }
        
        hint_instruction = hint_prompts.get(hint_level, hint_prompts["medium"])
        
        prompt = f"""Student question: {question}
Student's current answer/attempt: {student_answer}

{hint_instruction}"""
        
        messages = [{"role": "user", "content": prompt}]
        
        return await self.generate_response(messages, config)
