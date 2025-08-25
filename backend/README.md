# Learnobot Backend

A comprehensive AI-powered educational platform backend built with FastAPI, featuring intelligent tutoring, multi-language support, and advanced learning management capabilities.

## Features

- 🤖 **AI-Powered Tutoring**: Integrated LLM support for personalized learning experiences
- 👥 **Multi-Role System**: Support for students, teachers, and administrators
- 💬 **Intelligent Chat**: Context-aware conversations with learning progress tracking
- 🔍 **OCR Integration**: Extract text from images and documents
- 🌍 **Multi-Language Support**: Real-time translation capabilities
- 📚 **Task Management**: Comprehensive assignment and progress tracking
- 🔐 **Secure Authentication**: JWT-based authentication with role-based access control
- 📊 **Analytics**: Learning progress and performance analytics

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT with bcrypt password hashing
- **AI/ML**: OpenAI GPT, LangChain, ChromaDB for vector storage
- **Background Tasks**: Celery with Redis
- **OCR**: Tesseract
- **Translation**: Google Translate API
- **Testing**: pytest with async support

## Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL
- Redis
- Docker (optional)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd learnobot-backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Set up the database:
```bash
alembic upgrade head
```

6. Run the application:
```bash
uvicorn app.main:app --reload
```

### Docker Setup

```bash
docker-compose up -d
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
learnobot-backend/
├── app/
│   ├── api/              # API endpoints
│   ├── core/             # Core functionality
│   ├── models/           # Database models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   └── ai/               # AI components
├── alembic/              # Database migrations
├── tests/                # Test files
└── scripts/              # Utility scripts
```

## Development

### Running Tests

```bash
pytest
```

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description"
```

Apply migrations:
```bash
alembic upgrade head
```

### Code Quality

The project follows PEP 8 style guidelines. Use tools like `black` and `flake8` for code formatting and linting.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.
