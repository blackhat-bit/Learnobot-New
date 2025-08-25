from typing import Dict, Any, List, Optional, Callable
from enum import Enum
import asyncio
from datetime import datetime, timedelta

from app.ai.llm_manager import LLMManager
from app.models.llm_config import LLMConfig


class MediationStrategy(Enum):
    """Types of mediation strategies for AI tutoring."""
    SOCRATIC = "socratic"  # Guide through questions
    SCAFFOLDING = "scaffolding"  # Provide structured support
    MODELING = "modeling"  # Show examples and demonstrations
    COLLABORATIVE = "collaborative"  # Work together on problems
    INQUIRY_BASED = "inquiry_based"  # Student-led exploration
    DIRECT_INSTRUCTION = "direct_instruction"  # Clear explanations
    ADAPTIVE = "adaptive"  # Change strategy based on student response


class LearningDifficulty(Enum):
    """Types of learning difficulties to address."""
    COMPREHENSION = "comprehension"  # Understanding concepts
    RETENTION = "retention"  # Remembering information
    APPLICATION = "application"  # Using knowledge practically
    MOTIVATION = "motivation"  # Engagement and interest
    CONFUSION = "confusion"  # Unclear understanding
    OVERWHELM = "overwhelm"  # Too much information at once


class MediationStrategies:
    """Strategies for mediating learning difficulties and enhancing education."""
    
    def __init__(self):
        self.llm_manager = LLMManager()
        self.strategy_history = []
        self.effectiveness_tracking = {}
    
    async def mediate_learning_difficulty(
        self,
        difficulty: LearningDifficulty,
        student_context: Dict[str, Any],
        content_context: Dict[str, Any],
        config: LLMConfig,
        preferred_strategy: Optional[MediationStrategy] = None
    ) -> Dict[str, Any]:
        """Mediate a specific learning difficulty."""
        
        # Select strategy based on difficulty and context
        strategy = preferred_strategy or self._select_optimal_strategy(
            difficulty, student_context, content_context
        )
        
        # Execute mediation
        result = await self._execute_mediation_strategy(
            strategy, difficulty, student_context, content_context, config
        )
        
        # Track strategy usage and effectiveness
        self._track_strategy_usage(strategy, difficulty, result)
        
        return result
    
    def _select_optimal_strategy(
        self,
        difficulty: LearningDifficulty,
        student_context: Dict[str, Any],
        content_context: Dict[str, Any]
    ) -> MediationStrategy:
        """Select the most appropriate mediation strategy."""
        
        # Strategy selection logic based on difficulty type
        strategy_mappings = {
            LearningDifficulty.COMPREHENSION: self._select_comprehension_strategy,
            LearningDifficulty.RETENTION: self._select_retention_strategy,
            LearningDifficulty.APPLICATION: self._select_application_strategy,
            LearningDifficulty.MOTIVATION: self._select_motivation_strategy,
            LearningDifficulty.CONFUSION: self._select_confusion_strategy,
            LearningDifficulty.OVERWHELM: self._select_overwhelm_strategy
        }
        
        selector = strategy_mappings.get(difficulty)
        if selector:
            return selector(student_context, content_context)
        
        return MediationStrategy.ADAPTIVE  # Default fallback
    
    def _select_comprehension_strategy(
        self, student_context: Dict[str, Any], content_context: Dict[str, Any]
    ) -> MediationStrategy:
        """Select strategy for comprehension difficulties."""
        
        learning_style = student_context.get("learning_style", "visual")
        complexity = content_context.get("complexity", "medium")
        
        if complexity == "high":
            return MediationStrategy.SCAFFOLDING
        elif learning_style == "kinesthetic":
            return MediationStrategy.COLLABORATIVE
        else:
            return MediationStrategy.SOCRATIC
    
    def _select_retention_strategy(
        self, student_context: Dict[str, Any], content_context: Dict[str, Any]
    ) -> MediationStrategy:
        """Select strategy for retention difficulties."""
        
        # Focus on scaffolding and modeling for retention
        return MediationStrategy.SCAFFOLDING
    
    def _select_application_strategy(
        self, student_context: Dict[str, Any], content_context: Dict[str, Any]
    ) -> MediationStrategy:
        """Select strategy for application difficulties."""
        
        return MediationStrategy.MODELING
    
    def _select_motivation_strategy(
        self, student_context: Dict[str, Any], content_context: Dict[str, Any]
    ) -> MediationStrategy:
        """Select strategy for motivation difficulties."""
        
        return MediationStrategy.INQUIRY_BASED
    
    def _select_confusion_strategy(
        self, student_context: Dict[str, Any], content_context: Dict[str, Any]
    ) -> MediationStrategy:
        """Select strategy for confusion."""
        
        return MediationStrategy.DIRECT_INSTRUCTION
    
    def _select_overwhelm_strategy(
        self, student_context: Dict[str, Any], content_context: Dict[str, Any]
    ) -> MediationStrategy:
        """Select strategy for overwhelm."""
        
        return MediationStrategy.SCAFFOLDING
    
    async def _execute_mediation_strategy(
        self,
        strategy: MediationStrategy,
        difficulty: LearningDifficulty,
        student_context: Dict[str, Any],
        content_context: Dict[str, Any],
        config: LLMConfig
    ) -> Dict[str, Any]:
        """Execute a specific mediation strategy."""
        
        strategy_executors = {
            MediationStrategy.SOCRATIC: self._execute_socratic_strategy,
            MediationStrategy.SCAFFOLDING: self._execute_scaffolding_strategy,
            MediationStrategy.MODELING: self._execute_modeling_strategy,
            MediationStrategy.COLLABORATIVE: self._execute_collaborative_strategy,
            MediationStrategy.INQUIRY_BASED: self._execute_inquiry_strategy,
            MediationStrategy.DIRECT_INSTRUCTION: self._execute_direct_instruction,
            MediationStrategy.ADAPTIVE: self._execute_adaptive_strategy
        }
        
        executor = strategy_executors.get(strategy)
        if executor:
            return await executor(difficulty, student_context, content_context, config)
        
        # Fallback to direct instruction
        return await self._execute_direct_instruction(difficulty, student_context, content_context, config)
    
    async def _execute_socratic_strategy(
        self,
        difficulty: LearningDifficulty,
        student_context: Dict[str, Any],
        content_context: Dict[str, Any],
        config: LLMConfig
    ) -> Dict[str, Any]:
        """Execute Socratic method - guide through questions."""
        
        topic = content_context.get("topic", "the current topic")
        student_level = student_context.get("level", "beginner")
        
        prompt = f"""Use the Socratic method to help a {student_level} student understand {topic}. 
        The student is experiencing {difficulty.value} difficulties.

Create a sequence of guiding questions that:
1. Start with what the student might already know
2. Build understanding step by step
3. Help the student discover the answer themselves
4. Encourage critical thinking
5. Address the specific difficulty: {difficulty.value}

Provide 3-5 thoughtful questions with brief explanations of why each question helps."""
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.llm_manager.generate_response(messages, config)
        
        response["strategy_used"] = strategy.SOCRATIC.value
        response["mediation_focus"] = difficulty.value
        
        return response
    
    async def _execute_scaffolding_strategy(
        self,
        difficulty: LearningDifficulty,
        student_context: Dict[str, Any],
        content_context: Dict[str, Any],
        config: LLMConfig
    ) -> Dict[str, Any]:
        """Execute scaffolding strategy - provide structured support."""
        
        topic = content_context.get("topic", "the current topic")
        student_level = student_context.get("level", "beginner")
        
        prompt = f"""Create a scaffolded learning approach for a {student_level} student learning {topic}.
        The student is experiencing {difficulty.value} difficulties.

Provide a structured support framework that:
1. Breaks the concept into manageable chunks
2. Provides temporary supports that can be gradually removed
3. Offers clear steps and milestones
4. Includes practice opportunities at each level
5. Addresses the {difficulty.value} difficulty specifically

Create a step-by-step scaffold with 4-6 progressive levels."""
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.llm_manager.generate_response(messages, config)
        
        response["strategy_used"] = MediationStrategy.SCAFFOLDING.value
        response["mediation_focus"] = difficulty.value
        
        return response
    
    async def _execute_modeling_strategy(
        self,
        difficulty: LearningDifficulty,
        student_context: Dict[str, Any],
        content_context: Dict[str, Any],
        config: LLMConfig
    ) -> Dict[str, Any]:
        """Execute modeling strategy - show examples and demonstrations."""
        
        topic = content_context.get("topic", "the current topic")
        student_level = student_context.get("level", "beginner")
        
        prompt = f"""Demonstrate {topic} for a {student_level} student using modeling techniques.
        The student is experiencing {difficulty.value} difficulties.

Provide:
1. A clear, step-by-step demonstration
2. Think-aloud process showing your reasoning
3. Multiple examples showing variation
4. Common mistakes and how to avoid them
5. Practice opportunities for the student to try

Focus on addressing {difficulty.value} through clear modeling."""
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.llm_manager.generate_response(messages, config)
        
        response["strategy_used"] = MediationStrategy.MODELING.value
        response["mediation_focus"] = difficulty.value
        
        return response
    
    async def _execute_collaborative_strategy(
        self,
        difficulty: LearningDifficulty,
        student_context: Dict[str, Any],
        content_context: Dict[str, Any],
        config: LLMConfig
    ) -> Dict[str, Any]:
        """Execute collaborative strategy - work together on problems."""
        
        topic = content_context.get("topic", "the current topic")
        student_level = student_context.get("level", "beginner")
        
        prompt = f"""Design a collaborative learning experience for {topic} with a {student_level} student.
        The student is experiencing {difficulty.value} difficulties.

Create an interactive approach where you and the student:
1. Work together as partners on the problem
2. Share the thinking process
3. Build on each other's ideas
4. Solve problems together step by step
5. Support each other through difficulties

Design 2-3 collaborative activities that address {difficulty.value}."""
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.llm_manager.generate_response(messages, config)
        
        response["strategy_used"] = MediationStrategy.COLLABORATIVE.value
        response["mediation_focus"] = difficulty.value
        
        return response
    
    async def _execute_inquiry_strategy(
        self,
        difficulty: LearningDifficulty,
        student_context: Dict[str, Any],
        content_context: Dict[str, Any],
        config: LLMConfig
    ) -> Dict[str, Any]:
        """Execute inquiry-based strategy - student-led exploration."""
        
        topic = content_context.get("topic", "the current topic")
        student_level = student_context.get("level", "beginner")
        
        prompt = f"""Design an inquiry-based learning experience for {topic} for a {student_level} student.
        The student is experiencing {difficulty.value} difficulties.

Create an approach that:
1. Starts with the student's questions and curiosity
2. Guides them to investigate and discover
3. Provides resources and tools for exploration
4. Encourages hypothesis formation and testing
5. Supports self-directed learning

Focus on making the inquiry engaging and addressing {difficulty.value}."""
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.llm_manager.generate_response(messages, config)
        
        response["strategy_used"] = MediationStrategy.INQUIRY_BASED.value
        response["mediation_focus"] = difficulty.value
        
        return response
    
    async def _execute_direct_instruction(
        self,
        difficulty: LearningDifficulty,
        student_context: Dict[str, Any],
        content_context: Dict[str, Any],
        config: LLMConfig
    ) -> Dict[str, Any]:
        """Execute direct instruction strategy - clear explanations."""
        
        topic = content_context.get("topic", "the current topic")
        student_level = student_context.get("level", "beginner")
        
        prompt = f"""Provide direct, clear instruction on {topic} for a {student_level} student.
        The student is experiencing {difficulty.value} difficulties.

Give a structured explanation that:
1. States learning objectives clearly
2. Provides clear, sequential explanations
3. Uses concrete examples and non-examples
4. Checks for understanding frequently
5. Includes guided practice

Make the instruction clear and focused on resolving {difficulty.value}."""
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.llm_manager.generate_response(messages, config)
        
        response["strategy_used"] = MediationStrategy.DIRECT_INSTRUCTION.value
        response["mediation_focus"] = difficulty.value
        
        return response
    
    async def _execute_adaptive_strategy(
        self,
        difficulty: LearningDifficulty,
        student_context: Dict[str, Any],
        content_context: Dict[str, Any],
        config: LLMConfig
    ) -> Dict[str, Any]:
        """Execute adaptive strategy - change approach based on response."""
        
        # Start with a mixed approach and indicate adaptation capability
        topic = content_context.get("topic", "the current topic")
        student_level = student_context.get("level", "beginner")
        
        prompt = f"""Create an adaptive learning approach for {topic} for a {student_level} student.
        The student is experiencing {difficulty.value} difficulties.

Design a flexible approach that:
1. Starts with one teaching method
2. Monitors student response and understanding
3. Adapts teaching style based on student needs
4. Combines multiple strategies as needed
5. Provides clear indicators for when to change approach

Include decision points for adaptation and multiple backup strategies."""
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.llm_manager.generate_response(messages, config)
        
        response["strategy_used"] = MediationStrategy.ADAPTIVE.value
        response["mediation_focus"] = difficulty.value
        
        return response
    
    def _track_strategy_usage(
        self,
        strategy: MediationStrategy,
        difficulty: LearningDifficulty,
        result: Dict[str, Any]
    ):
        """Track strategy usage and effectiveness."""
        
        usage_record = {
            "strategy": strategy.value,
            "difficulty": difficulty.value,
            "timestamp": datetime.utcnow().isoformat(),
            "success": "error" not in result,
            "tokens_used": result.get("tokens_used", 0),
            "confidence": result.get("confidence_score", "unknown")
        }
        
        self.strategy_history.append(usage_record)
        
        # Update effectiveness tracking
        key = f"{strategy.value}_{difficulty.value}"
        if key not in self.effectiveness_tracking:
            self.effectiveness_tracking[key] = {
                "total_uses": 0,
                "successful_uses": 0,
                "average_confidence": []
            }
        
        tracking = self.effectiveness_tracking[key]
        tracking["total_uses"] += 1
        
        if usage_record["success"]:
            tracking["successful_uses"] += 1
        
        if result.get("confidence_score"):
            tracking["average_confidence"].append(result["confidence_score"])
    
    def get_strategy_effectiveness_report(self) -> Dict[str, Any]:
        """Get report on strategy effectiveness."""
        
        report = {
            "total_mediations": len(self.strategy_history),
            "strategy_performance": {},
            "difficulty_patterns": {},
            "recommendations": []
        }
        
        # Calculate performance metrics
        for key, data in self.effectiveness_tracking.items():
            strategy, difficulty = key.split("_", 1)
            
            success_rate = data["successful_uses"] / data["total_uses"] if data["total_uses"] > 0 else 0
            
            report["strategy_performance"][key] = {
                "strategy": strategy,
                "difficulty": difficulty,
                "total_uses": data["total_uses"],
                "success_rate": success_rate,
                "sample_size": data["total_uses"]
            }
        
        # Generate recommendations
        report["recommendations"] = self._generate_strategy_recommendations()
        
        return report
    
    def _generate_strategy_recommendations(self) -> List[str]:
        """Generate recommendations based on strategy effectiveness."""
        
        recommendations = []
        
        if not self.effectiveness_tracking:
            return ["No strategy data available yet. Continue using mediation to build effectiveness data."]
        
        # Find most and least effective strategies
        effectiveness_scores = {}
        for key, data in self.effectiveness_tracking.items():
            if data["total_uses"] >= 3:  # Only consider strategies with sufficient data
                success_rate = data["successful_uses"] / data["total_uses"]
                effectiveness_scores[key] = success_rate
        
        if effectiveness_scores:
            best_strategy = max(effectiveness_scores.items(), key=lambda x: x[1])
            worst_strategy = min(effectiveness_scores.items(), key=lambda x: x[1])
            
            recommendations.append(
                f"Most effective combination: {best_strategy[0]} with {best_strategy[1]*100:.1f}% success rate"
            )
            
            if worst_strategy[1] < 0.7:  # Less than 70% success
                recommendations.append(
                    f"Consider alternatives to: {worst_strategy[0]} (only {worst_strategy[1]*100:.1f}% success rate)"
                )
        
        return recommendations
