from typing import Dict, Any, List, Optional
import asyncio

from app.ai.llm_manager import LLMManager
from app.models.llm_config import LLMConfig


class InstructionChain:
    """Chain for educational instruction and tutoring interactions."""
    
    def __init__(self):
        self.llm_manager = LLMManager()
        self.chain_history = []
    
    async def execute_instruction_sequence(
        self,
        learning_objective: str,
        student_level: str,
        config: LLMConfig,
        steps: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Execute a sequence of instructional steps."""
        
        if not steps:
            steps = [
                "introduce_concept",
                "provide_explanation", 
                "give_examples",
                "check_understanding",
                "provide_practice"
            ]
        
        results = {}
        context = {
            "learning_objective": learning_objective,
            "student_level": student_level,
            "previous_steps": []
        }
        
        for step in steps:
            result = await self._execute_step(step, context, config)
            results[step] = result
            context["previous_steps"].append({
                "step": step,
                "result": result
            })
        
        return {
            "learning_objective": learning_objective,
            "student_level": student_level,
            "steps_completed": len(steps),
            "results": results,
            "overall_success": all("error" not in result for result in results.values())
        }
    
    async def _execute_step(
        self, 
        step: str, 
        context: Dict[str, Any], 
        config: LLMConfig
    ) -> Dict[str, Any]:
        """Execute a single instruction step."""
        
        step_prompts = {
            "introduce_concept": self._create_introduction_prompt,
            "provide_explanation": self._create_explanation_prompt,
            "give_examples": self._create_examples_prompt,
            "check_understanding": self._create_understanding_check_prompt,
            "provide_practice": self._create_practice_prompt,
            "assess_knowledge": self._create_assessment_prompt,
            "provide_feedback": self._create_feedback_prompt
        }
        
        if step not in step_prompts:
            return {"error": f"Unknown step: {step}"}
        
        prompt = step_prompts[step](context)
        messages = [{"role": "user", "content": prompt}]
        
        response = await self.llm_manager.generate_response(messages, config, context)
        
        # Track step in chain history
        self.chain_history.append({
            "step": step,
            "prompt": prompt,
            "response": response,
            "context": context.copy()
        })
        
        return response
    
    def _create_introduction_prompt(self, context: Dict[str, Any]) -> str:
        """Create prompt for introducing a concept."""
        
        return f"""You are introducing the concept of "{context['learning_objective']}" to a {context['student_level']} level student.

Create an engaging introduction that:
1. Captures the student's attention
2. Explains why this concept is important
3. Provides a simple, clear definition
4. Connects to what they might already know

Keep it conversational and encouraging."""
    
    def _create_explanation_prompt(self, context: Dict[str, Any]) -> str:
        """Create prompt for detailed explanation."""
        
        previous_content = self._get_previous_content(context)
        
        return f"""Building on the introduction, provide a comprehensive explanation of "{context['learning_objective']}" for a {context['student_level']} level student.

Previous context:
{previous_content}

Your explanation should:
1. Break down the concept into digestible parts
2. Use clear, age-appropriate language
3. Build logically from simple to more complex ideas
4. Include relevant analogies or metaphors
5. Anticipate and address common misconceptions"""
    
    def _create_examples_prompt(self, context: Dict[str, Any]) -> str:
        """Create prompt for providing examples."""
        
        previous_content = self._get_previous_content(context)
        
        return f"""Provide practical examples of "{context['learning_objective']}" for a {context['student_level']} level student.

Previous context:
{previous_content}

Include:
1. 2-3 clear, relatable examples
2. Step-by-step walkthrough of at least one example
3. Real-world applications the student can connect to
4. Varying difficulty levels within the examples"""
    
    def _create_understanding_check_prompt(self, context: Dict[str, Any]) -> str:
        """Create prompt for checking understanding."""
        
        previous_content = self._get_previous_content(context)
        
        return f"""Create questions to check the student's understanding of "{context['learning_objective']}" at a {context['student_level']} level.

Previous content covered:
{previous_content}

Generate:
1. 2-3 questions that test comprehension
2. Include both simple recall and application questions
3. Make questions engaging and thought-provoking
4. Provide guidance on what constitutes a good answer"""
    
    def _create_practice_prompt(self, context: Dict[str, Any]) -> str:
        """Create prompt for practice activities."""
        
        previous_content = self._get_previous_content(context)
        
        return f"""Design practice activities for "{context['learning_objective']}" appropriate for a {context['student_level']} level student.

Previous learning:
{previous_content}

Create:
1. 2-3 practice problems or activities
2. Varying difficulty levels
3. Clear instructions for each activity
4. Hints for getting started
5. What the student should accomplish"""
    
    def _create_assessment_prompt(self, context: Dict[str, Any]) -> str:
        """Create prompt for knowledge assessment."""
        
        previous_content = self._get_previous_content(context)
        
        return f"""Create an assessment to evaluate understanding of "{context['learning_objective']}" for a {context['student_level']} level student.

Learning sequence so far:
{previous_content}

Assessment should include:
1. Multiple choice questions (3-4)
2. Short answer questions (2-3)
3. One application/problem-solving question
4. Clear rubric for evaluation
5. Estimated time to complete"""
    
    def _create_feedback_prompt(self, context: Dict[str, Any]) -> str:
        """Create prompt for providing feedback."""
        
        return f"""Provide constructive feedback on a student's learning progress with "{context['learning_objective']}" at a {context['student_level']} level.

Create a feedback framework that:
1. Acknowledges what the student has learned well
2. Identifies areas for improvement
3. Suggests specific next steps
4. Encourages continued learning
5. Provides additional resources if needed"""
    
    def _get_previous_content(self, context: Dict[str, Any]) -> str:
        """Extract relevant content from previous steps."""
        
        previous_steps = context.get("previous_steps", [])
        
        if not previous_steps:
            return "This is the first step in the learning sequence."
        
        content_summary = []
        for step_data in previous_steps:
            step_name = step_data["step"]
            content = step_data["result"].get("content", "")
            if content:
                content_summary.append(f"{step_name}: {content[:200]}...")
        
        return "\n".join(content_summary) if content_summary else "Previous steps completed."
    
    async def create_adaptive_lesson(
        self,
        topic: str,
        student_level: str,
        learning_style: str,
        time_available: int,  # minutes
        config: LLMConfig
    ) -> Dict[str, Any]:
        """Create an adaptive lesson based on student parameters."""
        
        # Determine lesson structure based on time available
        if time_available <= 15:
            steps = ["introduce_concept", "provide_explanation", "give_examples"]
        elif time_available <= 30:
            steps = ["introduce_concept", "provide_explanation", "give_examples", "check_understanding"]
        else:
            steps = ["introduce_concept", "provide_explanation", "give_examples", 
                    "check_understanding", "provide_practice", "assess_knowledge"]
        
        # Adapt context for learning style
        context = {
            "learning_objective": topic,
            "student_level": student_level,
            "learning_style": learning_style,
            "time_available": time_available,
            "previous_steps": []
        }
        
        # Execute the lesson
        lesson_result = await self.execute_instruction_sequence(
            topic, student_level, config, steps
        )
        
        # Add adaptive metadata
        lesson_result["adaptive_info"] = {
            "learning_style": learning_style,
            "time_allocated": time_available,
            "steps_selected": steps,
            "adaptation_reason": f"Tailored for {learning_style} learner with {time_available} minutes"
        }
        
        return lesson_result
    
    def get_chain_summary(self) -> Dict[str, Any]:
        """Get summary of the instruction chain execution."""
        
        if not self.chain_history:
            return {"message": "No instruction chain executed yet"}
        
        total_steps = len(self.chain_history)
        successful_steps = len([step for step in self.chain_history if "error" not in step["response"]])
        
        return {
            "total_steps": total_steps,
            "successful_steps": successful_steps,
            "success_rate": successful_steps / total_steps if total_steps > 0 else 0,
            "steps_executed": [step["step"] for step in self.chain_history],
            "overall_tokens_used": sum(step["response"].get("tokens_used", 0) for step in self.chain_history)
        }
    
    def clear_history(self):
        """Clear the chain execution history."""
        self.chain_history = []
