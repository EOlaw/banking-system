# backend/app/services/accounts.py
from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.repositories import account_repository, audit_repository
from app.db.models.audit import AuditAction
from app.db.models.account import Account, AccountType
from app.schemas.account import AccountCreate, AccountUpdate

class AccountService:
    """Account management service."""
    
    @staticmethod
    async def get(db: Session, *, account_id: int) -> Optional[Account]:
        """
        Get an account by ID.
        
        Args:
            db: Database session
            account_id: Account ID
            
        Returns:
            Account if found, None otherwise
        """
        return account_repository.get(db, id=account_id)
    
    @staticmethod
    async def get_by_account_number(db: Session, *, account_number: str) -> Optional[Account]:
        """
        Get an account by account number.
        
        Args:
            db: Database session
            account_number: Account number
            
        Returns:
            Account if found, None otherwise
        """
        return account_repository.get_by_account_number(db, account_number=account_number)
    
    @staticmethod
    async def get_user_accounts(
        db: Session, 
        *, 
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        account_type: AccountType = None,
        is_active: bool = None,
    ) -> List[Account]:
        """
        Get accounts for a specific user.
        
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
        return account_repository.get_user_accounts(
            db,
            user_id=user_id,
            skip=skip,
            limit=limit,
            account_type=account_type,
            is_active=is_active,
        )
    
    @staticmethod
    async def create(
        db: Session, 
        *, 
        obj_in: AccountCreate, 
        user_id: int,
        current_user_id: int,
        ip_address: str = None,
    ) -> Account:
        """
        Create a new account.
        
        Args:
            db: Database session
            obj_in: Input data
            user_id: User ID (owner)
            current_user_id: ID of the user performing the action (for audit)
            ip_address: Client IP address for audit logging
            
        Returns:
            Created account
        """
        # Generate account number
        account_number = account_repository.generate_account_number(db)
        
        # Create the account
        account = account_repository.create_with_owner(
            db,
            obj_in=obj_in,
            user_id=user_id,
            account_number=account_number,
        )
        
        # Audit account creation
        audit_repository.log_action(
            db,
            action=AuditAction.CREATE,
            entity_type="account",
            entity_id=account.id,
            user_id=current_user_id,
            data={
                "account_number": account.account_number,
                "account_type": account.account_type.value,
                "owner_id": user_id,
            },
            ip_address=ip_address,
        )
        
        return account
    
    @staticmethod
    async def update(
        db: Session, 
        *, 
        account_id: int, 
        obj_in: AccountUpdate,
        current_user_id: int,
        ip_address: str = None,
    ) -> Optional[Account]:
        """
        Update an account.
        
        Args:
            db: Database session
            account_id: Account ID
            obj_in: Update data
            current_user_id: ID of the user performing the action (for audit)
            ip_address: Client IP address for audit logging
            
        Returns:
            Updated account if found, None otherwise
        """
        account = account_repository.get(db, id=account_id)
        if not account:
            return None
        
        # Update the account
        update_data = obj_in.dict(exclude_unset=True)
        account = account_repository.update(db, db_obj=account, obj_in=update_data)
        
        # Audit account update
        audit_repository.log_action(
            db,
            action=AuditAction.UPDATE,
            entity_type="account",
            entity_id=account.id,
            user_id=current_user_id,
            data=update_data,
            ip_address=ip_address,
        )
        
        return account
    
    @staticmethod
    async def delete(
        db: Session, 
        *, 
        account_id: int,
        current_user_id: int,
        ip_address: str = None,
    ) -> Optional[Account]:
        """
        Delete an account.
        
        Args:
            db: Database session
            account_id: Account ID
            current_user_id: ID of the user performing the action (for audit)
            ip_address: Client IP address for audit logging
            
        Returns:
            Deleted account if found, None otherwise
        """
        account = account_repository.get(db, id=account_id)
        if not account:
            return None
        
        # Delete the account
        account = account_repository.delete(db, id=account_id)
        
        # Audit account deletion
        audit_repository.log_action(
            db,
            action=AuditAction.DELETE,
            entity_type="account",
            entity_id=account_id,
            user_id=current_user_id,
            data={
                "account_number": account.account_number,
                "account_type": account.account_type.value,
                "owner_id": account.user_id,
            },
            ip_address=ip_address,
        )
        
        return account
    
    @staticmethod
    async def deactivate(
        db: Session, 
        *, 
        account_id: int,
        current_user_id: int,
        ip_address: str = None,
    ) -> Optional[Account]:
        """
        Deactivate an account.
        
        Args:
            db: Database session
            account_id: Account ID
            current_user_id: ID of the user performing the action (for audit)
            ip_address: Client IP address for audit logging
            
        Returns:
            Updated account if found, None otherwise
        """
        account = account_repository.get(db, id=account_id)
        if not account:
            return None
        
        # Deactivate the account
        account = account_repository.update(
            db, 
            db_obj=account, 
            obj_in={"is_active": False},
        )
        
        # Audit account deactivation
        audit_repository.log_action(
            db,
            action=AuditAction.UPDATE,
            entity_type="account",
            entity_id=account.id,
            user_id=current_user_id,
            data={"is_active": False},
            ip_address=ip_address,
        )
        
        return account
    
    @staticmethod
    async def reactivate(
        db: Session, 
        *, 
        account_id: int,
        current_user_id: int,
        ip_address: str = None,
    ) -> Optional[Account]:
        """
        Reactivate an account.
        
        Args:
            db: Database session
            account_id: Account ID
            current_user_id: ID of the user performing the action (for audit)
            ip_address: Client IP address for audit logging
            
        Returns:
            Updated account if found, None otherwise
        """
        account = account_repository.get(db, id=account_id)
        if not account:
            return None
        
        # Reactivate the account
        account = account_repository.update(
            db, 
            db_obj=account, 
            obj_in={"is_active": True},
        )
        
        # Audit account reactivation
        audit_repository.log_action(
            db,
            action=AuditAction.UPDATE,
            entity_type="account",
            entity_id=account.id,
            user_id=current_user_id,
            data={"is_active": True},
            ip_address=ip_address,
        )
        
        return account
    
    @staticmethod
    async def update_balance(
        db: Session, 
        *, 
        account_id: int, 
        amount: float,
        description: str,
        current_user_id: int,
        ip_address: str = None,
    ) -> Optional[Account]:
        """
        Update an account balance.
        
        Args:
            db: Database session
            account_id: Account ID
            amount: Amount to add (positive) or subtract (negative)
            description: Description of the balance update
            current_user_id: ID of the user performing the action (for audit)
            ip_address: Client IP address for audit logging
            
        Returns:
            Updated account if found, None otherwise
            
        Raises:
            ValueError: If resulting balance would be negative
        """
        account = account_repository.get(db, id=account_id)
        if not account:
            return None
        
        # Calculate new balance
        new_balance = account.balance + amount
        
        # Check if balance would be negative
        if new_balance < 0:
            raise ValueError("Insufficient funds")
        
        # Update the balance
        account = account_repository.update(
            db, 
            db_obj=account, 
            obj_in={"balance": new_balance},
        )
        
        # Audit balance update
        audit_repository.log_action(
            db,
            action=AuditAction.UPDATE,
            entity_type="account",
            entity_id=account.id,
            user_id=current_user_id,
            data={
                "previous_balance": account.balance - amount,
                "new_balance": account.balance,
                "amount": amount,
                "description": description,
            },
            ip_address=ip_address,
        )
        
        return account