#!/usr/bin/env python3
"""
Development server script for the Learnobot application.
"""

import os
import sys
import subprocess
import argparse
import signal
import time
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "alembic",
        "pydantic"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nRun: pip install -r requirements.txt")
        return False
    
    return True


def check_database_setup():
    """Check if database is set up."""
    try:
        from app.core.database import engine
        with engine.connect() as connection:
            # Try to query a table that should exist
            result = connection.execute("SELECT 1")
            result.fetchone()
        return True
    except Exception:
        return False


def setup_database():
    """Set up database if needed."""
    print("🔧 Setting up database...")
    
    script_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "setup_database.py"
    )
    
    try:
        subprocess.run([sys.executable, script_path], check=True)
        return True
    except subprocess.CalledProcessError:
        print("❌ Database setup failed")
        return False


def start_server(host="127.0.0.1", port=8000, reload=True, workers=1):
    """Start the development server."""
    
    cmd = [
        "uvicorn",
        "app.main:app",
        "--host", host,
        "--port", str(port)
    ]
    
    if reload:
        cmd.append("--reload")
    
    if workers > 1:
        cmd.extend(["--workers", str(workers)])
    
    print(f"🚀 Starting Learnobot server on http://{host}:{port}")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔧 Alternative docs: http://localhost:8000/redoc")
    print("\nPress Ctrl+C to stop the server")
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n⏹️  Server stopped")
    except FileNotFoundError:
        print("❌ uvicorn not found. Install with: pip install uvicorn[standard]")
        return False
    
    return True


def check_environment():
    """Check environment setup."""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("⚠️  .env file not found")
        
        # Check if .env.example exists
        env_example = Path(".env.example")
        if env_example.exists():
            print("💡 Copying .env.example to .env")
            env_content = env_example.read_text()
            env_file.write_text(env_content)
            print("✅ .env file created from template")
            print("🔧 Please edit .env file with your configuration")
        else:
            print("❌ No .env.example file found")
            return False
    
    return True


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Learnobot Development Server")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Disable auto-reload"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (default: 1)"
    )
    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="Skip dependency and database checks"
    )
    parser.add_argument(
        "--setup-db",
        action="store_true",
        help="Set up database before starting"
    )
    
    args = parser.parse_args()
    
    print("🚀 Learnobot Development Server")
    print("=" * 32)
    
    if not args.skip_checks:
        # Check environment
        if not check_environment():
            print("💥 Environment check failed")
            sys.exit(1)
        
        # Check dependencies
        if not check_dependencies():
            print("💥 Dependency check failed")
            sys.exit(1)
        
        # Check database setup
        if not check_database_setup() or args.setup_db:
            if not setup_database():
                print("💥 Database setup failed")
                sys.exit(1)
        
        print("✅ All checks passed!")
        print()
    
    # Start server
    reload = not args.no_reload
    
    success = start_server(
        host=args.host,
        port=args.port,
        reload=reload,
        workers=args.workers
    )
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Startup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)
