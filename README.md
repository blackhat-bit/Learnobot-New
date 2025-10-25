# LearnoBot

An AI-powered educational platform with Flutter frontend and FastAPI backend, featuring local LLM integration with Ollama.

## 🚀 Quick Start

### Recommended IDE
For the best development experience, we recommend using (one of the following):
- **Cursor** - [Download](https://cursor.sh/) (AI-powered code editor)
- **VS Code** - [Download](https://code.visualstudio.com/) with Flutter and Python extensions

Open the project in your IDE by opening the root folder (`learnobot-backend-Cursor`).

### Prerequisites
- **Flutter SDK** - [Installation Guide](https://flutter.dev/docs/get-started/install)
- **Python 3.8+** - [Download](https://www.python.org/downloads/)
- **Docker Desktop** - [Download](https://www.docker.com/products/docker-desktop)
- **Git** - [Download](https://git-scm.com/downloads)

### Step 1: Clone the Repository
```bash (in the IDE's terminal)
git clone <your-repo-url>
cd learnobot-backend-Cursor
```

### Step 2: Install Flutter Dependencies
```bash
flutter pub get
```

### Step 3: Setup Python Backend

Create and activate a virtual environment:

```bash
cd backend
python -m venv venv

# Windows PowerShell:
venv\Scripts\activate.ps1
or
.venv\Scripts\activate.ps1

# Mac/Linux:
source venv/bin/activate
```

**Verify activation:** Your terminal should show `(venv)` at the beginning of the line.

Install Python dependencies:
```bash
pip install -r requirements.txt
```

### Step 4: Generate Security Keys

The system requires two security keys:

#### 4a. Generate Encryption Key (for API keys)
```bash
cd backend
python scripts/generate_encryption_key.py
```

#### 4b. Generate Secret Key (for passwords and authentication)
```bash
# Generate a secure random secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Important:** Copy both generated keys - you'll need them in the next step!

### Step 5: Environment Configuration

Create a file named `.env` in the `backend` folder with the following content:

```env
# Required - Database connection
DATABASE_URL=postgresql://learnobot:YOUR_SECURE_PASSWORD@localhost:5432/learnobot_db

# Required - Security keys (generate your own!)
SECRET_KEY=paste-your-secret-key-from-step-4b-here
ENCRYPTION_KEY=paste-your-encryption-key-from-step-4a-here

# Optional - Cloud AI providers (for FIRST-TIME SETUP only)
# IMPORTANT: After first setup, remove these keys from .env and manage via Manager Panel
# Database is the single source of truth - .env keys are only used on first run
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
COHERE_API_KEY=
```

**Notes:**
- **SECRET_KEY**: Paste the key from Step 4b (used for password hashing and JWT tokens)
- **ENCRYPTION_KEY**: Paste the key from Step 4a (used for encrypting API keys in database)
- **Change the database password**: Replace `YOUR_SECURE_PASSWORD` with a strong password
- Cloud AI provider keys are optional - the app works with local Ollama models
- **IMPORTANT API Key Management**:
  - `.env` keys are ONLY used for first-time initialization
  - After adding keys via Manager Panel, **remove them from .env**
  - Database is the single source of truth for API keys
  - If keys remain in .env, they'll be re-added on first startup (one-time only)
  - **Recommended**: Leave .env empty and add all keys via Manager Panel

### Step 6: Start Docker Services

**Important:** Make sure you are in the `backend` folder!

```bash
# If not already there:
cd backend

# Start all services:
docker-compose up --build
```

**What this does:**
- Starts PostgreSQL database (port 5432)
- Starts Ollama AI service (port 11434)  
- Starts backend API server with OCR support (port 8000)
- First run takes 2-3 minutes to download Docker images

**Wait for this message:** `Application startup complete`

**Keep this terminal running!** Don't close it - the services need to stay active.

### Step 7: Verify Services Are Running

Open a **new terminal** and check:

```bash
cd backend
docker-compose ps
```

**Expected output:** All services should show "Up" status:
```
NAME                   STATUS
backend-backend-1      Up
backend-postgres-1     Up
backend-ollama-1       Up
```

**Quick test:** Open http://localhost:8000/docs in your browser
- You should see the Swagger API documentation page
- If it shows a connection error, wait 30 seconds and try again

### Step 8: Download AI Models (Optional but Recommended)

These models enable offline AI tutoring. Each model is ~5GB and takes 5-10 minutes to download.

Open a **new terminal**:

```bash
# Download main English model (recommended):
docker exec backend-ollama-1 ollama pull llama3.1:8b

# Download Hebrew model (optional):
docker exec backend-ollama-1 ollama pull aya-expanse:8b

#if you know any other models that may work better you can experience with those
```

**Verify download:**
```bash
docker exec backend-ollama-1 ollama list
```

You should see the downloaded models listed.

### Step 9: Start Flutter App

Open a **new terminal** (keep Docker running in the other):

```bash
# Go back to project root:
cd ..

# Start Flutter:
flutter run
```

**Select your platform:**
- Press **1** for Chrome (web)
- Press **2** for Windows
- Or select another available platform

**Verify:** App should show splash screen, then the login screen.

### Step 10: Create Admin User

1. Open your web browser
2. Go to http://localhost:8000/docs
3. Scroll down to find **"POST /api/v1/auth/register"**
4. Click **"Try it out"**
5. Replace the example JSON with:

```json
{
  "username": "admin",
  "email": "admin@learnobot.com",
  "password": "admin123",
  "full_name": "System Administrator",
  "role": "admin"
}
```

6. Click **"Execute"**
7. Look for **Response Code 200** - success!

**Important Notes:**
- The `"role"` field MUST be exactly `"admin"` (lowercase, with quotes)
- Create **only ONE** admin user this way
- Create students and teachers through the app interface
- Login credentials: username `admin`, password `admin123`

## ✅ Verify Everything Works

Check that all components are running:

1. **Backend API:** http://localhost:8000/docs should show Swagger UI
2. **Docker Services:** `docker-compose ps` should show all services "Up"
3. **Flutter App:** Should show login screen
4. **Admin Login:** Use username "admin" and password "admin123"

If all four work, you're ready to go! 🎉

If any don't work, see Troubleshooting below.

## 📁 Project Structure

```
learnobot-backend-Cursor/
├── lib/                           # Flutter frontend
│   ├── screens/                   # UI screens
│   │   ├── auth/                  # Authentication screens
│   │   ├── manager/               # Manager/Admin screens
│   │   ├── student/               # Student screens
│   │   └── teacher/               # Teacher screens
│   ├── services/                  # API services & business logic
│   ├── models/                    # Data models
│   ├── widgets/                   # Reusable UI components
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
├── assets/                        # Flutter assets (fonts, images)
└── pubspec.yaml                   # Flutter dependencies
```

## ⚠️ Important Notes

### Local Model Stability
**The app is designed to work primarily with cloud AI providers for stability.** While local Ollama models are supported, they may have limitations:

- **Performance**: Local models may be slower and less reliable than cloud providers
- **Resource Usage**: Requires significant RAM (8GB+ recommended)
- **Model Quality**: Cloud providers (OpenAI, Anthropic, Google) generally provide better responses
- **Recommended Setup**: Use cloud providers for production, local models for development/testing

### API Key Management
**For security and stability, we recommend adding API keys through the Manager Panel:**

1. **After initial setup**, log in as admin (username: "admin", password: "admin123")
2. **Go to Manager Panel** → AI Configuration → API Keys
3. **Add your API keys** through the secure interface
4. **Keys are encrypted** and stored safely in the database
5. **No need to edit .env file** for API keys

This approach is more secure than storing keys in environment files.

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
  - **Research Data Export**: Detailed interaction logs for research purposes - available in Research Analytics screen
  - **Student Analytics Export**: Complete student profiles with performance metrics - available via API endpoint
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
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🛠️ Development

### Backend Development (without Docker)

If you want to run the backend locally for development (with hot-reload):

```bash
# Stop Docker backend container:
docker stop backend-backend-1

# Run locally:
cd backend
venv\Scripts\activate.ps1  # Windows
# or
source venv/bin/activate   # Mac/Linux

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Note:** OCR image upload won't work without Docker (requires Tesseract). All other features work normally.

### Frontend Development

```bash
flutter run
```

### Database Management
- PostgreSQL runs in Docker container
- Data persists in `backend/data/postgres/`
- Models persist in `backend/data/ollama/`

### Useful Docker Commands

```bash
# Start all services (first time or after changes):
docker-compose up --build

# Start services in background (subsequent runs):
docker-compose up -d

# Stop all services:
docker-compose down

# View logs:
docker-compose logs -f

# View logs for specific service:
docker-compose logs -f backend

# Restart a specific service:
docker-compose restart backend
```

## 📝 Important Notes

- **Data Persistence**: Docker volumes ensure data survives container restarts
- **Model Downloads**: AI models are ~5GB each, download as needed
- **Environment Files**: `.env` files are gitignored and must be created locally
- **Virtual Environment**: Always activate `venv` before running backend locally
- **Admin Access**: Only create ONE admin user manually via Swagger UI
- **User Creation**: Create students and teachers through the app interface

## 🆘 Troubleshooting

### "Docker not found" or Docker not running
**Problem:** Docker Desktop is not installed or not running.

**Solution:**
- Install Docker Desktop from https://www.docker.com/products/docker-desktop
- Make sure Docker Desktop is running (check system tray/menu bar)
- Restart terminal after installation

### "Port already in use" (8000, 5432, or 11434)
**Problem:** Another service is using the required port.

**Solution:**
```bash
# Windows - Find what's using the port:
netstat -ano | findstr :8000

# Mac/Linux:
lsof -i :8000

# Then stop the conflicting service, or change ports in docker-compose.yml
```

### "Python not found" or wrong Python version
**Problem:** Python is not installed or wrong version.

**Solution:**
```bash
# Check version (should be 3.8+):
python --version

# If using python3 command instead:
python3 -m venv venv
python3 -m pip install -r requirements.txt
```

### "Flutter not found"
**Problem:** Flutter is not installed or not in PATH.

**Solution:**
- Make sure Flutter is in your system PATH
- Restart terminal after installation
- Run `flutter doctor` to check setup and fix any issues

### "Virtual environment not activating" (Windows)
**Problem:** PowerShell execution policy prevents running scripts.

**Solution:**
```bash
# Run this once:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then try activating again:
venv\Scripts\activate.ps1
```

### "Encryption key error" or API keys not working
**Problem:** ENCRYPTION_KEY missing or incorrect in .env file.

**Solution:**
- Make sure you ran: `python scripts/generate_encryption_key.py`
- Copy the ENTIRE key output to `.env` file
- Key format should be: `ENCRYPTION_KEY=long-base64-string-here`
- No spaces around the `=` sign

### "Models not downloading" or "Local models not working"
**Problem:** Network issues, Ollama service not running, or local model instability.

**Solution:**
- Check internet connection
- Models are large (5GB each) - download takes 5-10 minutes
- Verify Ollama is running: `docker-compose ps` (backend-ollama-1 should be "Up")
- Try again: `docker exec backend-ollama-1 ollama pull llama3.1:8b`
- Check progress: `docker exec backend-ollama-1 ollama list`

**If local models are unstable:**
- **Recommended**: Use cloud AI providers instead (OpenAI, Anthropic, Google)
- Add API keys through Manager Panel → AI Configuration → API Keys
- Cloud providers are more reliable and provide better responses
- Local models are mainly for development/testing

### "Flutter app won't start" or build errors
**Problem:** Flutter dependencies not installed or cache issues.

**Solution:**
```bash
# Clean and rebuild:
flutter clean
flutter pub get
flutter run
```

### "Admin user creation fails"
**Problem:** Backend not running, wrong JSON format, or user already exists.

**Solution:**
- Check backend is running: http://localhost:8000/docs should load
- Make sure `"role"` is exactly `"admin"` (lowercase, with quotes)
- Check the response in Swagger UI for error details
- View backend logs: `docker-compose logs backend`
- If user exists, you can login with those credentials

### "Can't access http://localhost:8000"
**Problem:** Backend service not running or failed to start.

**Solution:**
```bash
# Check service status:
docker-compose ps

# If backend shows "Exit" status, check logs:
docker-compose logs backend

# Try restarting:
docker-compose down
docker-compose up --build
```

### Still having issues?

```bash
# Check all Docker logs:
docker-compose logs -f

# Restart everything from scratch:
docker-compose down
docker-compose up --build

# If database issues, remove volumes and restart (WARNING: deletes all data):
docker-compose down -v
docker-compose up --build
```

## 🎉 You're Ready!

Once everything is running:
- **Flutter App**: Should open automatically and show login screen
- **Backend API**: Available at http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Admin Panel**: Login with username `admin` and password `admin123`

Enjoy using LearnoBot! 🚀
