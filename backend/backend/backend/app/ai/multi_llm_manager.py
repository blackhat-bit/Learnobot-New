from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime

from app.ai.llm_manager import LLMManager
from app.models.llm_config import LLMConfig


class MultiLLMManager:
    """Manager for coordinating multiple LLM configurations and strategies."""
    
    def __init__(self):
        self.llm_manager = LLMManager()
        self.usage_stats = {}
    
    async def generate_response_with_fallback(
        self, 
        messages: List[Dict[str, str]], 
        primary_config: LLMConfig,
        fallback_configs: List[LLMConfig],
        chat_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate response with fallback to other configurations if primary fails."""
        
        configs_to_try = [primary_config] + fallback_configs
        
        for i, config in enumerate(configs_to_try):
            try:
                response = await self.llm_manager.generate_response(
                    messages, config, chat_context
                )
                
                # Track successful usage
                self._track_usage(config.id, success=True)
                
                # Add metadata about which config was used
                response["config_used"] = {
                    "id": config.id,
                    "name": config.name,
                    "is_fallback": i > 0,
                    "attempt_number": i + 1
                }
                
                return response
            
            except Exception as e:
                # Track failed usage
                self._track_usage(config.id, success=False, error=str(e))
                
                # If this was the last config, raise the error
                if i == len(configs_to_try) - 1:
                    return {
                        "content": "I apologize, but all AI systems are currently unavailable. Please try again later.",
                        "model_used": "error_fallback",
                        "tokens_used": 0,
                        "error": "All LLM configurations failed",
                        "failed_configs": [c.name for c in configs_to_try]
                    }
        
        # This should never be reached, but just in case
        return {
            "content": "Unexpected error occurred.",
            "model_used": "error_fallback",
            "tokens_used": 0
        }
    
    async def generate_parallel_responses(
        self, 
        messages: List[Dict[str, str]], 
        configs: List[LLMConfig],
        chat_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Generate responses from multiple LLMs in parallel for comparison."""
        
        async def generate_single_response(config: LLMConfig) -> Dict[str, Any]:
            try:
                response = await self.llm_manager.generate_response(
                    messages, config, chat_context
                )
                response["config_id"] = config.id
                response["config_name"] = config.name
                return response
            except Exception as e:
                return {
                    "content": f"Error with {config.name}: {str(e)}",
                    "model_used": config.model_name,
                    "tokens_used": 0,
                    "config_id": config.id,
                    "config_name": config.name,
                    "error": str(e)
                }
        
        # Run all configurations in parallel
        tasks = [generate_single_response(config) for config in configs]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and format results
        valid_responses = []
        for response in responses:
            if not isinstance(response, Exception):
                valid_responses.append(response)
        
        return valid_responses
    
    async def select_best_response(
        self, 
        responses: List[Dict[str, Any]],
        selection_criteria: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Select the best response from multiple LLM outputs."""
        
        if not responses:
            return {
                "content": "No valid responses generated.",
                "model_used": "selection_fallback",
                "tokens_used": 0
            }
        
        # Default selection criteria
        criteria = selection_criteria or {
            "prefer_higher_confidence": True,
            "prefer_longer_responses": False,
            "prefer_specific_models": [],
            "avoid_error_responses": True
        }
        
        # Filter out error responses if requested
        if criteria.get("avoid_error_responses", True):
            valid_responses = [r for r in responses if "error" not in r]
            if valid_responses:
                responses = valid_responses
        
        # Score each response
        scored_responses = []
        for response in responses:
            score = self._calculate_response_score(response, criteria)
            scored_responses.append((score, response))
        
        # Sort by score (highest first)
        scored_responses.sort(key=lambda x: x[0], reverse=True)
        
        best_response = scored_responses[0][1]
        
        # Add selection metadata
        best_response["selection_info"] = {
            "total_responses": len(responses),
            "selection_score": scored_responses[0][0],
            "selection_criteria": criteria,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return best_response
    
    def _calculate_response_score(self, response: Dict[str, Any], criteria: Dict[str, Any]) -> float:
        """Calculate a score for response selection."""
        
        score = 0.0
        
        # Base score
        if "error" not in response:
            score += 10.0
        
        # Confidence score
        if criteria.get("prefer_higher_confidence", True):
            confidence = response.get("confidence_score", "medium")
            confidence_scores = {"high": 5.0, "medium": 2.5, "low": 1.0}
            score += confidence_scores.get(confidence, 0.0)
        
        # Response length
        content_length = len(response.get("content", ""))
        if criteria.get("prefer_longer_responses", False):
            score += min(content_length / 100, 5.0)  # Max 5 points for length
        else:
            # Prefer moderate length (not too short, not too long)
            if 50 <= content_length <= 500:
                score += 3.0
            elif content_length > 500:
                score += 1.0
        
        # Model preference
        preferred_models = criteria.get("prefer_specific_models", [])
        if preferred_models and response.get("model_used") in preferred_models:
            score += 8.0
        
        # Token efficiency (prefer responses that use tokens efficiently)
        tokens_used = response.get("tokens_used", 0)
        if tokens_used > 0 and content_length > 0:
            efficiency = content_length / tokens_used
            score += min(efficiency * 2, 3.0)  # Max 3 points for efficiency
        
        return score
    
    async def generate_consensus_response(
        self, 
        messages: List[Dict[str, str]], 
        configs: List[LLMConfig],
        chat_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a consensus response by combining outputs from multiple LLMs."""
        
        # Generate parallel responses
        responses = await self.generate_parallel_responses(messages, configs, chat_context)
        
        if not responses:
            return {
                "content": "Unable to generate consensus response.",
                "model_used": "consensus_fallback",
                "tokens_used": 0
            }
        
        # Extract valid responses
        valid_responses = [r for r in responses if "error" not in r and r.get("content")]
        
        if not valid_responses:
            return responses[0]  # Return first response even if it has an error
        
        # Simple consensus strategy: combine key information
        consensus_content = self._create_consensus_content(valid_responses)
        
        # Calculate combined metrics
        total_tokens = sum(r.get("tokens_used", 0) for r in valid_responses)
        models_used = [r.get("model_used", "unknown") for r in valid_responses]
        
        return {
            "content": consensus_content,
            "model_used": f"consensus({', '.join(set(models_used))})",
            "tokens_used": total_tokens,
            "confidence_score": "high",  # Consensus implies higher confidence
            "consensus_info": {
                "responses_combined": len(valid_responses),
                "models_used": models_used,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def _create_consensus_content(self, responses: List[Dict[str, Any]]) -> str:
        """Create consensus content from multiple responses."""
        
        contents = [r["content"] for r in responses if r.get("content")]
        
        if len(contents) == 1:
            return contents[0]
        
        # Simple consensus: if responses are similar, use the first one
        # If different, combine key points
        
        # For now, use the longest response as it's likely most comprehensive
        longest_response = max(contents, key=len)
        
        # Add a note about consensus
        consensus_note = f"\n\n*Note: This response represents a consensus from {len(contents)} AI models.*"
        
        return longest_response + consensus_note
    
    def _track_usage(self, config_id: int, success: bool, error: str = None):
        """Track usage statistics for LLM configurations."""
        
        if config_id not in self.usage_stats:
            self.usage_stats[config_id] = {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "recent_errors": []
            }
        
        stats = self.usage_stats[config_id]
        stats["total_requests"] += 1
        
        if success:
            stats["successful_requests"] += 1
        else:
            stats["failed_requests"] += 1
            if error:
                stats["recent_errors"].append({
                    "error": error,
                    "timestamp": datetime.utcnow().isoformat()
                })
                # Keep only recent errors (last 10)
                stats["recent_errors"] = stats["recent_errors"][-10:]
    
    def get_usage_statistics(self) -> Dict[int, Dict[str, Any]]:
        """Get usage statistics for all tracked configurations."""
        return self.usage_stats.copy()
    
    def get_config_health_score(self, config_id: int) -> float:
        """Calculate health score for a configuration based on recent performance."""
        
        if config_id not in self.usage_stats:
            return 1.0  # No data means neutral score
        
        stats = self.usage_stats[config_id]
        total = stats["total_requests"]
        
        if total == 0:
            return 1.0
        
        success_rate = stats["successful_requests"] / total
        
        # Adjust score based on recent errors
        recent_error_count = len(stats["recent_errors"])
        error_penalty = min(recent_error_count * 0.1, 0.5)  # Max 50% penalty
        
        health_score = max(success_rate - error_penalty, 0.0)
        
        return health_score
