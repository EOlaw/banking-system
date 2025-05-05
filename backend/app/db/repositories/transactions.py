# backend/app/db/repositories/transactions.py
from typing import List, Optional, Tuple
from datetime import datetime, timedelta

from sqlalchemy import func, desc, and_, or_
from sqlalchemy.orm import Session

from app.db.models.transaction import Transaction, TransactionType, TransactionStatus
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from .base import BaseRepository


class TransactionRepository(BaseRepository[Transaction, TransactionCreate, TransactionUpdate]):
    """Repository for Transaction model operations."""

    def __init__(self):
        super().__init__(Transaction)
    
    def get_by_reference_id(self, db: Session, *, reference_id: str) -> Optional[Transaction]:
        """
        Get a transaction by reference ID.
        
        Args:
            db: Database session
            reference_id: Transaction reference ID
            
        Returns:
            Transaction if found, None otherwise
        """
        return db.query(Transaction).filter(Transaction.reference_id == reference_id).first()
    
    def get_account_transactions(
        self,
        db: Session,
        *,
        account_id: int,
        skip: int = 0,
        limit: int = 100,
        start_date: datetime = None,
        end_date: datetime = None,
        transaction_type: TransactionType = None,
        status: TransactionStatus = None,
        min_amount: float = None,
        max_amount: float = None,
    ) -> List[Transaction]:
        """
        Get transactions for a specific account with optional filtering.
        
        Args:
            db: Database session
            account_id: Account ID
            skip: Number of transactions to skip
            limit: Maximum number of transactions to return
            start_date: Filter by start date
            end_date: Filter by end date
            transaction_type: Filter by transaction type
            status: Filter by status
            min_amount: Filter by minimum amount
            max_amount: Filter by maximum amount
            
        Returns:
            List of transactions
        """
        query = db.query(Transaction).filter(Transaction.account_id == account_id)
        
        # Apply filters
        if start_date:
            query = query.filter(Transaction.created_at >= start_date)
            
        if end_date:
            query = query.filter(Transaction.created_at <= end_date)
            
        if transaction_type:
            query = query.filter(Transaction.transaction_type == transaction_type)
            
        if status:
            query = query.filter(Transaction.status == status)
            
        if min_amount is not None:
            query = query.filter(Transaction.amount >= min_amount)
            
        if max_amount is not None:
            query = query.filter(Transaction.amount <= max_amount)
        
        # Order by creation date, newest first
        query = query.order_by(desc(Transaction.created_at))
        
        return query.offset(skip).limit(limit).all()
    
    def get_user_transactions(
        self,
        db: Session,
        *,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        start_date: datetime = None,
        end_date: datetime = None,
        transaction_type: TransactionType = None,
        status: TransactionStatus = None,
    ) -> List[Transaction]:
        """
        Get transactions for all accounts of a specific user.
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of transactions to skip
            limit: Maximum number of transactions to return
            start_date: Filter by start date
            end_date: Filter by end date
            transaction_type: Filter by transaction type
            status: Filter by status
            
        Returns:
            List of transactions
        """
        from app.db.models.account import Account
        
        query = db.query(Transaction)\
            .join(Account, Transaction.account_id == Account.id)\
            .filter(Account.user_id == user_id)
        
        # Apply filters
        if start_date:
            query = query.filter(Transaction.created_at >= start_date)
            
        if end_date:
            query = query.filter(Transaction.created_at <= end_date)
            
        if transaction_type:
            query = query.filter(Transaction.transaction_type == transaction_type)
            
        if status:
            query = query.filter(Transaction.status == status)
        
        # Order by creation date, newest first
        query = query.order_by(desc(Transaction.created_at))
        
        return query.offset(skip).limit(limit).all()
    
    def generate_reference_id(self, db: Session) -> str:
        """
        Generate a unique transaction reference ID.
        
        Args:
            db: Database session
            
        Returns:
            Unique reference ID
        """
        import random
        import string
        from datetime import datetime
        
        # Generate a random reference ID
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        reference_id = f"TXN-{timestamp}-{random_part}"
        
        # Check if the reference ID already exists
        while self.get_by_reference_id(db, reference_id=reference_id):
            random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            reference_id = f"TXN-{timestamp}-{random_part}"
            
        return reference_id
    
    def create_with_reference_id(
        self,
        db: Session,
        *,
        obj_in: TransactionCreate,
        reference_id: str = None,
    ) -> Transaction:
        """
        Create a new transaction with reference ID.
        
        Args:
            db: Database session
            obj_in: Input data
            reference_id: Optional reference ID
            
        Returns:
            Created transaction
        """
        if not reference_id:
            reference_id = self.generate_reference_id(db)
            
        create_data = obj_in.dict()
        db_obj = Transaction(
            **create_data,
            reference_id=reference_id,
        )
        db.add(db_obj)
        db.flush()
        return db_obj
    
    def get_transaction_stats(
        self,
        db: Session,
        *,
        account_id: int,
        days: int = 30,
    ) -> dict:
        """
        Get transaction statistics for an account.
        
        Args:
            db: Database session
            account_id: Account ID
            days: Number of days to include
            
        Returns:
            Transaction statistics
        """
        start_date = datetime.now() - timedelta(days=days)
        
        # Get total inflow (deposits and incoming transfers)
        inflow_query = db.query(func.sum(Transaction.amount).label("total"))\
            .filter(
                Transaction.account_id == account_id,
                Transaction.created_at >= start_date,
                Transaction.status == TransactionStatus.COMPLETED,
                or_(
                    Transaction.transaction_type == TransactionType.DEPOSIT,
                    and_(
                        Transaction.transaction_type == TransactionType.TRANSFER,
                        Transaction.recipient_account_id == account_id,
                    ),
                )
            )
        total_inflow = inflow_query.scalar() or 0.0
        
        # Get total outflow (withdrawals, payments, fees, and outgoing transfers)
        outflow_query = db.query(func.sum(Transaction.amount).label("total"))\
            .filter(
                Transaction.account_id == account_id,
                Transaction.created_at >= start_date,
                Transaction.status == TransactionStatus.COMPLETED,
                or_(
                    Transaction.transaction_type == TransactionType.WITHDRAWAL,
                    Transaction.transaction_type == TransactionType.PAYMENT,
                    Transaction.transaction_type == TransactionType.FEE,
                    and_(
                        Transaction.transaction_type == TransactionType.TRANSFER,
                        Transaction.recipient_account_id != account_id,
                    ),
                )
            )
        total_outflow = outflow_query.scalar() or 0.0
        
        # Get transaction counts by type
        type_counts = {}
        for t_type in TransactionType:
            count_query = db.query(func.count(Transaction.id))\
                .filter(
                    Transaction.account_id == account_id,
                    Transaction.created_at >= start_date,
                    Transaction.status == TransactionStatus.COMPLETED,
                    Transaction.transaction_type == t_type,
                )
            type_counts[t_type.value] = count_query.scalar()
        
        return {
            "total_inflow": total_inflow,
            "total_outflow": total_outflow,
            "net_flow": total_inflow - total_outflow,
            "transaction_counts": type_counts,
            "period_days": days,
        }