# backend/app/db/repositories/base.py
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import Base

# Define a type variable for SQLAlchemy models
ModelType = TypeVar("ModelType", bound=Base)
# Define a type variable for Pydantic schemas
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base class for all repositories providing common CRUD operations
    """
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """
        Get a record by ID
        """
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        Get multiple records with pagination
        """
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record
        """
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Update a record
        """
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> ModelType:
        """
        Delete a record
        """
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj


# backend/app/db/repositories/users.py
from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.models.user import User
from app.db.repositories.base import BaseRepository
from app.core.security import get_password_hash, verify_password

class UserRepository(BaseRepository[User, None, None]):
    def __init__(self):
        super().__init__(User)
    
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """
        Get a user by email
        """
        return db.query(User).filter(User.email == email).first()
    
    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        """
        Get a user by username
        """
        return db.query(User).filter(User.username == username).first()
    
    def create_user(
        self, db: Session, *, email: str, username: str, password: str, 
        first_name: Optional[str] = None, last_name: Optional[str] = None, 
        is_superuser: bool = False
    ) -> User:
        """
        Create a new user
        """
        user = User(
            email=email,
            username=username,
            password=password,  # Password will be hashed in the User __init__ method
            first_name=first_name,
            last_name=last_name,
            is_superuser=is_superuser
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    def authenticate(self, db: Session, *, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user with username and password
        """
        user = self.get_by_username(db, username=username)
        if not user:
            return None
        if not user.check_password(password):
            return None
        return user
    
    def is_active(self, user: User) -> bool:
        """
        Check if a user is active
        """
        return user.is_active
    
    def is_superuser(self, user: User) -> bool:
        """
        Check if a user is a superuser
        """
        return user.is_superuser


# backend/app/db/repositories/accounts.py
from typing import List, Optional
from sqlalchemy.orm import Session

from app.db.models.account import Account, AccountType
from app.db.repositories.base import BaseRepository

class AccountRepository(BaseRepository[Account, None, None]):
    def __init__(self):
        super().__init__(Account)
    
    def get_by_account_number(self, db: Session, *, account_number: str) -> Optional[Account]:
        """
        Get an account by account number
        """
        return db.query(Account).filter(Account.account_number == account_number).first()
    
    def get_by_owner(self, db: Session, *, owner_id: int) -> List[Account]:
        """
        Get all accounts for a user
        """
        return db.query(Account).filter(Account.owner_id == owner_id).all()
    
    def create_account(
        self, db: Session, *, owner_id: int, account_type: AccountType, 
        currency: str = "USD", initial_balance: float = 0.0
    ) -> Account:
        """
        Create a new account
        """
        account = Account(
            owner_id=owner_id,
            account_type=account_type,
            currency=currency,
            initial_balance=initial_balance
        )
        db.add(account)
        db.commit()
        db.refresh(account)
        return account
    
    def deposit(self, db: Session, *, account_id: int, amount: float) -> Account:
        """
        Deposit money into an account
        """
        account = self.get(db, id=account_id)
        if not account:
            raise ValueError("Account not found")
        account.deposit(amount)
        db.add(account)
        db.commit()
        db.refresh(account)
        return account
    
    def withdraw(self, db: Session, *, account_id: int, amount: float) -> Account:
        """
        Withdraw money from an account
        """
        account = self.get(db, id=account_id)
        if not account:
            raise ValueError("Account not found")
        account.withdraw(amount)
        db.add(account)
        db.commit()
        db.refresh(account)
        return account


# backend/app/db/repositories/transactions.py
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.models.transaction import Transaction, TransactionType, TransactionStatus
from app.db.repositories.base import BaseRepository
from app.db.repositories.accounts import AccountRepository

class TransactionRepository(BaseRepository[Transaction, None, None]):
    def __init__(self):
        super().__init__(Transaction)
        self.account_repository = AccountRepository()
    
    def get_by_transaction_number(self, db: Session, *, transaction_number: str) -> Optional[Transaction]:
        """
        Get a transaction by transaction number
        """
        return db.query(Transaction).filter(Transaction.transaction_number == transaction_number).first()
    
    def get_by_account(self, db: Session, *, account_id: int) -> List[Transaction]:
        """
        Get all transactions for an account
        """
        return db.query(Transaction).filter(
            (Transaction.source_account_id == account_id) | 
            (Transaction.destination_account_id == account_id)
        ).all()
    
    def get_by_user(self, db: Session, *, user_id: int) -> List[Transaction]:
        """
        Get all transactions for a user
        """
        return db.query(Transaction).filter(
            (Transaction.sender_id == user_id) | 
            (Transaction.receiver_id == user_id)
        ).all()
    
    def create_deposit(
        self, db: Session, *, account_id: int, amount: float, 
        user_id: int, description: Optional[str] = None
    ) -> Transaction:
        """
        Create a deposit transaction
        """
        # Create the transaction
        transaction = Transaction(
            transaction_type=TransactionType.DEPOSIT,
            amount=amount,
            destination_account_id=account_id,
            receiver_id=user_id,
            description=description
        )
        db.add(transaction)
        
        # Update the account balance
        self.account_repository.deposit(db, account_id=account_id, amount=amount)
        
        # Complete the transaction
        transaction.complete()
        transaction.completed_at = datetime.utcnow()
        
        # Commit and refresh
        db.commit()
        db.refresh(transaction)
        return transaction
    
    def create_withdrawal(
        self, db: Session, *, account_id: int, amount: float, 
        user_id: int, description: Optional[str] = None
    ) -> Transaction:
        """
        Create a withdrawal transaction
        """
        # Create the transaction
        transaction = Transaction(
            transaction_type=TransactionType.WITHDRAWAL,
            amount=amount,
            source_account_id=account_id,
            sender_id=user_id,
            description=description
        )
        db.add(transaction)
        
        try:
            # Update the account balance
            self.account_repository.withdraw(db, account_id=account_id, amount=amount)
            
            # Complete the transaction
            transaction.complete()
            transaction.completed_at = datetime.utcnow()
            
        except ValueError as e:
            # If withdrawal fails (e.g., insufficient funds)
            transaction.fail()
            db.commit()
            raise e
        
        # Commit and refresh
        db.commit()
        db.refresh(transaction)
        return transaction
    
    def create_transfer(
        self, db: Session, *, source_account_id: int, destination_account_id: int,
        amount: float, sender_id: int, receiver_id: int, description: Optional[str] = None
    ) -> Transaction:
        """
        Create a transfer transaction between accounts
        """
        # Create the transaction
        transaction = Transaction(
            transaction_type=TransactionType.TRANSFER,
            amount=amount,
            source_account_id=source_account_id,
            destination_account_id=destination_account_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            description=description
        )
        db.add(transaction)
        
        try:
            # Withdraw from source account
            self.account_repository.withdraw(db, account_id=source_account_id, amount=amount)
            
            # Deposit to destination account
            self.account_repository.deposit(db, account_id=destination_account_id, amount=amount)
            
            # Complete the transaction
            transaction.complete()
            transaction.completed_at = datetime.utcnow()
            
        except ValueError as e:
            # If transfer fails (e.g., insufficient funds)
            transaction.fail()
            db.commit()
            raise e
        
        # Commit and refresh
        db.commit()
        db.refresh(transaction)
        return transaction


# backend/app/db/repositories/__init__.py
from app.db.repositories.users import UserRepository
from app.db.repositories.accounts import AccountRepository
from app.db.repositories.transactions import TransactionRepository

__all__ = ["UserRepository", "AccountRepository", "TransactionRepository"]