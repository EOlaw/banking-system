# backend/app/db/models/user.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime

from app.db.session import Base
from app.core.security import get_password_hash

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    accounts = relationship("Account", back_populates="owner")
    sent_transactions = relationship("Transaction", foreign_keys="Transaction.sender_id", back_populates="sender")
    received_transactions = relationship("Transaction", foreign_keys="Transaction.receiver_id", back_populates="receiver")
    
    def __init__(self, email, username, password, first_name=None, last_name=None, is_superuser=False):
        self.email = email
        self.username = username
        self.hashed_password = get_password_hash(password)
        self.first_name = first_name
        self.last_name = last_name
        self.is_superuser = is_superuser
    
    def check_password(self, password):
        from app.core.security import verify_password
        return verify_password(password, self.hashed_password)
    
    def __repr__(self):
        return f"<User {self.username}>"


# backend/app/db/models/account.py
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid

from app.db.session import Base

class AccountType(enum.Enum):
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT = "credit"
    INVESTMENT = "investment"

class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    account_number = Column(String, unique=True, index=True, nullable=False)
    account_type = Column(Enum(AccountType), nullable=False)
    balance = Column(Float, default=0.0)
    currency = Column(String, default="USD")
    is_active = Column(Boolean, default=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="accounts")
    outgoing_transactions = relationship("Transaction", foreign_keys="Transaction.source_account_id", back_populates="source_account")
    incoming_transactions = relationship("Transaction", foreign_keys="Transaction.destination_account_id", back_populates="destination_account")
    
    def __init__(self, owner_id, account_type, currency="USD", initial_balance=0.0):
        self.owner_id = owner_id
        self.account_type = account_type
        self.currency = currency
        self.balance = initial_balance
        self.account_number = self._generate_account_number()
        
    def _generate_account_number(self):
        # Generate a unique account number
        # In a real system, this would follow specific banking rules
        return f"ACC-{uuid.uuid4().hex[:8].upper()}"
    
    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        self.balance += amount
        return self.balance
    
    def withdraw(self, amount):
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        self.balance -= amount
        return self.balance
    
    def __repr__(self):
        return f"<Account {self.account_number}: {self.balance} {self.currency}>"


# backend/app/db/models/transaction.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid

from app.db.session import Base

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
    REVERSED = "reversed"

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_number = Column(String, unique=True, index=True, nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING)
    description = Column(String)
    
    # Account relationships
    source_account_id = Column(Integer, ForeignKey("accounts.id"))
    destination_account_id = Column(Integer, ForeignKey("accounts.id"))
    source_account = relationship("Account", foreign_keys=[source_account_id], back_populates="outgoing_transactions")
    destination_account = relationship("Account", foreign_keys=[destination_account_id], back_populates="incoming_transactions")
    
    # User relationships
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_transactions")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_transactions")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    def __init__(self, transaction_type, amount, source_account_id=None, destination_account_id=None, 
                 sender_id=None, receiver_id=None, currency="USD", description=None):
        self.transaction_type = transaction_type
        self.amount = amount
        self.source_account_id = source_account_id
        self.destination_account_id = destination_account_id
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.currency = currency
        self.description = description
        self.transaction_number = self._generate_transaction_number()
        
    def _generate_transaction_number(self):
        # Generate a unique transaction number
        return f"TXN-{uuid.uuid4().hex[:10].upper()}"
    
    def complete(self):
        self.status = TransactionStatus.COMPLETED
        self.completed_at = func.now()
    
    def fail(self):
        self.status = TransactionStatus.FAILED
    
    def reverse(self):
        if self.status != TransactionStatus.COMPLETED:
            raise ValueError("Only completed transactions can be reversed")
        self.status = TransactionStatus.REVERSED
    
    def __repr__(self):
        return f"<Transaction {self.transaction_number}: {self.amount} {self.currency} ({self.status.value})>"


# backend/app/db/models/__init__.py
from app.db.models.user import User
from app.db.models.account import Account, AccountType
from app.db.models.transaction import Transaction, TransactionType, TransactionStatus

__all__ = [
    "User", 
    "Account", 
    "AccountType", 
    "Transaction", 
    "TransactionType", 
    "TransactionStatus"
]