from typing import Dict, Any, List, Optional, Callable
import asyncio
from datetime import datetime

from app.ai.chains.instruction_chain import InstructionChain
from app.models.llm_config import LLMConfig


class ConfigurableInstructionChain(InstructionChain):
    """Configurable instruction chain with custom steps and conditions."""
    
    def __init__(self):
        super().__init__()
        self.custom_steps = {}
        self.conditional_logic = {}
        self.branching_rules = {}
    
    def register_custom_step(
        self, 
        step_name: str, 
        prompt_generator: Callable[[Dict[str, Any]], str],
        description: str = ""
    ):
        """Register a custom instruction step."""
        
        self.custom_steps[step_name] = {
            "prompt_generator": prompt_generator,
            "description": description,
            "created_at": datetime.utcnow().isoformat()
        }
    
    def add_conditional_logic(
        self, 
        step_name: str, 
        condition: Callable[[Dict[str, Any]], bool],
        action: Dict[str, Any]
    ):
        """Add conditional logic for step execution."""
        
        self.conditional_logic[step_name] = {
            "condition": condition,
            "action": action
        }
    
    def add_branching_rule(
        self, 
        decision_point: str, 
        branches: Dict[str, Dict[str, Any]]
    ):
        """Add branching rules for adaptive instruction paths."""
        
        self.branching_rules[decision_point] = branches
    
    async def execute_configurable_sequence(
        self,
        learning_objective: str,
        student_profile: Dict[str, Any],
        config: LLMConfig,
        sequence_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a configurable instruction sequence."""
        
        steps = sequence_config.get("steps", [])
        enable_branching = sequence_config.get("enable_branching", False)
        enable_conditions = sequence_config.get("enable_conditions", True)
        
        results = {}
        context = {
            "learning_objective": learning_objective,
            "student_profile": student_profile,
            "previous_steps": [],
            "sequence_config": sequence_config
        }
        
        i = 0
        while i < len(steps):
            step = steps[i]
            
            # Check conditional logic
            if enable_conditions and step in self.conditional_logic:
                condition_result = self._evaluate_condition(step, context)
                if not condition_result["execute"]:
                    # Skip this step or modify execution
                    if condition_result.get("skip", False):
                        i += 1
                        continue
                    elif condition_result.get("replace_with"):
                        step = condition_result["replace_with"]
            
            # Execute the step
            result = await self._execute_configurable_step(step, context, config)
            results[step] = result
            
            # Update context
            context["previous_steps"].append({
                "step": step,
                "result": result,
                "index": i
            })
            
            # Check for branching
            if enable_branching:
                branch_decision = await self._evaluate_branching(step, result, context, config)
                if branch_decision["should_branch"]:
                    new_steps = branch_decision["new_steps"]
                    # Insert new steps after current position
                    steps = steps[:i+1] + new_steps + steps[i+1:]
            
            i += 1
        
        return {
            "learning_objective": learning_objective,
            "student_profile": student_profile,
            "steps_completed": len([r for r in results.values() if "error" not in r]),
            "total_steps_attempted": len(results),
            "results": results,
            "sequence_config": sequence_config,
            "final_context": context,
            "overall_success": all("error" not in result for result in results.values())
        }
    
    async def _execute_configurable_step(
        self, 
        step: str, 
        context: Dict[str, Any], 
        config: LLMConfig
    ) -> Dict[str, Any]:
        """Execute a step that might be custom or standard."""
        
        # Check if it's a custom step
        if step in self.custom_steps:
            return await self._execute_custom_step(step, context, config)
        else:
            # Use parent class method for standard steps
            return await self._execute_step(step, context, config)
    
    async def _execute_custom_step(
        self, 
        step: str, 
        context: Dict[str, Any], 
        config: LLMConfig
    ) -> Dict[str, Any]:
        """Execute a custom instruction step."""
        
        try:
            step_info = self.custom_steps[step]
            prompt_generator = step_info["prompt_generator"]
            
            # Generate prompt using custom function
            prompt = prompt_generator(context)
            messages = [{"role": "user", "content": prompt}]
            
            response = await self.llm_manager.generate_response(messages, config, context)
            
            # Track custom step in chain history
            self.chain_history.append({
                "step": step,
                "step_type": "custom",
                "prompt": prompt,
                "response": response,
                "context": context.copy()
            })
            
            return response
        
        except Exception as e:
            return {"error": f"Custom step '{step}' failed: {str(e)}"}
    
    def _evaluate_condition(self, step: str, context: Dict[str, Any]) -> Dict[str, bool]:
        """Evaluate conditional logic for a step."""
        
        if step not in self.conditional_logic:
            return {"execute": True}
        
        try:
            condition_info = self.conditional_logic[step]
            condition_func = condition_info["condition"]
            action = condition_info["action"]
            
            # Evaluate condition
            condition_result = condition_func(context)
            
            if condition_result:
                return {"execute": True}
            else:
                # Apply the action when condition is false
                return {
                    "execute": action.get("execute", False),
                    "skip": action.get("skip", True),
                    "replace_with": action.get("replace_with")
                }
        
        except Exception as e:
            # If condition evaluation fails, proceed with execution
            return {"execute": True, "condition_error": str(e)}
    
    async def _evaluate_branching(
        self, 
        step: str, 
        result: Dict[str, Any], 
        context: Dict[str, Any], 
        config: LLMConfig
    ) -> Dict[str, Any]:
        """Evaluate if branching should occur after a step."""
        
        if step not in self.branching_rules:
            return {"should_branch": False}
        
        try:
            branches = self.branching_rules[step]
            
            # Analyze the result to determine which branch to take
            branch_decision = await self._analyze_for_branching(result, context, branches, config)
            
            return branch_decision
        
        except Exception as e:
            return {"should_branch": False, "branching_error": str(e)}
    
    async def _analyze_for_branching(
        self, 
        result: Dict[str, Any], 
        context: Dict[str, Any], 
        branches: Dict[str, Dict[str, Any]], 
        config: LLMConfig
    ) -> Dict[str, Any]:
        """Analyze result and context to determine branching path."""
        
        # Simple branching logic based on student understanding
        student_profile = context.get("student_profile", {})
        confidence = result.get("confidence_score", "medium")
        
        # Example branching logic
        if confidence == "low" and "struggling_student" in branches:
            return {
                "should_branch": True,
                "branch_taken": "struggling_student",
                "new_steps": branches["struggling_student"].get("steps", []),
                "reason": "Low confidence response detected"
            }
        elif confidence == "high" and "advanced_student" in branches:
            return {
                "should_branch": True,
                "branch_taken": "advanced_student", 
                "new_steps": branches["advanced_student"].get("steps", []),
                "reason": "High confidence, providing advanced content"
            }
        
        return {"should_branch": False}
    
    def create_personalized_sequence(self, student_profile: Dict[str, Any]) -> List[str]:
        """Create a personalized instruction sequence based on student profile."""
        
        base_sequence = ["introduce_concept", "provide_explanation", "give_examples"]
        
        # Customize based on learning style
        learning_style = student_profile.get("learning_style", "visual")
        
        if learning_style == "visual":
            base_sequence.append("provide_visual_examples")
        elif learning_style == "auditory":
            base_sequence.append("provide_audio_explanation")
        elif learning_style == "kinesthetic":
            base_sequence.append("provide_hands_on_activity")
        
        # Adjust based on difficulty level
        level = student_profile.get("level", "beginner")
        
        if level == "beginner":
            base_sequence.extend(["check_understanding", "provide_practice"])
        elif level == "intermediate":
            base_sequence.extend(["check_understanding", "provide_practice", "challenge_activity"])
        elif level == "advanced":
            base_sequence.extend(["advanced_concepts", "real_world_application", "independent_research"])
        
        # Add assessment based on time available
        time_available = student_profile.get("time_available", 30)
        if time_available >= 45:
            base_sequence.append("comprehensive_assessment")
        elif time_available >= 20:
            base_sequence.append("quick_assessment")
        
        return base_sequence
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get summary of current configuration."""
        
        return {
            "custom_steps": {
                name: {"description": info["description"], "created_at": info["created_at"]}
                for name, info in self.custom_steps.items()
            },
            "conditional_logic_count": len(self.conditional_logic),
            "branching_rules_count": len(self.branching_rules),
            "chain_history_length": len(self.chain_history)
        }
    
    def export_configuration(self) -> Dict[str, Any]:
        """Export current configuration for reuse."""
        
        # Note: This exports structure but not the actual functions
        # Functions would need to be recreated when importing
        
        return {
            "custom_steps_names": list(self.custom_steps.keys()),
            "conditional_logic_steps": list(self.conditional_logic.keys()),
            "branching_rules_steps": list(self.branching_rules.keys()),
            "configuration_summary": self.get_configuration_summary()
        }
