from typing import Dict, Any, List, Optional


class HebrewPrompts:
    """Hebrew-specific prompts for language learning."""
    
    @staticmethod
    def get_hebrew_tutor_system_prompt(
        skill_level: str = "beginner",
        focus_area: str = "general"
    ) -> str:
        """Get system prompt for Hebrew language tutoring."""
        
        base_prompt = """אתה מורה עברית מומחה ומנוסה שתפקידו לעזור לתלמידים ללמוד עברית בצורה יעילה ומהנה.

🎯 **תפקידים עיקריים:**
- לספק הסברים ברורים ומדויקים בעברית ובאנגלית
- להתאים את שיטת ההוראה לרמה ולצרכים של התלמיד
- לעודד חשיבה ביקורתית באמצעות שאלות מחשבה
- לתת משובים תומכים ובונים
- לפרק מושגים מורכבים לחלקים קטנים וניתנים להבנה
- להשתמש בדוגמאות, השוואות ויישומים מהחיים

📚 **גישה בהוראה:**
- התחל ממה שהתלמיד כבר יודע
- בנה ידע בהדרגה
- בדוק הבנה באופן קבוע
- ספק דוגמאות מרובות ונקודות מבט שונות
- עודד השתתפות פעילה ושאלות
- חגוג התקדמות ואבני דרך בלמידה

💡 **הנחיות למענה:**
- שמור על הסברים ברורים ומתאימים לגיל
- השתמש בשפה מעודדת וחיובית
- שאל שאלות המשך להעמקת ההבנה
- ספק רמזים במקום תשובות ישירות כאשר אפשר
- הצע צעדים הבאים ומשאבים נוספים
- היה סבלני ותומך בטעויות כהזדמנויות למידה"""
        
        # Add skill level specific guidance
        level_guidance = {
            "beginner": """

🌟 **התאמה לרמת מתחילים:**
- התמקד באלף-בית, ניקוד ובסיסי קריאה
- השתמש בשפה פשוטה ובמילים בסיסיות
- ספק הרבה עידוד והכרה בהישגים קטנים
- פרק מושגים לשלבים קטנים מאוד
- השתמש בהרבה דוגמאות קונקרטיות""",
            
            "intermediate": """

⚡ **התאמה לרמת ביניים:**
- הרחב אוצר מילים והכר דקדוק בסיסי
- עודד קריאה עצמאית של טקסטים פשוטים
- חבר מושגים חדשים לחומר שנלמד קודם
- ספק אתגרים מתונים לבניית ביטחון
- שלב תרגול מודרך ועצמאי""",
            
            "advanced": """

🚀 **התאמה לרמה מתקדמת:**
- השתמש באוצר מילים מתקדם ובדקדוק מורכב
- עודד ניתוח והבנה עמוקה של טקסטים
- הצג בעיות ותרחישים מאתגרים
- קדם מחקר עצמאי וחקירה
- התמקד ביישומים מהחיים האמיתיים"""
        }
        
        base_prompt += level_guidance.get(skill_level, "")
        
        # Add focus area specific guidance
        focus_guidance = {
            "reading": """

📖 **התמקדות בקריאה:**
- התחל עם טקסטים קצרים ופשוטים
- הדגש זיהוי מילים ומשמעות
- שלב קריאה בקול ושקטה
- עזור בהבנת הקשר ורמזים טקסטואליים""",
            
            "writing": """

✍️ **התמקדות בכתיבה:**
- התחל עם מילים ומשפטים פשוטים
- הדגש איות נכון וכתיב ברור
- עודד ביטוי יצירתי ואישי
- ספק משוב על תוכן ואופן""",
            
            "speaking": """

🗣️ **התמקדות בדיבור:**
- התרגל הגייה ואינטונציה
- עודד שיחה ובעיות תקשורת
- בנה ביטחון בביטוי בעל פה
- השתמש במשחקי תפקידים ותרחישים""",
            
            "grammar": """

📝 **התמקדות בדקדוק:**
- הסבר כללי דקדוק בצורה ברורה
- השתמש בדוגמאות רבות מהחיים
- קשר דקדוק לשימוש מעשי
- תרגל דרך כתיבה ודיבור"""
        }
        
        base_prompt += focus_guidance.get(focus_area, "")
        
        base_prompt += """

זכור: המטרה שלך היא לעורר סקרנות, לבנות ביטחון וליצור חוויית למידה חיובית שמעודדת למידה לכל החיים."""
        
        return base_prompt
    
    @staticmethod
    def get_hebrew_vocabulary_prompt(
        words: List[str], 
        context: str = "",
        include_grammar: bool = True
    ) -> str:
        """Get prompt for Hebrew vocabulary instruction."""
        
        words_text = ", ".join(words)
        
        prompt = f"""לימד את המילים הבאות לתלמיד עברית: {words_text}

{f"הקשר: {context}" if context else ""}

עבור כל מילה, ספק:
1. המילה בעברית עם ניקוד מלא
2. תרגום לאנגלית
3. הגייה באותיות לטיניות
4. דוגמה למשפט בעברית
5. תרגום המשפט לאנגלית"""
        
        if include_grammar:
            prompt += """
6. מידע דקדוקי (שם עצם/פועל/תואר וכו')
7. צורות נוספות אם רלוונטי (רבים, נטיות וכו')"""
        
        prompt += """

השתמש בשפה ברורה ונגישה, והקפד על דיוק בניקוד ובתרגום."""
        
        return prompt
    
    @staticmethod
    def get_hebrew_reading_comprehension_prompt(
        text: str, 
        level: str,
        question_types: List[str] = None
    ) -> str:
        """Get prompt for Hebrew reading comprehension exercises."""
        
        if not question_types:
            question_types = ["understanding", "details", "inference", "vocabulary"]
        
        return f"""צור תרגיל הבנת הנקרא בעברית לרמת {level}.

הטקסט:
{text}

צור שאלות מהסוגים הבאים: {", ".join(question_types)}

עבור כל שאלה:
1. נסח את השאלה בעברית ברורה
2. ספק אפשרויות תשובה אם מתאים
3. כתב את התשובה הנכונה
4. הסבר למה התשובה נכונה

ודא שהשאלות מתאימות לרמת {level} ובודקות הבנה אמיתית של הטקסט."""
    
    @staticmethod
    def get_hebrew_grammar_prompt(
        grammar_topic: str, 
        level: str,
        include_exercises: bool = True
    ) -> str:
        """Get prompt for Hebrew grammar instruction."""
        
        prompt = f"""הסבר את הנושא הדקדוקי "{grammar_topic}" לתלמיד ברמת {level}.

ההסבר צריך לכלול:
1. הגדרה ברורה של הנושא
2. כללים עיקריים בצורה פשוטה
3. דוגמאות מגוונות ומובנות
4. התייחסות לחריגים נפוצים אם קיימים
5. טיפים לזכירה ולשימוש נכון"""
        
        if include_exercises:
            prompt += """
6. 3-5 תרגילים להתרגלות
7. פתרונות מפורטים לתרגילים"""
        
        prompt += """

השתמש בשפה נגישה ובדוגמאות מהחיים היומיומיים."""
        
        return prompt
    
    @staticmethod
    def get_hebrew_conversation_prompt(
        scenario: str, 
        level: str,
        vocabulary_focus: List[str] = None
    ) -> str:
        """Get prompt for Hebrew conversation practice."""
        
        vocab_text = f"התמקד במילים: {', '.join(vocabulary_focus)}" if vocabulary_focus else ""
        
        return f"""צור תרגיל שיחה בעברית לרמת {level} על הנושא: {scenario}

{vocab_text}

הכן:
1. דיאלוג לדוגמה של 6-8 משפטים
2. ביטויים שימושיים לסיטואציה
3. שאלות לתרגול השיחה
4. הצעות לווריאציות על הנושא
5. טיפים לביטוי טבעי

ודא שהתוכן מתאים לרמת {level} ושימושי למצבים אמיתיים."""
    
    @staticmethod
    def get_hebrew_writing_prompt(
        writing_task: str, 
        level: str,
        word_limit: int = None
    ) -> str:
        """Get prompt for Hebrew writing instruction."""
        
        limit_text = f"מגבלת מילים: {word_limit}" if word_limit else ""
        
        return f"""הדרך תלמיד לכתיבה בעברית ברמת {level}.

משימת הכתיבה: {writing_task}
{limit_text}

ספק:
1. הוראות ברורות למשימה
2. מבנה מוצע לכתיבה
3. רשימת מילים ומושגים שימושיים
4. דוגמאות למשפטי פתיחה וסיום
5. טיפים לכתיבה טובה בעברית
6. רובריקה להערכה עצמית

עודד יצירתיות תוך שמירה על דיוק לשוני."""
    
    @staticmethod
    def get_hebrew_cultural_context_prompt(
        cultural_topic: str,
        connection_to_language: str = ""
    ) -> str:
        """Get prompt for explaining Hebrew cultural context."""
        
        return f"""הסבר את ההיבט התרבותי של "{cultural_topic}" בהקשר ללימוד עברית.

{f"הקשר לשפה: {connection_to_language}" if connection_to_language else ""}

כלול:
1. רקע היסטורי קצר
2. משמעות תרבותית
3. איך זה משפיע על השפה העברית
4. דוגמאות לשימוש בחיים המודרניים
5. הבדלים תרבותיים שחשוב להכיר
6. הצעות לחקירה נוספת

עשה את ההסבר מעניין ורלוונטי ללומדי עברית."""
