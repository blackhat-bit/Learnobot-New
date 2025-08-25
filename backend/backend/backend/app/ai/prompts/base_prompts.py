from typing import Dict, Any, List, Optional
from datetime import datetime


class BasePrompts:
    """Base prompts for educational AI interactions."""
    
    @staticmethod
    def get_tutor_system_prompt(
        subject: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        learning_objectives: Optional[List[str]] = None,
        student_profile: Optional[Dict[str, Any]] = None
    ) -> str:
        """Get system prompt for AI tutor role."""
        
        base_prompt = """You are an expert AI tutor designed to help students learn effectively and enjoyably. Your role is to:

🎯 **Core Responsibilities:**
- Provide clear, accurate, and engaging explanations
- Adapt your teaching style to the student's level and needs
- Encourage critical thinking through thoughtful questions
- Offer supportive and constructive feedback
- Break down complex concepts into manageable parts
- Use examples, analogies, and real-world applications

📚 **Teaching Approach:**
- Start with what the student already knows
- Build knowledge incrementally
- Check for understanding regularly
- Provide multiple examples and perspectives
- Encourage active participation and questions
- Celebrate progress and learning milestones

💡 **Response Guidelines:**
- Keep explanations clear and age-appropriate
- Use encouraging and positive language
- Ask follow-up questions to deepen understanding
- Provide hints rather than direct answers when possible
- Suggest next steps and additional resources
- Be patient and supportive of mistakes as learning opportunities"""

        # Add subject-specific guidance
        if subject:
            subject_guidance = {
                "mathematics": """

📊 **Mathematics Focus:**
- Show step-by-step problem-solving processes
- Explain the 'why' behind mathematical concepts
- Use visual representations when helpful
- Connect math to real-world applications
- Encourage different solution methods""",
                
                "science": """

🔬 **Science Focus:**
- Emphasize observation, hypothesis, and experimentation
- Use analogies from everyday life
- Encourage questioning and curiosity about how things work
- Connect scientific concepts to current events and technology
- Promote hands-on thinking and exploration""",
                
                "language_arts": """

📖 **Language Arts Focus:**
- Build vocabulary through context and usage
- Encourage creative expression and critical analysis
- Use examples from literature, media, and student interests
- Focus on communication skills and clarity
- Celebrate creativity while teaching structure""",
                
                "history": """

🏛️ **History Focus:**
- Make connections between past and present
- Encourage perspective-taking and empathy
- Use stories and narratives to bring events to life
- Discuss cause and effect relationships
- Explore multiple viewpoints on historical events""",
                
                "programming": """

💻 **Programming Focus:**
- Start with small, working examples
- Explain concepts before showing code
- Encourage experimentation and debugging
- Break down complex problems into smaller parts
- Emphasize best practices and clean code"""
            }
            
            base_prompt += subject_guidance.get(subject.lower(), "")
        
        # Add difficulty level adjustments
        if difficulty_level:
            level_adjustments = {
                "beginner": """

🌟 **Beginner Level Adjustments:**
- Use simple, everyday language
- Provide more detailed explanations
- Offer frequent encouragement and reassurance
- Break concepts into very small steps
- Use plenty of concrete examples""",
                
                "intermediate": """

⚡ **Intermediate Level Adjustments:**
- Introduce more technical vocabulary gradually
- Encourage independent thinking before providing hints
- Connect new concepts to previously learned material
- Provide moderate challenges to build confidence
- Use a mix of guided and independent practice""",
                
                "advanced": """

🚀 **Advanced Level Adjustments:**
- Use appropriate technical language
- Encourage deeper analysis and synthesis
- Present challenging problems and scenarios
- Facilitate independent research and exploration
- Focus on applications and real-world problem solving"""
            }
            
            base_prompt += level_adjustments.get(difficulty_level.lower(), "")
        
        # Add learning objectives if provided
        if learning_objectives:
            objectives_text = ", ".join(learning_objectives)
            base_prompt += f"""

🎯 **Session Learning Objectives:**
Focus on helping the student achieve: {objectives_text}"""
        
        # Add student profile considerations
        if student_profile:
            profile_additions = []
            
            if student_profile.get("learning_style"):
                style = student_profile["learning_style"]
                profile_additions.append(f"- Adapt to {style} learning style")
            
            if student_profile.get("interests"):
                interests = ", ".join(student_profile["interests"])
                profile_additions.append(f"- Connect concepts to student interests: {interests}")
            
            if student_profile.get("challenges"):
                challenges = ", ".join(student_profile["challenges"])
                profile_additions.append(f"- Be mindful of learning challenges: {challenges}")
            
            if profile_additions:
                base_prompt += "\n\n👤 **Student Profile Considerations:**\n" + "\n".join(profile_additions)
        
        base_prompt += """

Remember: Your goal is to inspire curiosity, build confidence, and create a positive learning experience that encourages lifelong learning."""
        
        return base_prompt
    
    @staticmethod
    def get_explanation_prompt(topic: str, level: str, context: str = "") -> str:
        """Get prompt for explaining a concept."""
        
        return f"""Explain the concept of "{topic}" to a {level} level student.

{f"Context: {context}" if context else ""}

Your explanation should:
1. Start with a simple, clear definition
2. Use appropriate language for the {level} level
3. Include relevant examples
4. Make connections to familiar concepts
5. Anticipate and address potential confusion

Make your explanation engaging and easy to understand."""
    
    @staticmethod
    def get_practice_generation_prompt(
        topic: str, 
        difficulty: str, 
        num_problems: int = 3,
        problem_type: str = "mixed"
    ) -> str:
        """Get prompt for generating practice problems."""
        
        return f"""Generate {num_problems} practice problems about "{topic}" at {difficulty} difficulty level.

Problem type: {problem_type}

For each problem:
1. Present a clear, well-structured question
2. Include any necessary context or setup
3. Make problems progressively challenging if multiple
4. Ensure problems test understanding, not just memorization
5. Include hints for getting started (without giving away answers)

Format each problem clearly with numbering."""
    
    @staticmethod
    def get_feedback_prompt(
        question: str, 
        student_answer: str, 
        correct_answer: str = None,
        feedback_style: str = "constructive"
    ) -> str:
        """Get prompt for providing feedback on student work."""
        
        return f"""Provide {feedback_style} feedback on a student's answer.

Question: {question}

Student's Answer: {student_answer}

{f"Correct Answer: {correct_answer}" if correct_answer else ""}

Your feedback should:
1. Acknowledge what the student did well
2. Identify specific areas for improvement
3. Explain why certain parts are correct or incorrect
4. Provide guidance for better understanding
5. Encourage continued learning
6. Suggest next steps if appropriate

Be supportive and educational in your feedback."""
    
    @staticmethod
    def get_hint_prompt(
        question: str, 
        student_attempt: str, 
        hint_level: str = "medium"
    ) -> str:
        """Get prompt for providing hints."""
        
        hint_instructions = {
            "low": "Provide a very subtle hint that just points the student in the right direction without revealing the answer.",
            "medium": "Provide a helpful hint that guides the student toward the solution without giving it away completely.",
            "high": "Provide a detailed hint that clearly shows the path to the solution while still requiring the student to complete the final steps."
        }
        
        instruction = hint_instructions.get(hint_level, hint_instructions["medium"])
        
        return f"""A student is working on this problem and needs help:

Question: {question}

Student's current attempt: {student_attempt}

{instruction}

Your hint should:
- Be encouraging and supportive
- Guide without giving away the complete answer
- Help the student understand the approach
- Build confidence to continue working"""
    
    @staticmethod
    def get_assessment_prompt(
        topic: str, 
        level: str, 
        assessment_type: str = "quiz",
        time_limit: int = None
    ) -> str:
        """Get prompt for creating assessments."""
        
        return f"""Create a {assessment_type} to assess understanding of "{topic}" for {level} level students.

{f"Time limit: {time_limit} minutes" if time_limit else ""}

Include:
1. A variety of question types (multiple choice, short answer, application)
2. Questions that test different levels of understanding
3. Clear instructions for students
4. Appropriate difficulty for the {level} level
5. A basic rubric or answer key

Ensure the assessment is fair, comprehensive, and educational."""
    
    @staticmethod
    def get_motivation_prompt(student_situation: str) -> str:
        """Get prompt for providing motivation and encouragement."""
        
        return f"""A student is experiencing the following situation: {student_situation}

Provide motivational and encouraging support that:
1. Acknowledges their feelings and challenges
2. Reminds them of their capabilities and past successes
3. Offers specific, actionable strategies for moving forward
4. Maintains a positive but realistic tone
5. Inspires confidence and persistence
6. Celebrates the learning process, not just outcomes

Be genuine, supportive, and empowering in your response."""
    
    @staticmethod
    def get_study_plan_prompt(
        subject: str, 
        goals: List[str], 
        time_available: str,
        current_level: str
    ) -> str:
        """Get prompt for creating study plans."""
        
        goals_text = ", ".join(goals)
        
        return f"""Create a personalized study plan for a {current_level} level student.

Subject: {subject}
Learning Goals: {goals_text}
Time Available: {time_available}

The study plan should include:
1. Clear, achievable milestones
2. Specific activities and resources for each goal
3. Realistic timeline based on available time
4. Mix of different learning activities
5. Regular check-points for progress assessment
6. Flexibility for adjustments

Make the plan practical, motivating, and achievable."""
