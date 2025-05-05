# backend/app/db/models/account.py
from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from ..base import BaseModel

class AccountType(enum.Enum):
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT = "credit"
    INVESTMENT = "investment"

class Account(BaseModel):
    """Account model for different types of bank accounts"""
    __tablename__ = "accounts"
    
    account_number = Column(String(20), unique=True, index=True, nullable=False)
    account_type = Column(Enum(AccountType), nullable=False)
    balance = Column(Float, default=0.0, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)  # ISO 4217 currency code
    is_active = Column(Boolean, default=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Account {self.account_number}>"