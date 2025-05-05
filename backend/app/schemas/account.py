# backend/app/schemas/account.py
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator

from app.db.models.account import AccountType

class AccountBase(BaseModel):
    """Base account schema with common attributes."""
    account_type: AccountType
    currency: str = Field("USD", min_length=3, max_length=3)
    
    @validator('currency')
    def currency_code_format(cls, v):
        if not v.isalpha() or len(v) != 3:
            raise ValueError('Currency code must be a 3-letter ISO 4217 code (e.g., USD, EUR)')
        return v.upper()

class AccountCreate(AccountBase):
    """Schema for creating a new account."""
    balance: float = Field(0.0, ge=0.0)

class AccountUpdate(BaseModel):
    """Schema for updating an existing account."""
    account_type: Optional[AccountType] = None
    currency: Optional[str] = None
    is_active: Optional[bool] = None
    
    @validator('currency')
    def currency_code_format(cls, v):
        if v is not None:
            if not v.isalpha() or len(v) != 3:
                raise ValueError('Currency code must be a 3-letter ISO 4217 code (e.g., USD, EUR)')
            return v.upper()
        return v

class AccountInDBBase(AccountBase):
    """Base schema for account in database, including ID and timestamps."""
    id: int
    user_id: int
    account_number: str
    balance: float
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class Account(AccountInDBBase):
    """Schema for account response."""
    pass

class AccountWithOwner(Account):
    """Schema for account with owner information."""
    owner: User

class AccountList(BaseModel):
    """Schema for list of accounts."""
    items: List[Account]
    total: int