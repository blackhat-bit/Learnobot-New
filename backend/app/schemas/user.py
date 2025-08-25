from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, validator
from enum import Enum


class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


# User creation schemas
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    password: str
    role: UserRole = UserRole.STUDENT
    language_preference: str = "en"
    timezone: str = "UTC"

    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if len(v) > 50:
            raise ValueError('Username must be no more than 50 characters long')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    language_preference: Optional[str] = None
    timezone: Optional[str] = None


class UserPasswordUpdate(BaseModel):
    current_password: str
    new_password: str

    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


# User response schemas
class UserBase(BaseModel):
    id: int
    email: EmailStr
    username: str
    full_name: str
    role: UserRole
    is_active: bool
    is_verified: bool

    class Config:
        from_attributes = True


class UserProfile(UserBase):
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    language_preference: str
    timezone: str
    created_at: datetime
    last_login: Optional[datetime] = None


class UserPublic(BaseModel):
    id: int
    username: str
    full_name: str
    role: UserRole
    avatar_url: Optional[str] = None
    bio: Optional[str] = None

    class Config:
        from_attributes = True


# Authentication schemas
class UserLogin(BaseModel):
    username: str  # Can be username or email
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefresh(BaseModel):
    refresh_token: str


class UserRegistration(UserCreate):
    confirm_password: str

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
