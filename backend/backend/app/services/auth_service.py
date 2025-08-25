from typing import Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timedelta

from app.models.user import User, UserRole
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_refresh_token
)
from app.schemas.user import UserCreate, UserLogin, Token
from app.config import settings


class AuthService:
    """Service for authentication and user management."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def register_user(self, user_data: UserCreate) -> User:
        """Register a new user."""
        
        # Check if user already exists
        existing_user = self.db.query(User).filter(
            (User.email == user_data.email) | (User.username == user_data.username)
        ).first()
        
        if existing_user:
            if existing_user.email == user_data.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            role=user_data.role,
            language_preference=user_data.language_preference,
            timezone=user_data.timezone
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        return db_user
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user by username/email and password."""
        
        user = self.db.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user or not verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user account"
            )
        
        return user
    
    def login_user(self, username: str, password: str) -> Tuple[Token, User]:
        """Login a user and return tokens."""
        
        user = self.authenticate_user(username, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        # Create tokens
        access_token = create_access_token(
            subject=user.id,
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
        )
        refresh_token = create_refresh_token(subject=user.id)
        
        # Update last login
        user.last_login = datetime.utcnow()
        self.db.commit()
        
        token = Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60
        )
        
        return token, user
    
    def refresh_user_token(self, refresh_token: str) -> Token:
        """Refresh access token using refresh token."""
        
        user_id = verify_refresh_token(refresh_token)
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Create new tokens
        access_token = create_access_token(
            subject=user.id,
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
        )
        new_refresh_token = create_refresh_token(subject=user.id)
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60
        )
    
    def change_password(self, user: User, current_password: str, new_password: str) -> bool:
        """Change user's password."""
        
        if not verify_password(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password"
            )
        
        user.hashed_password = get_password_hash(new_password)
        self.db.commit()
        
        return True
    
    def deactivate_user(self, user: User) -> bool:
        """Deactivate user account."""
        
        user.is_active = False
        self.db.commit()
        
        return True
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        
        return self.db.query(User).filter(User.email == email).first()
    
    def update_user_profile(self, user: User, **kwargs) -> User:
        """Update user profile."""
        
        for key, value in kwargs.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def verify_user_email(self, user: User) -> bool:
        """Mark user email as verified."""
        
        user.is_verified = True
        self.db.commit()
        
        return True
    
    def get_users_by_role(self, role: UserRole, skip: int = 0, limit: int = 100) -> list[User]:
        """Get users by role."""
        
        return self.db.query(User).filter(
            User.role == role,
            User.is_active == True
        ).offset(skip).limit(limit).all()
    
    def search_users(self, query: str, skip: int = 0, limit: int = 100) -> list[User]:
        """Search users by name, username, or email."""
        
        search_pattern = f"%{query}%"
        return self.db.query(User).filter(
            (User.full_name.ilike(search_pattern)) |
            (User.username.ilike(search_pattern)) |
            (User.email.ilike(search_pattern))
        ).filter(User.is_active == True).offset(skip).limit(limit).all()
