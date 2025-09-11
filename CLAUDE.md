# Claude Code Configuration

# LearnoBot - Educational AI Assistant

## Project Overview
**AI-powered educational assistant helping elementary students with learning disabilities understand Hebrew instructional tasks**

### What LearnoBot Does
- Students scan/type homework instructions → AI breaks them down into simple steps
- Provides Hebrew explanations, examples, and guidance  
- Two modes: Practice (full help) vs Test (minimal hints)
- Teachers track student progress and tune AI behavior

### Core Components
1. **AI Chatbot** - Core instruction mediation in Hebrew
2. **Student Interface** - Flutter app for iOS/Android  
3. **Teacher Management Panel** - Progress tracking + AI tuning tools
4. **Data Logging** - Research analytics for academic study

## Technical Stack
### Frontend (Flutter/Dart)
- Hebrew UI for students with learning disabilities
- Provider for state management
- SQLite for local storage
- HTTP client for API communication


## Project Structure
```
learnobot-backend-Cursor/
├── lib/                    # Flutter Dart source code
├── backend/               # Python FastAPI backend
│   ├── app/              # Backend application code
│   ├── requirements.txt  # Python dependencies
│   └── README.md        # Backend documentation
├── pubspec.yaml          # Flutter dependencies
└── analysis_options.yaml # Dart linting rules
```

## Key Commands
### Flutter (Frontend)
- `flutter run` - Run the mobile app
- `flutter test` - Run Flutter tests
- `flutter pub get` - Install Flutter dependencies
- `flutter build` - Build the app
  

### Backend
- `cd backend && docker-compose up -d `- start the postgress db and the ollama cotainers
- `.venv\Scripts\activate.ps1`- activate python inviroment  
- `cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` - Run FastAPI server
- `cd backend && pytest` - Run backend tests
- `cd backend && pip install -r requirements.txt` - Install Python dependencies
- `cd backend && alembic upgrade head` - Run database migrations

## Technologies Used
### Frontend (Flutter)
- Provider for state management
- SQLite for local storage
- HTTP client for API communication
- Google Generative AI integration

### Backend (FastAPI)
- PostgreSQL database with SQLAlchemy ORM
- Multi-LLM support (Ollama, OpenAI, Anthropic)
- LangChain integration for educational conversations
- JWT authentication
- OpenAI GPT integration
- Celery for background tasks
- OCR with Tesseract
- Translation services

## Development Notes
- This is a full-stack educational AI application
- Backend serves API endpoints for the Flutter mobile app
- Uses AI/ML for intelligent tutoring and chat features
- Supports multiple user roles (students, teachers, administrators)