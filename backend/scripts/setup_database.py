#!/usr/bin/env python3
"""
Script to set up the database for the Learnobot application.
"""

import sys
import os
import subprocess

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import create_tables, engine
from app.models.llm_config import LLMConfig
from app.core.database import SessionLocal


def run_migrations():
    """Run Alembic migrations."""
    print("📦 Running database migrations...")
    
    try:
        # Initialize Alembic if not already done
        result = subprocess.run(
            ["alembic", "current"], 
            capture_output=True, 
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        if result.returncode != 0:
            print("🔄 Initializing Alembic...")
            subprocess.run(
                ["alembic", "revision", "--autogenerate", "-m", "Initial migration"],
                check=True,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
        
        # Run migrations
        subprocess.run(
            ["alembic", "upgrade", "head"],
            check=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        print("✅ Database migrations completed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Migration failed: {e}")
        return False
    except FileNotFoundError:
        print("❌ Alembic not found. Please install alembic: pip install alembic")
        return False


def create_default_llm_config():
    """Create default LLM configuration."""
    print("🤖 Creating default LLM configuration...")
    
    db = SessionLocal()
    try:
        # Check if default config already exists
        existing_config = db.query(LLMConfig).filter(
            LLMConfig.is_default == True
        ).first()
        
        if existing_config:
            print("ℹ️  Default LLM configuration already exists")
            return True
        
        # Create default OpenAI GPT-4 configuration
        default_config = LLMConfig(
            name="Default GPT-4",
            description="Default OpenAI GPT-4 configuration for Learnobot",
            provider="openai",
            model_name="gpt-4",
            temperature=0.7,
            max_tokens=1000,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            system_prompt="""You are an expert AI tutor designed to help students learn effectively. 
            Your role is to provide clear explanations, encourage critical thinking, 
            adapt to the student's level, and create engaging learning experiences.""",
            context_window=8192,
            max_requests_per_minute=60,
            max_requests_per_day=1000,
            supports_function_calling=True,
            supports_vision=False,
            supports_streaming=True,
            use_cases=["chat", "tutoring", "explanation", "practice"],
            subject_specializations=["mathematics", "science", "language_arts", "history"],
            content_filter_enabled=True,
            safety_level="medium",
            is_active=True,
            is_default=True,
            tags=["default", "gpt-4", "openai"]
        )
        
        db.add(default_config)
        db.commit()
        db.refresh(default_config)
        
        print(f"✅ Default LLM configuration created (ID: {default_config.id})")
        return True
        
    except Exception as e:
        print(f"❌ Error creating default LLM configuration: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()


def test_database_connection():
    """Test database connection."""
    print("🔌 Testing database connection...")
    
    try:
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            result.fetchone()
        
        print("✅ Database connection successful")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False


def main():
    """Main setup function."""
    print("🚀 Learnobot Database Setup")
    print("=" * 30)
    
    # Test database connection
    if not test_database_connection():
        print("\n💥 Setup failed: Cannot connect to database")
        print("Please check your DATABASE_URL configuration")
        sys.exit(1)
    
    # Run migrations
    if not run_migrations():
        print("\n💥 Setup failed: Migration error")
        sys.exit(1)
    
    # Create default LLM configuration
    if not create_default_llm_config():
        print("\n⚠️  Warning: Could not create default LLM configuration")
        print("You can create one manually later through the admin interface")
    
    print("\n🎉 Database setup completed successfully!")
    print("\nNext steps:")
    print("1. Run 'python scripts/create_admin.py' to create an admin user")
    print("2. Start the application with 'uvicorn app.main:app --reload'")
    print("3. Visit http://localhost:8000/docs to see the API documentation")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)
