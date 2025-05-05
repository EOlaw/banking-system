# backend/app/schemas/transaction.py
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator

from app.db.models.transaction import TransactionType, TransactionStatus

class TransactionBase(BaseModel):
    """Base transaction schema with common attributes."""
    transaction_type: TransactionType
    amount: float = Field(..., gt=0.0)
    currency: str = Field("USD", min_length=3, max_length=3)
    description: Optional[str] = None
    
    @validator('currency')
    def currency_code_format(cls, v):
        if not v.isalpha() or len(v) != 3:
            raise ValueError('Currency code must be a 3-letter ISO 4217 code (e.g., USD, EUR)')
        return v.upper()

class TransactionCreate(TransactionBase):
    """Schema for creating a new transaction."""
    account_id: int
    recipient_account_id: Optional[int] = None
    status: TransactionStatus = TransactionStatus.PENDING

class TransactionUpdate(BaseModel):
    """Schema for updating an existing transaction."""
    description: Optional[str] = None
    status: Optional[TransactionStatus] = None

class TransactionInDBBase(TransactionBase):
    """Base schema for transaction in database, including ID and timestamps."""
    id: int
    account_id: int
    recipient_account_id: Optional[int] = None
    reference_id: str
    status: TransactionStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class Transaction(TransactionInDBBase):
    """Schema for transaction response."""
    pass

class TransactionWithAccount(Transaction):
    """Schema for transaction with account information."""
    account: Account

class TransactionList(BaseModel):
    """Schema for list of transactions."""
    items: List[Transaction]
    total: int

# Additional schemas for specific transaction operations
class DepositCreate(BaseModel):
    """Schema for creating a deposit transaction."""
    account_id: int
    amount: float = Field(..., gt=0.0)
    currency: str = Field("USD", min_length=3, max_length=3)
    description: Optional[str] = None
    
    @validator('currency')
    def currency_code_format(cls, v):
        if not v.isalpha() or len(v) != 3:
            raise ValueError('Currency code must be a 3-letter ISO 4217 code (e.g., USD, EUR)')
        return v.upper()

class WithdrawalCreate(BaseModel):
    """Schema for creating a withdrawal transaction."""
    account_id: int
    amount: float = Field(..., gt=0.0)
    currency: str = Field("USD", min_length=3, max_length=3)
    description: Optional[str] = None
    
    @validator('currency')
    def currency_code_format(cls, v):
        if not v.isalpha() or len(v) != 3:
            raise ValueError('Currency code must be a 3-letter ISO 4217 code (e.g., USD, EUR)')
        return v.upper()

class TransferCreate(BaseModel):
    """Schema for creating a transfer transaction."""
    source_account_id: int
    destination_account_id: int
    amount: float = Field(..., gt=0.0)
    currency: str = Field("USD", min_length=3, max_length=3)
    description: Optional[str] = None
    
    @validator('currency')
    def currency_code_format(cls, v):
        if not v.isalpha() or len(v) != 3:
            raise ValueError('Currency code must be a 3-letter ISO 4217 code (e.g., USD, EUR)')
        return v.upper()
    
    @validator('destination_account_id')
    def accounts_cannot_be_same(cls, v, values):
        if 'source_account_id' in values and v == values['source_account_id']:
            raise ValueError('Source and destination accounts cannot be the same')
        return v

class PaymentCreate(BaseModel):
    """Schema for creating a payment transaction."""
    account_id: int
    amount: float = Field(..., gt=0.0)
    currency: str = Field("USD", min_length=3, max_length=3)
    recipient: str = Field(..., min_length=1)
    description: Optional[str] = None
    
    @validator('currency')
    def currency_code_format(cls, v):
        if not v.isalpha() or len(v) != 3:
            raise ValueError('Currency code must be a 3-letter ISO 4217 code (e.g., USD, EUR)')
        return v.upper()