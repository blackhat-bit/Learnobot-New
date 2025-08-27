.c#!/usr/bin/env python
"""
Script to create different types of users for LearnoBot
Place this file in: learnobot-backend/scripts/create_users.py
"""
import sys
import os

# Add parent directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine
from app.models.user import Base, User, UserRole, StudentProfile, TeacherProfile
from app.core.security import get_password_hash
import getpass

def create_user():
    """Create a user interactively"""
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        print("=== Create LearnoBot User ===")
        print()
        
        # Choose user type
        print("Select user type:")
        print("1. Teacher")
        print("2. Student") 
        print("3. Admin")
        
        while True:
            choice = input("Enter choice (1-3): ").strip()
            if choice == "1":
                role = UserRole.TEACHER
                role_name = "Teacher"
                break
            elif choice == "2":
                role = UserRole.STUDENT
                role_name = "Student"
                break
            elif choice == "3":
                role = UserRole.ADMIN
                role_name = "Admin"
                break
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
        
        print(f"\nCreating {role_name} user...")
        print()
        
        # Get user details
        username = input("Enter username: ").strip()
        if not username:
            print("Username cannot be empty!")
            return
            
        email = input("Enter email: ").strip()
        if not email or '@' not in email:
            print("Invalid email address!")
            return
            
        password = getpass.getpass("Enter password: ")
        if len(password) < 6:
            print("Password must be at least 6 characters!")
            return
            
        confirm_password = getpass.getpass("Confirm password: ")
        if password != confirm_password:
            print("Passwords do not match!")
            return
        
        # Get additional info based on role
        full_name = input("Enter full name: ").strip()
        if not full_name:
            print("Full name cannot be empty!")
            return
        
        # Check if user exists
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            print(f"User with username '{username}' or email '{email}' already exists!")
            return
        
        # Create base user
        user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            role=role,
            is_active=True
        )
        
        db.add(user)
        db.flush()  # Get the user ID
        
        # Create profile based on role
        if role == UserRole.TEACHER:
            # Get teacher-specific info
            school = input("Enter school name (optional): ").strip() or "Default School"
            subject = input("Enter subject taught (optional): ").strip() or "General"
            
            teacher_profile = TeacherProfile(
                user_id=user.id,
                full_name=full_name,
                school=school,
                subject=subject
            )
            db.add(teacher_profile)
            
        elif role == UserRole.STUDENT:
            # Get student-specific info
            grade = input("Enter grade/class: ").strip() or "Unknown"
            school = input("Enter school name (optional): ").strip() or "Default School"
            
            # Difficulty level (1-5 scale)
            while True:
                try:
                    difficulty = input("Enter difficulty level (1-5, where 5 is most challenging): ").strip()
                    difficulty_level = int(difficulty) if difficulty else 3
                    if 1 <= difficulty_level <= 5:
                        break
                    else:
                        print("Difficulty level must be between 1 and 5.")
                except ValueError:
                    print("Please enter a valid number.")
            
            description = input("Enter learning description (optional): ").strip() or "Student learning profile"
            
            student_profile = StudentProfile(
                user_id=user.id,
                full_name=full_name,
                grade=grade,
                school=school,
                difficulty_level=difficulty_level,
                description=description
            )
            db.add(student_profile)
        
        db.commit()
        
        print()
        print(f"✅ {role_name} user '{username}' created successfully!")
        print()
        print("User details:")
        print(f"  Username: {username}")
        print(f"  Email: {email}")
        print(f"  Full Name: {full_name}")
        print(f"  Role: {role_name}")
        
        if role == UserRole.TEACHER:
            print(f"  School: {school}")
            print(f"  Subject: {subject}")
        elif role == UserRole.STUDENT:
            print(f"  Grade: {grade}")
            print(f"  School: {school}")
            print(f"  Difficulty Level: {difficulty_level}")
        
        print()
        print(f"{role_name} capabilities:")
        if role == UserRole.ADMIN:
            print("  - Access AI Configuration Manager")
            print("  - View all students' analytics")
            print("  - Export research data")
            print("  - Switch between LLM providers")
            print("  - Modify system prompts")
        elif role == UserRole.TEACHER:
            print("  - View assigned students")
            print("  - Monitor student progress")
            print("  - Access chat functionality")
            print("  - View basic analytics")
        elif role == UserRole.STUDENT:
            print("  - Chat with AI assistant")
            print("  - Upload task images")
            print("  - Get help with assignments")
            print("  - Practice and test modes")
        
    except Exception as e:
        print(f"Error creating user: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def list_users():
    """List all users with their profiles"""
    db = SessionLocal()
    
    try:
        users = db.query(User).all()
        
        if not users:
            print("No users found in the database.")
            return
            
        print("\n=== Current Users ===")
        print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Role':<10} {'Full Name':<25} {'Active':<8}")
        print("-" * 100)
        
        for user in users:
            full_name = "N/A"
            
            # Get full name from profile
            if user.role == UserRole.TEACHER and hasattr(user, 'teacher_profile') and user.teacher_profile:
                full_name = user.teacher_profile.full_name
            elif user.role == UserRole.STUDENT and hasattr(user, 'student_profile') and user.student_profile:
                full_name = user.student_profile.full_name
            
            print(f"{user.id:<5} {user.username:<20} {user.email:<30} {user.role.value:<10} {full_name:<25} {'Yes' if user.is_active else 'No':<8}")
        
        print(f"\nTotal users: {len(users)}")
        
        # Count by role
        admin_count = sum(1 for u in users if u.role == UserRole.ADMIN)
        teacher_count = sum(1 for u in users if u.role == UserRole.TEACHER)
        student_count = sum(1 for u in users if u.role == UserRole.STUDENT)
        
        print(f"Admins: {admin_count}, Teachers: {teacher_count}, Students: {student_count}")
        
    finally:
        db.close()

def create_sample_users():
    """Create sample users for testing"""
    db = SessionLocal()
    
    try:
        print("=== Creating Sample Users ===")
        
        # Sample teacher
        teacher_user = User(
            username="teacher_sample",
            email="teacher@learnobot.com",
            hashed_password=get_password_hash("123456"),
            role=UserRole.TEACHER,
            is_active=True
        )
        db.add(teacher_user)
        db.flush()
        
        teacher_profile = TeacherProfile(
            user_id=teacher_user.id,
            full_name="Sarah Cohen",
            school="Beit Sefer Yesodi",
            subject="Mathematics"
        )
        db.add(teacher_profile)
        
        # Sample students
        students_data = [
            ("student1", "student1@learnobot.com", "David Levi", "Grade 4", 3, "Needs help with reading comprehension"),
            ("student2", "student2@learnobot.com", "Maya Goldberg", "Grade 5", 4, "Excellent student, seeks challenges"),
            ("student3", "student3@learnobot.com", "Ron Shapiro", "Grade 3", 2, "Struggles with complex instructions"),
        ]
        
        for username, email, full_name, grade, difficulty, description in students_data:
            student_user = User(
                username=username,
                email=email,
                hashed_password=get_password_hash("123456"),
                role=UserRole.STUDENT,
                is_active=True
            )
            db.add(student_user)
            db.flush()
            
            student_profile = StudentProfile(
                user_id=student_user.id,
                full_name=full_name,
                grade=grade,
                school="Beit Sefer Yesodi",
                difficulty_level=difficulty,
                description=description
            )
            db.add(student_profile)
        
        db.commit()
        
        print("✅ Sample users created successfully!")
        print("\nCreated accounts:")
        print("👨‍🏫 Teacher: teacher@learnobot.com / 123456")
        print("👨‍🎓 Student1: student1@learnobot.com / 123456")
        print("👨‍🎓 Student2: student2@learnobot.com / 123456") 
        print("👨‍🎓 Student3: student3@learnobot.com / 123456")
        
    except Exception as e:
        print(f"Error creating sample users: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--list":
            list_users()
        elif sys.argv[1] == "--sample":
            create_sample_users()
        else:
            print("Usage: python create_users.py [--list|--sample]")
    else:
        create_user()
