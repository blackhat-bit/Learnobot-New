# app/main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from pathlib import Path
import asyncio
import time
from app.api import auth, chat, teacher, student, upload
from app.core.database import engine, SessionLocal
from app.models import user, chat as chat_models, task, llm_config, notification
from app.models.llm_config import LLMProvider
from app.config import settings
from app.api import llm_management
from app.ai.multi_llm_manager import multi_llm_manager

# Create database tables
user.Base.metadata.create_all(bind=engine)
chat_models.Base.metadata.create_all(bind=engine)
task.Base.metadata.create_all(bind=engine)
llm_config.Base.metadata.create_all(bind=engine)
notification.Base.metadata.create_all(bind=engine)

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

# Add timeout middleware to prevent stuck requests
@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    """Add request timeout to prevent backend from getting stuck"""

    # Set timeout based on endpoint
    if "upload-task" in str(request.url):
        timeout = 300  # 5 minutes for image processing
    elif "messages" in str(request.url):
        timeout = 180  # 3 minutes for AI responses
    else:
        timeout = 30   # 30 seconds for other requests

    try:
        start_time = time.time()
        response = await asyncio.wait_for(call_next(request), timeout=timeout)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=408,
            detail=f"Request timeout after {timeout} seconds"
        )

@app.on_event("startup")
async def startup_event():
    """Initialize providers on application startup"""
    print("🚀 Starting LearnoBot API...")
    
    # Initialize encryption service
    from app.core.encryption import init_encryption_service
    init_encryption_service(settings.ENCRYPTION_KEY)
    if settings.ENCRYPTION_KEY:
        print("✅ Encryption service initialized with key")
    else:
        print("⚠️  No ENCRYPTION_KEY - API keys will be stored in plain text (dev mode)")
    
    # Sync local providers to database
    sync_providers_to_database()
    
    # Load encrypted API keys from database and initialize providers
    from app.core.encryption import get_encryption_service
    from app.ai.multi_llm_manager import OpenAIProvider, AnthropicProvider, GoogleProvider, CohereProvider
    
    encryption_service = get_encryption_service()
    
    db = SessionLocal()
    try:
        providers_with_keys = db.query(LLMProvider).filter(
            LLMProvider.api_key.isnot(None),
            LLMProvider.type == "cloud"  # Only cloud providers need API keys
        ).all()
        
        for provider_db in providers_with_keys:
            # Decrypt the stored API key
            decrypted_key = encryption_service.decrypt(provider_db.api_key)
            
            if decrypted_key and len(decrypted_key) > 0:
                try:
                    # Initialize provider directly without re-storing (avoid double encryption)
                    provider_name = provider_db.name.lower()
                    
                    # Update in-memory settings
                    if provider_name == "openai":
                        settings.OPENAI_API_KEY = decrypted_key
                        provider_class = OpenAIProvider
                    elif provider_name == "anthropic":
                        settings.ANTHROPIC_API_KEY = decrypted_key
                        provider_class = AnthropicProvider
                    elif provider_name == "google":
                        settings.GOOGLE_API_KEY = decrypted_key
                        provider_class = GoogleProvider
                    elif provider_name == "cohere":
                        settings.COHERE_API_KEY = decrypted_key
                        provider_class = CohereProvider
                    else:
                        print(f"⚠️  Unknown provider: {provider_name}")
                        continue
                    
                    # Initialize provider instance
                    provider_instance = provider_class()
                    provider_instance.initialize({"api_key": decrypted_key})
                    
                    # Add to active providers (in-memory only, no DB write)
                    multi_llm_manager.providers[provider_name] = provider_instance
                    
                    print(f"✅ Loaded and initialized {provider_name} from database")
                    
                except Exception as e:
                    print(f"⚠️  Failed to initialize {provider_db.name}: {e}")
            else:
                print(f"⚠️  Could not decrypt API key for {provider_db.name}")
                
    except Exception as e:
        print(f"⚠️  Error loading API keys from database: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    # Create task images directory
    task_images_dir = Path("uploads/task_images")
    task_images_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Created task images directory: {task_images_dir}")
    
    print("✅ Startup complete!")

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

