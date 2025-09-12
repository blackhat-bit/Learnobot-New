# LearnoBot

An AI-powered educational platform with Flutter frontend and FastAPI backend, featuring local LLM integration with Ollama.

## 🚀 Quick Start

### Prerequisites
- Flutter SDK
- Python 3.8+
- Docker & Docker Compose
- Git

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd learnobot-backend-Cursor
```

### 2. Install Dependencies

**Flutter Frontend:**
```bash
flutter pub get
```

**Python Backend:**
```bash
cd backend
pip install -r requirements.txt
```

### 3. Set Up Virtual Environment
```bash
cd backend
python -m venv .venv
.venv\scripts\activate.ps1  # Windows PowerShell
# or
source .venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
```

### 4. Environment Configuration
Create `backend/.env` file:
```env
DATABASE_URL=postgresql://learnobot:SomePassword@localhost:5432/learnobot_db
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-key
```

### 5. Start Docker Services
```bash
cd backend
docker-compose up -d
```

### 6. Download AI Models
```bash
docker exec backend-ollama-1 ollama pull llama3.1:8b
docker exec backend-ollama-1 ollama pull aya-expanse:8b
```

### 7. Start Backend Server
```bash
cd backend
.venv\scripts\activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 8. Start Frontend
```bash
# In another terminal, go back to project root
cd .. 
flutter run
```

### 9. Create Admin User
- Go to `http://localhost:8000/docs` (Swagger UI)
- Find the `POST /api/v1/auth/register` endpoint
- Click "Try it out" and use this body template:

```json
{
  "username": "admin",
  "email": "admin@learnobot.com",
  "password": "admin123",
  "full_name": "System Administrator",
  "role": "admin"
}
```

**Important Notes:**

- Fill the first 4 feild as you like, but the role MUST BE "admin"
- Only create **one** admin user manually
- All other users (students, teachers) should be created through the app interface
- The admin user will have full access to all system features

## 📁 Project Structure

```
learnobot-backend-Cursor/
├── lib/                           # Flutter frontend
│   ├── screens/                   # UI screens
│   │   ├── auth/                  # Authentication screens
│   │   ├── manager/               # Manager/Admin screens
│   │   ├── student/               # Student screens
│   │   ├── teacher/               # Teacher screens
│   │   └── splash_screen.dart     # App startup screen
│   ├── services/                  # API services & business logic
│   ├── models/                    # Data models
│   ├── widgets/                   # Reusable UI components
│   ├── constants/                 # App constants & strings
│   ├── utils/                     # Utility functions
│   └── main.dart                  # App entry point
├── backend/                       # FastAPI backend
│   ├── app/                       # Main application
│   │   ├── api/                   # API endpoints
│   │   ├── ai/                    # AI/LLM integration
│   │   ├── core/                  # Core functionality
│   │   ├── models/                # Database models
│   │   ├── schemas/               # Pydantic schemas
│   │   ├── services/              # Business logic
│   │   └── main.py                # FastAPI app
│   ├── data/                      # Persistent data
│   │   ├── postgres/              # Database files
│   │   └── ollama/                # AI model files
│   ├── scripts/                   # Utility scripts
│   ├── tests/                     # Backend tests
│   ├── alembic/                   # Database migrations
│   └── requirements.txt           # Python dependencies
├── assets/                        # Flutter assets
│   ├── fonts/                     # Custom fonts (Heebo)
│   ├── images/                    # App images
│   └── animations/                # Animation files
├── android/                       # Android platform files
├── ios/                          # iOS platform files
├── web/                          # Web platform files
├── windows/                      # Windows platform files
├── linux/                        # Linux platform files
├── macos/                        # macOS platform files
└── pubspec.yaml                  # Flutter dependencies
```

## 🔧 Key Features

- **Local AI Models**: Ollama integration with Llama3.1/3.2
- **Multi-User System**: Students, Teachers, Managers
- **Real-time Chat**: AI-powered tutoring
- **Hebrew Support**: Primary language with English fallback
- **Docker Integration**: Easy deployment and data persistence

## 📚 API Documentation

Once running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🛠️ Development

### Backend Development
```bash
cd backend
.venv\scripts\activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
flutter run
```

### Database Management
- PostgreSQL runs in Docker container
- Data persists in `backend/data/postgres/`
- Models persist in `backend/data/ollama/`

## 📝 Notes

- **No Python Scripts**: User creation is done via Swagger UI or app interface
- **Data Persistence**: Docker volumes ensure data survives container restarts
- **Model Downloads**: AI models are ~5GB each, download as needed
- **Environment**: Always activate virtual environment before running backend
- **Ignored Files**: `.env`, `.venv/`, `backend/data/`, and model files are gitignored (created automatically)

## 🆘 Troubleshooting

1. **Docker Issues**: Ensure Docker Desktop is running
2. **Port Conflicts**: Check if ports 8000, 5432, 11434 are available
3. **Model Downloads**: Models can take 10-15 minutes to download
4. **Virtual Environment**: Always activate `.venv` before running backend

## 📖 Flutter Resources

- [Lab: Write your first Flutter app](https://docs.flutter.dev/get-started/codelab)
- [Cookbook: Useful Flutter samples](https://docs.flutter.dev/cookbook)
- [Online documentation](https://docs.flutter.dev/)
