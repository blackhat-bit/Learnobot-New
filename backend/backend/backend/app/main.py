from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.config import settings
from app.api import auth, chat, teacher, student, llm_management
from app.core.database import engine
from app.models import user, chat as chat_model, task, llm_config


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description="A comprehensive AI-powered educational platform backend",
        debug=settings.debug,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Trusted host middleware for production
    if not settings.debug:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["learnobot.com", "*.learnobot.com"]
        )
    
    # Include routers
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
    app.include_router(teacher.router, prefix="/api/v1/teacher", tags=["Teacher"])
    app.include_router(student.router, prefix="/api/v1/student", tags=["Student"])
    app.include_router(llm_management.router, prefix="/api/v1/llm", tags=["LLM Management"])
    
    @app.on_event("startup")
    async def startup_event():
        """Application startup event."""
        print(f"Starting {settings.app_name} v{settings.version}")
        print(f"Environment: {settings.environment}")
        print(f"Debug mode: {settings.debug}")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Application shutdown event."""
        print("Shutting down Learnobot Backend")
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc):
        """Global HTTP exception handler."""
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "status_code": exc.status_code}
        )
    
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint."""
        return {
            "message": f"Welcome to {settings.app_name}",
            "version": settings.version,
            "status": "running"
        }
    
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": settings.app_name}
    
    return app


# Create the app instance
app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )
