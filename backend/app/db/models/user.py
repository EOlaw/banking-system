# backend/app/db/models/user.py
from sqlalchemy import Boolean, Column, String, Text
from sqlalchemy.orm import relationship

from ..base import BaseModel

class User(BaseModel):
    """User model for authentication and profile information"""
    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    phone_number = Column(String(20))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Profile information
    address = Column(Text)
    date_of_birth = Column(String(10))  # Format: YYYY-MM-DD
    
    # Relationships
    accounts = relationship("Account", back_populates="owner", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.username}>"