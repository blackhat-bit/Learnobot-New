# Chat Flow Analysis - Complete System Architecture

**Project**: LearnoBot Educational AI Assistant
**Date**: 2025-10-25
**Focus**: How chat messages flow through the system for different AI providers

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Complete Chat Flow](#complete-chat-flow)
4. [Google AI Flow (Cloud Provider)](#google-ai-flow-cloud-provider)
5. [Other Cloud AI Flow](#other-cloud-ai-flow-openai-anthropic-cohere)
6. [Local AI Flow (Ollama)](#local-ai-flow-ollama)
7. [Key Differences Between Providers](#key-differences-between-providers)
8. [Fixes Implemented](#fixes-implemented)
9. [Code Walkthrough](#code-walkthrough)
10. [Testing Examples](#testing-examples)

---

## Overview

LearnoBot supports 3 types of AI providers:
1. **Google AI** (Gemini) - Cloud, requires special system instruction handling
2. **Other Cloud AIs** - OpenAI GPT, Anthropic Claude, Cohere Command
3. **Local AIs** - Ollama (Llama, Aya, etc.) running in Docker

Each provider type has different characteristics and requires different prompt formatting.

---

## Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────┐
│                        Flutter Mobile App                          │
│  Student sends message: "תסביר לי מה זה חיבור"                    │
└──────────────────────────┬─────────────────────────────────────────┘
                           │
                           ▼ POST /api/v1/chat/sessions/{id}/messages
┌────────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (chat.py)                        │
│  Endpoint: send_message()                                          │
│  • Validates user session                                           │
│  • Calls chat_service.process_message()                            │
└──────────────────────────┬─────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────────────┐
│               ChatService (chat_service.py)                         │
│  • Saves user message to database                                  │
│  • Fetches conversation history (last 10 messages)                 │
│  • Formats history: "תלמיד: ..." / "לרנובוט: ..."                │
│  • Prepares student context (name, grade, difficulty)              │
│  • Determines which processing path to use                         │
└──────────────────────────┬─────────────────────────────────────────┘
                           │
              ┌────────────┴─────────────┐
              ▼                          ▼
┌──────────────────────┐    ┌──────────────────────────┐
│  Hebrew Mediation    │    │  Instruction Processor   │
│  (Local Ollama Only) │    │  (Cloud Models)          │
│                      │    │                          │
│  hebrew_mediation_   │    │  instruction_chain.py    │
│  chain.py            │    │                          │
└──────┬───────────────┘    └───────┬──────────────────┘
       │                            │
       │                            │
       └──────────┬─────────────────┘
                  │
                  ▼
┌────────────────────────────────────────────────────────────────────┐
│            MultiProviderLLMManager (multi_llm_manager.py)          │
│  Method: generate(prompt, provider)                                │
│  • Routes to appropriate provider instance                         │
│  • Google: Prepends system instruction                             │
│  • OpenAI/Anthropic: Direct API call                              │
│  • Ollama: HTTP request to Docker container                       │
└──────────────────────────┬─────────────────────────────────────────┘
                           │
              ┌────────────┴─────────────┐
              ▼                          ▼
┌────────────────────────┐    ┌───────────────────────┐
│  Google Gemini         │    │  OpenAI GPT-4         │
│  (Cloud API)           │    │  (Cloud API)          │
│                        │    │                       │
│  • System instruction  │    │  • Standard prompt    │
│    prepended to prompt │    │  • No special handling│
└────────┬───────────────┘    └──────┬────────────────┘
         │                           │
         └──────────┬────────────────┘
                    │
                    ▼
         ┌───────────────────────┐
         │  Ollama (Local)       │
         │  Docker Container     │
         │  localhost:11434      │
         │                       │
         │  • Full Hebrew prompts│
         │  • Mediation chain    │
         └───────┬───────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────────────┐
│                    AI Response Generated                           │
│  "חיבור הוא פעולה מתמטית שבה אנו מצרפים שני מספרים יחד..."        │
└──────────────────────────┬─────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────────────┐
│                ChatService saves response to database               │
│  • Creates ChatMessage (role: ASSISTANT)                           │
│  • Logs analytics event                                            │
│  • Returns to API endpoint                                         │
└──────────────────────────┬─────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────────────┐
│                    Flutter App Displays Response                    │
│  Chat bubble with AI's answer                                      │
└────────────────────────────────────────────────────────────────────┘
```

---

## Complete Chat Flow

### Step-by-Step Process

#### 1. Student Sends Message (Flutter App)

**File**: `lib/screens/student/student_chat_screen.dart`

```dart
void _sendMessage() {
  final message = _textController.text.trim();
  if (message.isEmpty) return;

  // Send to backend
  chatService.sendMessage(
    sessionId: widget.sessionId,
    content: message,
    assistanceType: _selectedAssistanceType,
    provider: _selectedProvider  // e.g., "google-gemini_2_5_flash"
  );
}
```

---

#### 2. API Endpoint Receives Request

**File**: `backend/app/api/chat.py` (lines 65-80)

```python
@router.post("/sessions/{session_id}/messages", response_model=chat_schemas.ChatMessage)
async def send_message(
    session_id: int,
    message: chat_schemas.ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message in a chat session and get AI response"""
    return await chat_service.process_message(
        db=db,
        session_id=session_id,
        user_id=current_user.id,
        message=message.content,
        assistance_type=message.assistance_type,
        provider=message.provider
    )
```

**Request Body**:
```json
{
  "content": "תסביר לי מה זה חיבור",
  "assistance_type": "explain",
  "provider": "google-gemini_2_5_flash"
}
```

---

#### 3. Chat Service Processes Message

**File**: `backend/app/services/chat_service.py` (lines 98-136)

```python
async def process_message(self, db: Session, session_id: int, user_id: int,
                          message: str, assistance_type: str = None,
                          provider: str = None):
    # Save user message to database
    user_message = ChatMessage(
        session_id=session_id,
        user_id=user_id,
        role=MessageRole.USER,
        content=message
    )
    db.add(user_message)
    db.commit()

    # Get session details
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    student = session.student

    # Get recent conversation history (last 10 messages)
    recent_messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.timestamp.desc()).limit(10).all()

    recent_messages.reverse()  # Chronological order

    # Format conversation history
    conversation_history = []
    for msg in recent_messages[:-1]:  # Exclude current message
        role = "תלמיד" if msg.role == MessageRole.USER else "לרנובוט"
        conversation_history.append(f"{role}: {msg.content}")

    # Prepare student context
    student_context = {
        "name": student.full_name,
        "grade": student.grade,
        "difficulty_level": student.difficulty_level,
        "difficulties": student.difficulties_description,
        "language_preference": student.user.language_preference,
        "conversation_history": "\n".join(conversation_history)
    }

    # Now route to appropriate processor...
```

**Conversation History Format** (Example):
```
תלמיד: שלום
לרנובוט: היי, אני לרנובוט... איך אני יכול לעזור לך?
תלמיד: תסביר לי מה זה חיבור
```

---

#### 4. Routing Decision: Which Processor?

**File**: `backend/app/services/chat_service.py` (lines 143-190)

```python
# Check if Hebrew mediation should be used (only for local models)
if hebrew_mediation_service.should_use_mediation(session, assistance_type, provider):
    # ═══════════════════════════════════════════════════════
    # PATH A: Hebrew Mediation (Local Ollama Models Only)
    # ═══════════════════════════════════════════════════════
    mediation_result = hebrew_mediation_service.process_mediated_response(
        db=db,
        session_id=session_id,
        instruction=message,
        student_response=message,
        provider=provider,
        assistance_type=assistance_type
    )
    ai_response = mediation_result["response"]

elif session.mode == InteractionMode.PRACTICE:
    # ═══════════════════════════════════════════════════════
    # PATH B: Instruction Processor (Cloud Models)
    # ═══════════════════════════════════════════════════════
    if assistance_type == "breakdown":
        ai_response = instruction_processor.breakdown_instruction(
            message, student.difficulty_level, language_pref, provider, student_context
        )
    elif assistance_type == "example":
        ai_response = instruction_processor.provide_example(
            message, "main concept", language_pref, provider, student_context
        )
    elif assistance_type == "explain":
        ai_response = instruction_processor.explain_instruction(
            message, student.difficulty_level, language_pref, provider, student_context
        )
    else:
        # Fallback to analysis (natural conversation)
        analysis = instruction_processor.analyze_instruction(message, student_context, provider)
        ai_response = analysis["analysis"]
```

**Decision Logic**:
- **Local Ollama Models** → Hebrew Mediation Chain (sophisticated emotional support)
- **Cloud Models** (Google, OpenAI, etc.) → Instruction Processor (efficient short prompts)

**File**: `backend/app/services/hebrew_mediation_service.py` (lines 155-159)

```python
def should_use_mediation(self, session: ChatSession, assistance_type: str = None, provider: str = None) -> bool:
    # Use mediation for local models (Ollama/Aya) in Agent Selection mode
    if provider and provider.startswith("ollama-"):
        return True  # Always use mediation for Ollama
    return False  # Cloud models use instruction processor
```

---

## Google AI Flow (Cloud Provider)

### Path B: Instruction Processor → Google Provider

#### Step 5: Instruction Chain Builds Prompt

**File**: `backend/app/ai/chains/instruction_chain.py` (lines 94-190)

```python
def analyze_instruction(self, instruction: str, student_context: dict, provider: str = None) -> dict:
    # For cloud models, use efficient prompt with system guidance
    if provider and not provider.startswith("ollama-"):
        # Load custom prompt from manager if available
        custom_system_prompt = self._get_custom_system_prompt("practice")

        # Get conversation history
        conversation_history = student_context.get("conversation_history", "")

        # Count messages in conversation (for flow detection)
        message_count = len([line for line in conversation_history.split('\n')
                             if line.strip().startswith('תלמיד:')]) if conversation_history else 0

        # Check if student recently received assistance
        just_received_help = any(keyword in conversation_history.lower() for keyword in [
            'בוא נפרק', 'שלב ראשון', 'לדוגמה', 'זה כמו'
        ]) if conversation_history else False

        # Check if first message
        is_first_message = not conversation_history or conversation_history.strip() == ""

        if is_first_message:
            # ═══════════════════════════════════════════════════════
            # FIRST MESSAGE: Greeting + Assistance Type Options
            # ═══════════════════════════════════════════════════════
            default_prompt = f"""אתה לרנובוט, עוזר AI שעוזר לתלמידים.

התלמיד שאל: "{instruction}"

אני יכול לעזור בשלוש דרכים:
**הסבר** - הסבר מה זה אומר
**פירוק לשלבים** - לחלק למשימות קטנות
**דוגמה** - לתת דוגמה מהחיים

איך תרצה שאעזור לך?"""

        elif message_count == 1:
            # ═══════════════════════════════════════════════════════
            # SECOND MESSAGE: Task Reading Verification
            # ═══════════════════════════════════════════════════════
            default_prompt = f"""לפני שנתחיל, שאל בעדינות: "קראת כבר את המשימה שקיבלת?"

אם התלמיד אומר כן - המשך לעזור
אם התלמיד אומר לא - עודד אותו לקרוא קודם"""

        elif just_received_help:
            # ═══════════════════════════════════════════════════════
            # AFTER ASSISTANCE: Clarity Follow-Up
            # ═══════════════════════════════════════════════════════
            default_prompt = f"""אתה זה עתה נתת הסבר/פירוק/דוגמה לתלמיד.

עכשיו שאל: "האם עכשיו זה יותר ברור לך?"

אם התלמיד אומר לא - הצע לנסות דרך אחרת"""

        else:
            # ═══════════════════════════════════════════════════════
            # CONTINUING CONVERSATION: Natural Response
            # ═══════════════════════════════════════════════════════
            default_prompt = f"""אתה לרנובוט, עוזר AI חינוכי. המשך את השיחה באופן טבעי.

שיחה קודמת (רק להקשר - אל תחזור על זה!):
{conversation_history}

הודעה אחרונה: "{instruction}"

הנחיות לתשובה שלך:
1. אם התלמיד נתן תשובה (מספר, פתרון):
   - אמת אם זה נכון או לא
   - אם נכון: עודד ושאל אם רוצה עזרה נוספת
   - אם לא נכון: הנחה בעדינות (בלי לתת תשובה!)

2. אם התלמיד שואל שאלה חדשה:
   - הצע: **הסבר** **פירוק לשלבים** **דוגמה**

3. תמיד היה מעודד ותומך

חשוב מאוד:
- ענה ישירות לתלמיד, אל תכתוב "תלמיד:" או "לרנובוט:"
- אל תחזור על השיחה הקודמת
- אל תפתור במקום התלמיד, רק הנחה!"""

        # Prepend custom system prompt if exists
        if custom_system_prompt:
            prompt_text = f"{custom_system_prompt}\n\n{default_prompt}"
        else:
            prompt_text = default_prompt

    # Use multi_llm_manager to generate response
    result = multi_llm_manager.generate(prompt_text, provider=provider)

    return {"analysis": result}
```

**Key Features**:
1. **Message Count Detection** → Different prompts based on conversation stage
2. **Conversation History Included** → AI knows what was said before
3. **Flow Prompts** → Task reading check, clarity follow-up
4. **No History Echo** → Explicit instruction not to repeat "תלמיד:"

---

#### Step 6: Multi-LLM Manager Routes to Google

**File**: `backend/app/ai/multi_llm_manager.py` (lines 889-929)

```python
def generate(self, prompt: str, provider: str = None, **kwargs) -> str:
    if provider is None:
        provider = self.active_provider

    if provider not in self.providers:
        raise ValueError(f"Provider {provider} not available")

    provider_instance = self.providers[provider]

    try:
        # Route to appropriate provider
        response = provider_instance.generate(prompt, **kwargs)
        return response
    except Exception as e:
        logger.error(f"Error generating from {provider}: {e}")
        raise
```

---

#### Step 7: Google Provider Adds System Instruction

**File**: `backend/app/ai/multi_llm_manager.py` (lines 564-590)

```python
class GoogleProvider(BaseLLMProvider):
    def initialize(self, config: Dict[str, Any]):
        # ... (SDK initialization)

        # System instruction to prepend to every prompt
        self.system_instruction = """You are LearnoBot, an educational AI assistant helping students with learning disabilities understand Hebrew instructional tasks.

Your role:
- Guide students to learn independently (never give direct answers)
- Use simple, clear Hebrew language
- Be patient, encouraging, and supportive

Critical rules:
- NEVER solve problems for the student
- NEVER provide final answers or numerical results
- ONLY explain methods and processes
- Students MUST work it out themselves

---"""

    def generate(self, prompt: str, **kwargs) -> str:
        import time
        logger = logging.getLogger(__name__)
        start_time = time.time()

        try:
            # ═══════════════════════════════════════════════════════
            # PREPEND SYSTEM INSTRUCTION TO PROMPT
            # ═══════════════════════════════════════════════════════
            full_prompt = f"{self.system_instruction}\n\n{prompt}"

            # Log the prompt being sent (without system instruction for brevity)
            logger.info(f"📤 GOOGLE PROMPT (length={len(prompt)}):\n{prompt}\n{'='*80}")

            response = self.client.generate_content(
                full_prompt,
                generation_config=generation_config
            )

            response_text = response.text

            # Log the response received
            logger.info(f"📥 GOOGLE RESPONSE (length={len(response_text)}):\n{response_text}\n{'='*80}")

            return response_text

        except Exception as e:
            logger.error(f"Google AI generation error: {e}")
            raise
```

**Why Prepend System Instruction?**
- `google-generativeai==0.3.2` doesn't support `system_instruction` parameter in constructor
- Workaround: Prepend to every prompt
- Ensures Google behaves like GPT (educational guidance, no direct answers)

---

#### Step 8: Google Gemini Generates Response

**Example Prompt Sent to Google**:
```
You are LearnoBot, an educational AI assistant helping students with learning disabilities understand Hebrew instructional tasks.

Your role:
- Guide students to learn independently (never give direct answers)
- Use simple, clear Hebrew language
- Be patient, encouraging, and supportive

Critical rules:
- NEVER solve problems for the student
- NEVER provide final answers or numerical results
- ONLY explain methods and processes
- Students MUST work it out themselves

---

אתה לרנובוט, עוזר AI חינוכי. המשך את השיחה באופן טבעי.

שיחה קודמת (רק להקשר - אל תחזור על זה!):
תלמיד: שלום
לרנובוט: היי, אני לרנובוט... איך אני יכול לעזור לך?

הודעה אחרונה: "תסביר לי מה זה חיבור"

הנחיות לתשובה שלך:
...
```

**Google Response**:
```
חיבור הוא פעולה מתמטית שבה אנו מצרפים שני מספרים או יותר כדי לקבל סכום כולל.

למשל, אם יש לך 3 תפוחים ומוסיפים עוד 2 תפוחים, החיבור עוזר לך לדעת כמה תפוחים יש לך בסך הכל.

הדרך לעשות חיבור:
1. קח את המספר הראשון
2. הוסף אליו את המספר השני
3. התוצאה היא הסכום

איך אתה רוצה שנתרגל את זה? אני יכול לתת דוגמאות נוספות או לפרק את זה לשלבים קטנים יותר.
```

**Notice**:
- ✅ No emoji (removed per specification)
- ✅ No direct answer (doesn't say "3+2=5")
- ✅ Explains method/concept only
- ✅ Asks follow-up question
- ✅ No "תלמיד:" prefix echoed

---

## Other Cloud AI Flow (OpenAI, Anthropic, Cohere)

### Similar to Google, But Simpler

**Same Flow**:
1. Instruction chain builds prompt
2. Multi-LLM manager routes to provider
3. Provider makes API call

**Differences from Google**:

#### OpenAI (GPT-4)

**File**: `backend/app/ai/multi_llm_manager.py` (lines 164-188)

```python
class OpenAIProvider(BaseLLMProvider):
    def generate(self, prompt: str, **kwargs) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key, timeout=120.0)

        # Log the prompt being sent
        logger.info(f"📤 OPENAI PROMPT (length={len(prompt)}):\n{prompt}\n{'='*80}")

        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        response_text = response.choices[0].message.content

        # Log the response received
        logger.info(f"📥 OPENAI RESPONSE (length={len(response_text)}):\n{response_text}\n{'='*80}")

        return response_text
```

**Key Difference**: No system instruction prepending (OpenAI naturally understands educational guidance)

---

#### Anthropic (Claude)

**File**: `backend/app/ai/multi_llm_manager.py` (lines 294-324)

```python
class AnthropicProvider(BaseLLMProvider):
    def generate(self, prompt: str, **kwargs) -> str:
        import anthropic
        client = anthropic.Anthropic(
            api_key=self.api_key,
            timeout=httpx.Timeout(120.0, connect=10.0)
        )

        response = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text
```

**Key Difference**: Uses Anthropic SDK message format

---

#### Cohere (Command)

**File**: `backend/app/ai/multi_llm_manager.py` (lines 725-760)

```python
class CohereProvider(BaseLLMProvider):
    def generate(self, prompt: str, **kwargs) -> str:
        import cohere
        client = cohere.Client(api_key=self.api_key)

        response = client.generate(
            model=self.model,
            prompt=prompt,
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )

        return response.generations[0].text
```

**Key Difference**: Uses Cohere SDK generate() method

---

## Local AI Flow (Ollama)

### Path A: Hebrew Mediation Chain → Ollama Provider

**Why Different?**
- Local models need **more structured guidance** than cloud models
- Ollama models benefit from **full Hebrew prompts** with system context
- **Hebrew Mediation Chain** provides sophisticated emotional support

---

#### Step 5: Hebrew Mediation Chain Processes Message

**File**: `backend/app/ai/chains/hebrew_mediation_chain.py` (lines 260-311)

```python
def _call(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Execute Hebrew mediation conversation flow"""

    instruction = inputs.get("instruction", "")
    student_response = inputs.get("student_response", "")
    mode = inputs.get("mode", "practice")
    student_context = inputs.get("student_context", {})
    assistance_type = inputs.get("assistance_type")

    # Assess student comprehension from their response
    if student_response:
        comprehension = self.memory.assess_comprehension(student_response)
    else:
        comprehension = "initial"

    # Get failed strategies from memory
    failed_strategies = self.memory.get_failed_strategies()

    # ═══════════════════════════════════════════════════════
    # INITIAL GREETING (First message only)
    # ═══════════════════════════════════════════════════════
    if (comprehension == "initial" and
        (not student_response or
         student_response.strip() in ["", "היי", "שלום", "הי"])):
        return {
            "response": "היי, אני לרנובוט, ואני פה כדי לעזור לך להבין את המשימות שלך. מה שלומך?",
            "strategy_used": "initial_greeting",
            "comprehension_level": comprehension
        }

    # ═══════════════════════════════════════════════════════
    # EMOTIONAL SUPPORT (Detected keywords like "עצוב", "כועס")
    # ═══════════════════════════════════════════════════════
    if comprehension == "emotional":
        strategy = "emotional_support"
    else:
        # Route to appropriate strategy
        strategy = self.router.route_strategy(comprehension, failed_strategies, mode, assistance_type)

    # Generate response based on strategy
    response = self._execute_strategy(strategy, instruction, student_context)

    # Track strategy attempt
    success = comprehension in ["understood", "partial"]
    self.memory.add_strategy_attempt(strategy, success)

    return {
        "response": response,
        "strategy_used": strategy,
        "comprehension_level": comprehension
    }
```

**Key Features**:
1. **Comprehension Assessment** → Analyzes student emotion/confusion
2. **Strategy Routing** → Picks best mediation approach (emotional support, breakdown, example, etc.)
3. **Memory Tracking** → Remembers failed strategies to avoid repeating
4. **Direct Emotional Responses** → Pre-defined responses for "אני עצוב", "אני כועס", etc.

---

#### Step 6: Execute Strategy with Full Hebrew Prompt

**File**: `backend/app/ai/chains/hebrew_mediation_chain.py` (lines 129-202)

```python
# Strategy templates for Ollama (full Hebrew prompts)
self.strategy_templates = {
    "emotional_support": PromptTemplate(
        input_variables=["instruction"],
        template="""התלמיד אמר: {instruction}

תגיב בעברית בחמימות ותמיכה. תגיב לרגש של התלמיד, לא למשימה.
השתמש במילים כמו: "אני כאן בשבילך", "אני מבין", "בוא ננסה יחד"
תגיב בשפה חמה ומעודדת, 1-2 משפטים קצרים.

תגובה:"""
    ),

    "highlight_keywords": PromptTemplate(
        input_variables=["instruction"],
        template="""בוא נסתכל על המילים החשובות בהוראה: {instruction}

זהה 2-3 מילות מפתח חשובות בהוראה.
הסבר מה כל מילה אומרת במילים פשוטות.

תגובה:"""
    ),

    "breakdown_steps": PromptTemplate(
        input_variables=["instruction"],
        template="""בוא נפרק את ההוראה לשלבים פשוטים: {instruction}

פרק את ההוראה ל-3-4 שלבים פשוטים וברורים.
כל שלב צריך להיות קצר וקל להבנה.
השתמש במילים כמו: "שלב ראשון", "אחר כך", "בסוף".

תגובה:"""
    ),

    # ... (more strategies)
}
```

**Why Full Prompts?**
- Local models (Llama, Aya) need **more explicit instructions**
- Cloud models (GPT, Gemini) are better at **understanding context**
- Hebrew prompts help local models maintain **language consistency**

---

#### Step 7: Ollama Provider Makes HTTP Request

**File**: `backend/app/ai/multi_llm_manager.py` (lines 823-881)

```python
class OllamaProvider(BaseLLMProvider):
    def generate(self, prompt: str, **kwargs) -> str:
        import requests
        import logging

        logger = logging.getLogger(__name__)

        try:
            # ═══════════════════════════════════════════════════════
            # HTTP REQUEST TO OLLAMA DOCKER CONTAINER
            # ═══════════════════════════════════════════════════════
            response = requests.post(
                f"{self.base_url}/api/generate",  # http://localhost:11434/api/generate
                json={
                    "model": self.model,  # e.g., "llama3.1:8b"
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens
                    }
                },
                timeout=120  # 2 minute timeout
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                raise Exception(f"Ollama API returned {response.status_code}")

        except requests.exceptions.Timeout:
            logger.error("Ollama request timed out after 120 seconds")
            raise Exception("Ollama timeout")
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise
```

**Key Points**:
- Ollama runs in Docker container (localhost:11434)
- HTTP POST to `/api/generate` endpoint
- `stream=False` for complete response
- 120 second timeout (Ollama is slower than cloud APIs)

---

#### Step 8: Ollama (Llama/Aya) Generates Response

**Example Prompt Sent to Ollama**:
```
בוא נפרק את ההוראה לשלבים פשוטים: תסביר לי מה זה חיבור

פרק את ההוראה ל-3-4 שלבים פשוטים וברורים.
כל שלב צריך להיות קצר וקל להבנה.
השתמש במילים כמו: "שלב ראשון", "אחר כך", "בסוף".

תגובה:
```

**Ollama Response**:
```
שלב ראשון: חיבור זה פעולה שבה לוקחים שני מספרים

אחר כך: מחברים אותם יחד כדי לקבל מספר חדש

שלב שלישי: המספר החדש נקרא "סכום"

בסוף: אפשר לחבר כמה מספרים שרוצים, תמיד נקבל סכום אחד
```

**Notice**:
- ✅ Follows Hebrew prompt structure exactly
- ✅ Uses keywords from prompt ("שלב ראשון", "אחר כך", "בסוף")
- ✅ Simple, clear Hebrew
- ✅ No direct calculation examples

---

## Key Differences Between Providers

### Comparison Table

| Feature | Google | OpenAI/Anthropic | Ollama (Local) |
|---------|--------|------------------|----------------|
| **Prompt Type** | Short, efficient | Short, efficient | Full, structured |
| **System Instruction** | Prepended to prompt | Native SDK support | Included in prompt |
| **Conversation History** | Included | Included | Included |
| **Chain Used** | Instruction Processor | Instruction Processor | Hebrew Mediation |
| **Response Speed** | Fast (~1-3s) | Fast (~1-3s) | Slower (~5-10s) |
| **Emotional Support** | Basic | Basic | Advanced (mediation) |
| **Cost** | Per-token (paid) | Per-token (paid) | Free (local) |
| **Special Handling** | System instruction prepend | None | Strategy routing |
| **No Direct Answers** | System instruction | Prompt guidance | Prompt guidance |

---

## Fixes Implemented

### 1. Conversation History Leak Fix

**Problem**: AI was echoing conversation history with "תלמיד:" prefixes

**Before**:
```
AI Response: "תלמיד: תסביר לי מה זה חיבור
לרנובוט: בטח! חיבור זה..."
```

**Fix** (`instruction_chain.py` lines 156-160):
```python
חשוב מאוד:
- ענה ישירות לתלמיד, אל תכתוב "תלמיד:" או "לרנובוט:"
- אל תחזור על השיחה הקודמת
- רק תן תשובה טבעית להודעה האחרונה
```

**After**:
```
AI Response: "בטח! חיבור זה פעולה מתמטית..."
```

---

### 2. No Direct Answers Rule (Strengthened)

**Problem**: GPT and Gemini giving direct answers like "5+3=8"

**Fix 1**: Added system instruction to Google (`multi_llm_manager.py` lines 531-547):
```python
self.system_instruction = """Critical rules:
- NEVER solve problems for the student
- NEVER provide final answers or numerical results
- ONLY explain methods and processes
- Students MUST work it out themselves"""
```

**Fix 2**: Added CRITICAL warning to all assistance methods (`instruction_chain.py` lines 287-298):
```python
strict_no_answer_rule = """
⚠️ CRITICAL EDUCATIONAL RULE - YOU MUST FOLLOW THIS:
- DO NOT give the final answer or solution
- DO NOT solve the problem for the student
- DO NOT provide numerical results or calculations
- ONLY explain the METHOD and PROCESS
- The student MUST work it out themselves
"""
```

**Result**: AI explains "how to add" instead of saying "8"

---

### 3. Task Reading Verification

**Added**: Second message prompt (`instruction_chain.py` lines 145-160)

```python
elif message_count == 1:
    default_prompt = """לפני שנתחיל, שאל בעדינות: "קראת כבר את המשימה שקיבלת?"

אם התלמיד אומר כן - המשך לעזור
אם התלמיד אומר לא - עודד אותו לקרוא קודם"""
```

**Purpose**: Encourages students to read task before asking for help

---

### 4. Clarity Follow-Up

**Added**: After-assistance prompt (`instruction_chain.py` lines 162-179)

```python
elif just_received_help:
    default_prompt = """עכשיו שאל: "האם עכשיו זה יותר ברור לך?"

אם התלמיד אומר לא - הצע לנסות דרך אחרת"""
```

**Purpose**: Checks understanding, offers alternative assistance if still confused

---

### 5. Photo Upload Encouragement

**Added**: When stuck prompt (`instruction_chain.py` lines 181-198)

```python
elif message_count >= 3 and not has_task_image and any(keyword in instruction_clean for keyword in [
    'לא מבין', 'קשה', 'לא הצלחתי'
]):
    default_prompt = """הצע בעדינות: "אם תרצה, תוכל לצלם את המשימה ולהעלות תמונה - ככה אוכל לעזור לך טוב יותר!"
```

**Purpose**: Suggests image upload when text-based help isn't working

---

### 6. Emoji Removal

**Changed**: All 43 user-facing emojis removed

**Before**:
```
🔍 **הסבר** - הסבר מה זה אומר
"יופי! אתה בכיוון הנכון 👍"
"היי, אני לרנובוט... מה שלומך? 😊"
```

**After**:
```
**הסבר** - הסבר מה זה אומר
"יופי! אתה בכיוון הנכון"
"היי, אני לרנובוט... מה שלומך?"
```

**Reason**: Hebrew specification explicitly forbids emojis

---

## Code Walkthrough

### File Structure

```
backend/app/
├── api/
│   └── chat.py                    # API endpoints
├── services/
│   ├── chat_service.py            # Chat business logic
│   └── hebrew_mediation_service.py # Mediation wrapper
├── ai/
│   ├── chains/
│   │   ├── instruction_chain.py   # Cloud model prompts
│   │   └── hebrew_mediation_chain.py # Local model prompts
│   ├── prompts/
│   │   └── hebrew_prompts.py      # Hebrew templates
│   └── multi_llm_manager.py       # Provider management
```

### Key Classes

**InstructionProcessor** (`instruction_chain.py`):
- `analyze_instruction()` - Natural conversation (cloud models)
- `breakdown_instruction()` - Breakdown to steps
- `provide_example()` - Give real-life example
- `explain_instruction()` - Explain in simple terms

**HebrewMediationChain** (`hebrew_mediation_chain.py`):
- `_call()` - Main mediation flow (local models)
- `_execute_strategy()` - Execute specific strategy
- `assess_comprehension()` - Detect student emotion/confusion

**MultiProviderLLMManager** (`multi_llm_manager.py`):
- `generate()` - Route to appropriate provider
- `add_api_key()` - Add cloud provider API key
- `remove_api_key()` - Remove provider

---

## Testing Examples

### Example 1: Google Gemini (Cloud)

**User**: "שלום"

**Flow**:
1. Chat service formats history (empty)
2. Instruction chain detects `is_first_message = True`
3. Builds greeting prompt
4. Multi-LLM manager routes to Google
5. Google prepends system instruction
6. Gemini generates response

**Response**: "היי, אני לרנובוט... איך תרצה שאעזור לך?"

---

### Example 2: Task Reading Check

**User**: "עזרה עם שאלה"

**Flow**:
1. Chat service formats history (1 previous message)
2. Instruction chain detects `message_count = 1`
3. Builds task reading prompt
4. Routes to Google
5. Gemini asks

**Response**: "קראת כבר את המשימה שקיבלת?"

---

### Example 3: Ollama Llama (Local)

**User**: "אני עצוב"

**Flow**:
1. Chat service checks provider = "ollama-llama3_1_8b"
2. Routes to Hebrew mediation chain
3. Mediation assesses comprehension = "emotional"
4. Returns direct emotional response (no LLM call needed)

**Response**: "אני מבין שאתה מרגיש עצוב. זה בסדר להרגיש כך. אני כאן בשבילך. איך אני יכול לעזור לך להרגיש יותר טוב?"

---

### Example 4: No Direct Answer Enforcement

**User**: "מה זה 5+3?"

**Flow**:
1. Instruction chain builds prompt with CRITICAL rule
2. Google prepends system instruction
3. Gemini respects both instructions

**Response**: "חיבור זה פעולה שבה אנו מצרפים שני מספרים. בשאלה הזו, אתה צריך לחבר את המספר הראשון (5) עם המספר השני (3). איך נעשה את זה? נתחיל מ-5 ונספור קדימה 3 צעדים. נסה בעצמך!"

**Notice**: Explains method, doesn't say "8"

---

**End of Chat Flow Analysis**
