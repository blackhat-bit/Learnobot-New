# scripts/create_admin.py
#!/usr/bin/env python
"""
Script to create an admin user for LearnoBot
Place this file in: learnobot-backend/scripts/create_admin.py
"""
"""
import sys
import os

# Add parent directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine
from app.models.user import Base, User, UserRole
from app.core.security import get_password_hash
import getpass

def create_admin():

Create an admin user interactively
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        print("=== Create LearnoBot Admin User ===")
        print()
        
        # Get admin details
        username = input("Enter admin username: ").strip()
        if not username:
            print("Username cannot be empty!")
            return
            
        email = input("Enter admin email: ").strip()
        if not email or '@' not in email:
            print("Invalid email address!")
            return
            
        password = getpass.getpass("Enter admin password: ")
        if len(password) < 6:
            print("Password must be at least 6 characters!")
            return
            
        confirm_password = getpass.getpass("Confirm password: ")
        if password != confirm_password:
            print("Passwords do not match!")
            return
        
        # Check if user exists
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            print(f"User with username '{username}' or email '{email}' already exists!")
            
            # Check if it's admin
            if existing_user.role == UserRole.ADMIN:
                print("This user is already an admin.")
            else:
                # Ask if they want to upgrade to admin
                upgrade = input(f"User exists as {existing_user.role}. Upgrade to admin? (y/n): ")
                if upgrade.lower() == 'y':
                    existing_user.role = UserRole.ADMIN
                    db.commit()
                    print(f"User '{username}' upgraded to admin successfully!")
            return
        
        # Create admin user
        admin_user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            role=UserRole.ADMIN,
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        
        print()
        print(f"✅ Admin user '{username}' created successfully!")
        print()
        print("You can now login with:")
        print(f"  Username: {username}")
        print(f"  Password: [hidden]")
        print()
        print("Admin capabilities:")
        print("  - Access AI Configuration Manager")
        print("  - View all students' analytics")
        print("  - Export research data")
        print("  - Switch between LLM providers")
        print("  - Modify system prompts")
        
    except Exception as e:
        print(f"Error creating admin: {str(e)}")
        db.rollback()
    finally:
        db.close()

def list_users():
    List all users in the system
    db = SessionLocal()
    
    try:
        users = db.query(User).all()
        
        if not users:
            print("No users found in the database.")
            return
            
        print("\n=== Current Users ===")
        print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Role':<10} {'Active':<8}")
        print("-" * 75)
        
        for user in users:
            print(f"{user.id:<5} {user.username:<20} {user.email:<30} {user.role.value:<10} {'Yes' if user.is_active else 'No':<8}")
        
        print(f"\nTotal users: {len(users)}")
        
    finally:
        db.close()

if __name__ == "__main__":
    # Check if user wants to list users
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        list_users()
    else:
        create_admin()
        """