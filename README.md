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
DATABASE_URL=postgresql://learnobot:StrongPassword123!@localhost:5432/learnobot_db
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
docker exec backend-ollama-1 ollama pull llama3.2:1b
```

### 7. Start Backend Server
```bash
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
- Use the registration endpoint to create 1 admin/manager user

## 📁 Project Structure

```
learnobot-backend-Cursor/
├── lib/                    # Flutter frontend
│   ├── screens/           # UI screens
│   ├── services/          # API services
│   └── models/            # Data models
├── backend/               # FastAPI backend
│   ├── app/              # Main application
│   ├── data/             # Persistent data (DB, models)
│   └── scripts/          # Utility scripts
└── assets/               # Flutter assets
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

## 🆘 Troubleshooting

1. **Docker Issues**: Ensure Docker Desktop is running
2. **Port Conflicts**: Check if ports 8000, 5432, 11434 are available
3. **Model Downloads**: Models can take 10-15 minutes to download
4. **Virtual Environment**: Always activate `.venv` before running backend

## 📖 Flutter Resources

- [Lab: Write your first Flutter app](https://docs.flutter.dev/get-started/codelab)
- [Cookbook: Useful Flutter samples](https://docs.flutter.dev/cookbook)
- [Online documentation](https://docs.flutter.dev/)
