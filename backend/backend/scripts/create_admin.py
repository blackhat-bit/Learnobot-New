#!/usr/bin/env python3
"""
Script to create an admin user for the Learnobot application.
"""

import asyncio
import sys
import os

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, create_tables
from app.models.user import User, UserRole
from app.core.security import get_password_hash


def create_admin_user():
    """Create an admin user interactively."""
    
    print("🚀 Learnobot Admin User Creation")
    print("=" * 40)
    
    # Create tables if they don't exist
    create_tables()
    
    # Get user input
    email = input("Enter admin email: ").strip()
    if not email:
        print("❌ Email is required")
        return False
    
    username = input("Enter admin username: ").strip()
    if not username:
        print("❌ Username is required")
        return False
    
    full_name = input("Enter admin full name: ").strip()
    if not full_name:
        print("❌ Full name is required")
        return False
    
    password = input("Enter admin password (min 8 characters): ").strip()
    if len(password) < 8:
        print("❌ Password must be at least 8 characters")
        return False
    
    confirm_password = input("Confirm password: ").strip()
    if password != confirm_password:
        print("❌ Passwords do not match")
        return False
    
    # Create admin user
    db: Session = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == email) | (User.username == username)
        ).first()
        
        if existing_user:
            if existing_user.email == email:
                print(f"❌ User with email '{email}' already exists")
            else:
                print(f"❌ User with username '{username}' already exists")
            return False
        
        # Create new admin user
        admin_user = User(
            email=email,
            username=username,
            full_name=full_name,
            hashed_password=get_password_hash(password),
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("\n✅ Admin user created successfully!")
        print(f"   ID: {admin_user.id}")
        print(f"   Email: {admin_user.email}")
        print(f"   Username: {admin_user.username}")
        print(f"   Role: {admin_user.role.value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin user: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()


def main():
    """Main function."""
    try:
        success = create_admin_user()
        if success:
            print("\n🎉 You can now log in with the admin credentials!")
            sys.exit(0)
        else:
            print("\n💥 Failed to create admin user")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
