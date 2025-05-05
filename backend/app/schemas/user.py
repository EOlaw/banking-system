# backend/app/schemas/user.py
from typing import Optional
from datetime import date
from pydantic import BaseModel, EmailStr, Field, validator
import re

class UserBase(BaseModel):
    """Base user schema with common attributes."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[str] = None  # Format: YYYY-MM-DD
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username must contain only alphanumeric characters, underscores, and hyphens')
        return v
    
    @validator('date_of_birth')
    def valid_date_format(cls, v):
        if v is not None:
            try:
                year, month, day = map(int, v.split('-'))
                date(year, month, day)
            except (ValueError, TypeError):
                raise ValueError('Date of birth must be in format YYYY-MM-DD')
        return v
    
    @validator('phone_number')
    def valid_phone_number(cls, v):
        if v is not None and not re.match(r'^\+?[0-9\- ]+$', v):
            raise ValueError('Invalid phone number format')
        return v

class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserUpdate(BaseModel):
    """Schema for updating an existing user."""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[str] = None  # Format: YYYY-MM-DD
    password: Optional[str] = None
    is_active: Optional[bool] = None
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if v is not None and not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username must contain only alphanumeric characters, underscores, and hyphens')
        return v
    
    @validator('date_of_birth')
    def valid_date_format(cls, v):
        if v is not None:
            try:
                year, month, day = map(int, v.split('-'))
                date(year, month, day)
            except (ValueError, TypeError):
                raise ValueError('Date of birth must be in format YYYY-MM-DD')
        return v
    
    @validator('phone_number')
    def valid_phone_number(cls, v):
        if v is not None and not re.match(r'^\+?[0-9\- ]+$', v):
            raise ValueError('Invalid phone number format')
        return v
    
    @validator('password')
    def password_strength(cls, v):
        if v is not None:
            if len(v) < 8:
                raise ValueError('Password must be at least 8 characters long')
            if not any(c.isupper() for c in v):
                raise ValueError('Password must contain at least one uppercase letter')
            if not any(c.islower() for c in v):
                raise ValueError('Password must contain at least one lowercase letter')
            if not any(c.isdigit() for c in v):
                raise ValueError('Password must contain at least one digit')
        return v

class UserInDBBase(UserBase):
    """Base schema for user in database, including ID and timestamps."""
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class User(UserInDBBase):
    """Schema for user response."""
    pass

class UserInDB(UserInDBBase):
    """Schema for user in database, including hashed password."""
    hashed_password: str