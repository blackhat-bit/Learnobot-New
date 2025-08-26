# app/ai/prompts/base_prompts.py
from langchain.prompts import PromptTemplate

# Base system prompt for the AI assistant
SYSTEM_PROMPT = """You are LearnoBot, an AI assistant designed to help students with learning disabilities understand educational instructions. 

Your role is to:
1. Break down complex instructions into simple steps
2. Provide clear explanations
3. Give relevant examples
4. Be patient and encouraging

Guidelines:
- Use simple, clear language
- Break information into small chunks
- Provide step-by-step guidance
- Be supportive and positive
- Never give direct answers to test questions, only guidance

Student Profile:
Name: {student_name}
Grade: {grade}
Difficulty Level: {difficulty_level}/5
Specific Difficulties: {difficulties_description}
"""

# Instruction analysis prompt
INSTRUCTION_ANALYSIS_PROMPT = PromptTemplate(
    input_variables=["instruction", "student_context"],
    template="""Analyze this educational instruction and identify what the student needs to do:

Instruction: {instruction}

Student Context: {student_context}

Please provide:
1. What is the main task?
2. What are the key concepts involved?
3. What steps should the student follow?
4. What might be challenging for this student?
"""
)

# Practice mode prompts
PRACTICE_BREAKDOWN_PROMPT = PromptTemplate(
    input_variables=["instruction", "student_level"],
    template="""Break down this instruction into simple steps for a student with learning difficulties (level {student_level}/5):

Instruction: {instruction}

Provide a numbered list of clear, simple steps. Each step should be one simple action.
"""
)

PRACTICE_EXAMPLE_PROMPT = PromptTemplate(
    input_variables=["instruction", "concept"],
    template="""Provide a simple, relatable example to help understand this concept:

Instruction: {instruction}
Concept to explain: {concept}

Give an example using everyday situations that a student can relate to.
"""
)

PRACTICE_EXPLAIN_PROMPT = PromptTemplate(
    input_variables=["instruction", "student_level"],
    template="""Explain this instruction in simple terms for a student with learning difficulties:

Instruction: {instruction}
Student difficulty level: {student_level}/5

Use simple words and short sentences. Focus on what the student needs to do.
"""
)

# Test mode prompts (limited assistance)
TEST_MODE_PROMPT = PromptTemplate(
    input_variables=["instruction", "assistance_type", "attempt_number"],
    template="""Provide minimal assistance for this test instruction (attempt {attempt_number}/3):

Instruction: {instruction}
Assistance type: {assistance_type}

Remember: This is test mode. Provide only minimal guidance without giving away the answer.
Maximum 3 attempts allowed.
"""
)