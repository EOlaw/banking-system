# backend/app/schemas/auth.py
from typing import Optional
from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    """Schema for token response."""
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    """Schema for token payload."""
    sub: Optional[int] = None

class Login(BaseModel):
    """Schema for login request."""
    email: EmailStr
    password: str

class PasswordChange(BaseModel):
    """Schema for password change request."""
    current_password: str
    new_password: str