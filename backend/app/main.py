# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from app.api import auth, chat, teacher, student
from app.core.database import engine
from app.models import user, chat as chat_models, task, llm_config
from app.config import settings
from app.api import llm_management

# Create database tables
user.Base.metadata.create_all(bind=engine)
chat_models.Base.metadata.create_all(bind=engine)
task.Base.metadata.create_all(bind=engine)
llm_config.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_PREFIX}/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_PREFIX}/auth", tags=["auth"])
app.include_router(chat.router, prefix=f"{settings.API_PREFIX}/chat", tags=["chat"])
app.include_router(teacher.router, prefix=f"{settings.API_PREFIX}/teacher", tags=["teacher"])
app.include_router(student.router, prefix=f"{settings.API_PREFIX}/student", tags=["student"])
app.include_router(llm_management.router, prefix=f"{settings.API_PREFIX}/llm", tags=["llm_management"])

# Import analytics router (we'll create this next)
from app.api import analytics
app.include_router(analytics.router, prefix=f"{settings.API_PREFIX}/analytics", tags=["analytics"])

@app.get("/")
def read_root():
    return {"message": "Welcome to LearnoBot API"}

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "timestamp": datetime.utcnow()
    }

