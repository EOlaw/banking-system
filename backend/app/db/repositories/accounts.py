# backend/app/db/repositories/accounts.py
from typing import List, Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.db.models.account import Account, AccountType
from app.schemas.account import AccountCreate, AccountUpdate
from .base import BaseRepository


class AccountRepository(BaseRepository[Account, AccountCreate, AccountUpdate]):
    """Repository for Account model operations."""

    def __init__(self):
        super().__init__(Account)
    
    def get_by_account_number(self, db: Session, *, account_number: str) -> Optional[Account]:
        """
        Get an account by account number.
        
        Args:
            db: Database session
            account_number: Account number
            
        Returns:
            Account if found, None otherwise
        """
        return db.query(Account).filter(Account.account_number == account_number).first()
    
    def get_user_accounts(
        self, 
        db: Session, 
        *, 
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        account_type: AccountType = None,
        is_active: bool = None,
    ) -> List[Account]:
        """
        Get accounts for a specific user with optional filtering.
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of accounts to skip
            limit: Maximum number of accounts to return
            account_type: Filter by account type
            is_active: Filter by active status
            
        Returns:
            List of accounts
        """
        query = db.query(Account).filter(Account.user_id == user_id)
        
        if account_type:
            query = query.filter(Account.account_type == account_type)
            
        if is_active is not None:
            query = query.filter(Account.is_active == is_active)
            
        return query.offset(skip).limit(limit).all()
    
    def get_user_total_balance(self, db: Session, *, user_id: int, currency: str = "USD") -> float:
        """
        Get total balance for a user in a specific currency.
        
        Args:
            db: Database session
            user_id: User ID
            currency: Currency code
            
        Returns:
            Total balance
        """
        result = db.query(func.sum(Account.balance).label("total"))\
            .filter(Account.user_id == user_id, Account.currency == currency)\
            .scalar()
        return result or 0.0
    
    def generate_account_number(self, db: Session) -> str:
        """
        Generate a unique account number.
        
        Args:
            db: Database session
            
        Returns:
            Unique account number
        """
        import random
        import string
        from datetime import datetime
        
        # Generate a random account number
        timestamp = datetime.now().strftime("%Y%m%d")
        random_part = ''.join(random.choices(string.digits, k=10))
        account_number = f"{timestamp}{random_part}"
        
        # Check if the account number already exists
        while self.get_by_account_number(db, account_number=account_number):
            random_part = ''.join(random.choices(string.digits, k=10))
            account_number = f"{timestamp}{random_part}"
            
        return account_number

    def create_with_owner(
        self, 
        db: Session, 
        *, 
        obj_in: AccountCreate, 
        user_id: int,
        account_number: str = None,
    ) -> Account:
        """
        Create a new account with owner.
        
        Args:
            db: Database session
            obj_in: Input data
            user_id: User ID
            account_number: Optional account number
            
        Returns:
            Created account
        """
        if not account_number:
            account_number = self.generate_account_number(db)
            
        create_data = obj_in.dict()
        db_obj = Account(
            **create_data,
            account_number=account_number,
            user_id=user_id,
        )
        db.add(db_obj)
        db.flush()
        return db_obj
    
    def get_inactive_accounts(self, db: Session, *, days_inactive: int = 180) -> List[Account]:
        """
        Get accounts that haven't had any activity for a specified number of days.
        
        Args:
            db: Database session
            days_inactive: Number of days of inactivity
            
        Returns:
            List of inactive accounts
        """
        from sqlalchemy import text
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_inactive)
        
        # This uses a subquery to find accounts with no transactions after the cutoff date
        query = text("""
            SELECT a.* FROM accounts a
            LEFT JOIN (
                SELECT account_id, MAX(created_at) as last_activity
                FROM transactions
                GROUP BY account_id
            ) t ON a.id = t.account_id
            WHERE t.last_activity IS NULL OR t.last_activity < :cutoff_date
            AND a.is_active = TRUE
        """)
        
        result = db.execute(query, {"cutoff_date": cutoff_date})
        return [Account(**dict(row)) for row in result]