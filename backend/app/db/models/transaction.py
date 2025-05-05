# backend/app/db/models/transaction.py
from sqlalchemy import Column, String, Integer, Float, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from ..base import BaseModel

class TransactionType(enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    PAYMENT = "payment"
    FEE = "fee"
    INTEREST = "interest"

class TransactionStatus(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Transaction(BaseModel):
    """Transaction model for tracking money movements"""
    __tablename__ = "transactions"
    
    transaction_type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)  # ISO 4217 currency code
    description = Column(Text)
    reference_id = Column(String(50), unique=True, index=True)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False)
    
    # For transfers
    recipient_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    
    # Foreign keys
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    
    # Relationships
    account = relationship("Account", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction {self.reference_id}>"