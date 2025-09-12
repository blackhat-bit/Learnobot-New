# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from pathlib import Path
from app.api import auth, chat, teacher, student, upload
from app.core.database import engine, SessionLocal
from app.models import user, chat as chat_models, task, llm_config
from app.models.llm_config import LLMProvider
from app.config import settings
from app.api import llm_management
from app.ai.multi_llm_manager import multi_llm_manager

# Create database tables
user.Base.metadata.create_all(bind=engine)
chat_models.Base.metadata.create_all(bind=engine)
task.Base.metadata.create_all(bind=engine)
llm_config.Base.metadata.create_all(bind=engine)

def sync_providers_to_database():
    """Sync detected LLM providers to database"""
    db = SessionLocal()
    try:
        for provider_name, provider_instance in multi_llm_manager.providers.items():
            # Checkctivae if provider already exists
            existing = db.query(LLMProvider).filter(LLMProvider.name == provider_name).first()
            
            if not existing:
                # Create new provider entry
                provider_info = provider_instance.get_info()
                new_provider = LLMProvider(
                    name=provider_name,
                    type=provider_info.get("type", "unknown"),
                    is_active=True,
                    config=provider_info
                )
                db.add(new_provider)
                print(f" Added LLM provider: {provider_name}")
        
        db.commit()
        print(f"🔄 Provider sync complete. Total providers: {len(multi_llm_manager.providers)}")
        
    except Exception as e:
        print(f" Failed to sync providers: {e}")
        db.rollback()
    finally:
        db.close()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_PREFIX}/openapi.json"
)

@app.on_event("startup")
async def startup_event():
    """Initialize providers on application startup"""
    print(" Starting LearnoBot API...")
    sync_providers_to_database()
    print(" Startup complete!")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)

# Mount static files for serving uploaded images
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_PREFIX}/auth", tags=["auth"])
app.include_router(chat.router, prefix=f"{settings.API_PREFIX}/chat", tags=["chat"])
app.include_router(teacher.router, prefix=f"{settings.API_PREFIX}/teacher", tags=["teacher"])
app.include_router(student.router, prefix=f"{settings.API_PREFIX}/student", tags=["student"])
app.include_router(llm_management.router, prefix=f"{settings.API_PREFIX}/llm", tags=["llm_management"])
app.include_router(upload.router, prefix=f"{settings.API_PREFIX}/upload", tags=["upload"])

# Import analytics router
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

