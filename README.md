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


### 3.Create a virtual environment:
**Python Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate.ps1  # Windows PowerShell
# or
source venv/bin/activate   # Linux/Mac
```


### 3. Install dependencies:
```bash
pip install -r requirements.txt
(you should create beforehand requirements.txt)
```


### 4. Environment Configuration
Create `backend/.env` file:
```env
DATABASE_URL=postgresql://learnobot:SomePassword@localhost:5432/learnobot_db
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-key
```

### 5. Start Docker Services (Database + Ollama + Backend with OCR)
```bash
cd backend (if not in backend folder)
docker-compose up --build
```
**This starts all services including the backend with OCR support built-in. No manual Tesseract installation needed!**

### 6. Download AI Models
```bash
docker exec backend-ollama-1 ollama pull llama3.1:8b
docker exec backend-ollama-1 ollama pull aya-expanse:8b
```

### 7. Backend Server
**Option A - Docker Backend (Easiest):** Already running at `http://localhost:8000` ✅
- ✅ OCR image upload works automatically

**Option B - Local Development:**
```bash
# Stop Docker backend container
docker stop backend-backend-1

# Run locally for development
cd backend
venv\Scripts\activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- ⚠️ **OCR image upload won't work** (requires manual Tesseract installation)
- ✅ All other features work (manual text input, AI chat, etc.)

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

## 👨‍💼 Manager/Admin Features

### AI Configuration Management
Managers have exclusive access to the **AI Configuration Manager** panel where they can:

- **Model Management**: Activate/deactivate AI models (Ollama local models, OpenAI, Anthropic, etc.)
- **Provider Configuration**: Switch between different AI providers and configure API keys
- **Prompt Engineering**: Customize system prompts for different modes (practice vs test)
- **Performance Testing**: Compare responses from different AI models
- **Real-time Monitoring**: View provider status and model availability

### Analytics & Reporting
The most important feature for managers is the **analytics and CSV export system**:

- **Student Progress Tracking**: Monitor individual student performance and engagement
- **Conversation Analytics**: View detailed chat logs and interaction patterns
- **Time Tracking**: Track total conversation time and average session duration
- **CSV Export**: Two types of data export available
  - **Research Data Export**: Detailed interaction logs for research purposes (`/export/csv`) - **Download button in Research Analytics screen**
  - **Student Analytics Export**: Complete student profiles with performance metrics (`/export/students/csv`) - **Available via API endpoint**
- **Usage Statistics**: Monitor system usage and identify trends

### Access Control
- **User Management**: Create and manage student/teacher accounts
- **Role-based Access**: Control what each user type can access
- **System Administration**: Full access to all system features and configurations

## 🔧 Key Features

- **Local AI Models**: Ollama integration with Llama3.1/3.2
- **Multi-User System**: Students, Teachers, Managers
- **Real-time Chat**: AI-powered tutoring
- **OCR Text Recognition**: Upload homework images with automatic Hebrew text extraction
- **Hebrew Support**: Primary language with English fallback
- **Docker Integration**: Easy deployment and data persistence
- **Tesseract OCR**: Built-in support for Hebrew and English text recognition

## 📚 API Documentation

Once running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🛠️ Development

### Backend Development
```bash
cd backend
venv\Scripts\activate.ps1
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

### Docker Commands
```bash
# Start all services (first time or after changes)
docker-compose up --build

# Start services (subsequent runs)
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild only backend with OCR updates
docker-compose up --build backend
```

## 📝 Notes

- **No Python Scripts**: User creation is done via Swagger UI or app interface
- **Data Persistence**: Docker volumes ensure data survives container restarts
- **Model Downloads**: AI models are ~5GB each, download as needed
- **Environment**: Always activate virtual environment before running backend
- **Ignored Files**: `.env`, `venv/`, `backend/data/`, and model files are gitignored (created automatically)

## 🆘 Troubleshooting

1. **Docker Issues**: Ensure Docker Desktop is running
2. **Port Conflicts**: Check if ports 8000, 5432, 11434 are available
3. **Model Downloads**: Models can take 10-15 minutes to download
4. **OCR Not Working**:
   - If using Docker: Rebuild backend container with `docker-compose up --build`
   - If running backend locally (without Docker): Install Tesseract OCR manually
5. **Virtual Environment**: Always activate `venv` before running backend

