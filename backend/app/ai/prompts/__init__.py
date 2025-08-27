"""
Prompt templates and management for AI interactions.
"""

# Import key prompt templates and functions that actually exist
from .base_prompts import (
    SYSTEM_PROMPT,
    INSTRUCTION_ANALYSIS_PROMPT,
    PRACTICE_BREAKDOWN_PROMPT,
    PRACTICE_EXAMPLE_PROMPT,
    PRACTICE_EXPLAIN_PROMPT,
    TEST_MODE_PROMPT
)
from .hebrew_prompts import (
    HEBREW_SYSTEM_PROMPT,
    HEBREW_PRACTICE_PROMPT,
    HEBREW_TEST_PROMPT,
    HEBREW_BREAKDOWN_PROMPT,
    HEBREW_EXAMPLE_PROMPT,
    HEBREW_EXPLAIN_PROMPT,
    get_encouragement,
    identify_question_type
)

__all__ = [
    "SYSTEM_PROMPT",
    "INSTRUCTION_ANALYSIS_PROMPT", 
    "PRACTICE_BREAKDOWN_PROMPT",
    "PRACTICE_EXAMPLE_PROMPT",
    "PRACTICE_EXPLAIN_PROMPT",
    "TEST_MODE_PROMPT",
    "HEBREW_SYSTEM_PROMPT",
    "HEBREW_PRACTICE_PROMPT",
    "HEBREW_TEST_PROMPT", 
    "HEBREW_BREAKDOWN_PROMPT",
    "HEBREW_EXAMPLE_PROMPT",
    "HEBREW_EXPLAIN_PROMPT",
    "get_encouragement",
    "identify_question_type"
]
