# app/ai/mediation_strategies.py
from enum import Enum
from typing import List, Dict, Optional

class MediationStrategy(Enum):
    BREAKDOWN = "breakdown"
    EXAMPLE = "example"
    EXPLAIN = "explain"
    HIGHLIGHT_KEYWORDS = "highlight_keywords"
    REREAD = "reread"
    SIMPLIFY = "simplify"

class MediationManager:
    """Manages pedagogical mediation strategies based on teacher practices"""
    
    def __init__(self):
        self.strategies_hierarchy = [
            MediationStrategy.HIGHLIGHT_KEYWORDS,
            MediationStrategy.REREAD,
            MediationStrategy.BREAKDOWN,
            MediationStrategy.EXAMPLE,
            MediationStrategy.EXPLAIN,
            MediationStrategy.SIMPLIFY
        ]
        self.max_attempts = {
            "practice": float('inf'),
            "test": 3
        }
    
    def get_next_strategy(self, 
                         failed_strategies: List[MediationStrategy], 
                         mode: str = "practice") -> Optional[MediationStrategy]:
        """Get the next appropriate strategy based on what has been tried"""
        
        if mode == "test" and len(failed_strategies) >= self.max_attempts["test"]:
            return None
        
        for strategy in self.strategies_hierarchy:
            if strategy not in failed_strategies:
                return strategy
        
        # In practice mode, cycle back to beginning
        if mode == "practice":
            return self.strategies_hierarchy[0]
        
        return None
    
    def apply_strategy(self, 
                      strategy: MediationStrategy, 
                      instruction: str, 
                      processor) -> str:
        """Apply a specific mediation strategy"""
        
        if strategy == MediationStrategy.BREAKDOWN:
            return processor.breakdown_instruction(instruction, 3)
        elif strategy == MediationStrategy.EXAMPLE:
            return processor.provide_example(instruction, "main concept")
        elif strategy == MediationStrategy.EXPLAIN:
            return processor.explain_instruction(instruction, 3)
        elif strategy == MediationStrategy.HIGHLIGHT_KEYWORDS:
            return self._highlight_keywords(instruction)
        elif strategy == MediationStrategy.REREAD:
            return f"Let's read the instruction again carefully:\n\n{instruction}\n\nWhat do you understand now?"
        elif strategy == MediationStrategy.SIMPLIFY:
            return processor.explain_instruction(instruction, 5)  # Max simplification
        
        return "I'm here to help. What part is difficult for you?"
    
    def _highlight_keywords(self, instruction: str) -> str:
        """Highlight important keywords in the instruction"""
        # Simple implementation - in production, use NLP to identify keywords
        keywords = ["what", "how", "why", "when", "where", "explain", "describe", "find"]
        result = instruction
        for keyword in keywords:
            if keyword in result.lower():
                result = result.replace(keyword, f"**{keyword}**")
                result = result.replace(keyword.capitalize(), f"**{keyword.capitalize()}**")
        
        return f"Let's look at the important words:\n\n{result}\n\nWhat are the question words here?"