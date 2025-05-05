# backend/app/services/transactions.py
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.repositories import transaction_repository, account_repository, audit_repository
from app.db.models.audit import AuditAction
from app.db.models.transaction import Transaction, TransactionType, TransactionStatus
from app.schemas.transaction import TransactionCreate, TransactionUpdate

class TransactionService:
    """Transaction processing service."""
    
    @staticmethod
    async def get(db: Session, *, transaction_id: int) -> Optional[Transaction]:
        """
        Get a transaction by ID.
        
        Args:
            db: Database session
            transaction_id: Transaction ID
            
        Returns:
            Transaction if found, None otherwise
        """
        return transaction_repository.get(db, id=transaction_id)
    
    @staticmethod
    async def get_by_reference_id(db: Session, *, reference_id: str) -> Optional[Transaction]:
        """
        Get a transaction by reference ID.
        
        Args:
            db: Database session
            reference_id: Transaction reference ID
            
        Returns:
            Transaction if found, None otherwise
        """
        return transaction_repository.get_by_reference_id(db, reference_id=reference_id)
    
    @staticmethod
    async def get_account_transactions(
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
        Get transactions for a specific account.
        
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
        return transaction_repository.get_account_transactions(
            db,
            account_id=account_id,
            skip=skip,
            limit=limit,
            start_date=start_date,
            end_date=end_date,
            transaction_type=transaction_type,
            status=status,
            min_amount=min_amount,
            max_amount=max_amount,
        )
    
    @staticmethod
    async def create_deposit(
        db: Session,
        *,
        account_id: int,
        amount: float,
        description: str = None,
        currency: str = "USD",
        current_user_id: int,
        ip_address: str = None,
    ) -> Transaction:
        """
        Create a deposit transaction.
        
        Args:
            db: Database session
            account_id: Account ID
            amount: Deposit amount
            description: Transaction description
            currency: Transaction currency
            current_user_id: ID of the user performing the action (for audit)
            ip_address: Client IP address for audit logging
            
        Returns:
            Created transaction
            
        Raises:
            ValueError: If deposit amount is not positive
        """
        # Validate amount
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        
        # Get account
        account = account_repository.get(db, id=account_id)
        if not account:
            raise ValueError("Account not found")
        
        # Check if account is active
        if not account.is_active:
            raise ValueError("Account is inactive")
        
        # Check currency
        if currency != account.currency:
            raise ValueError(f"Currency mismatch. Account currency is {account.currency}")
        
        # Create transaction
        reference_id = transaction_repository.generate_reference_id(db)
        transaction_in = TransactionCreate(
            transaction_type=TransactionType.DEPOSIT,
            amount=amount,
            currency=currency,
            description=description or "Deposit",
            status=TransactionStatus.COMPLETED,
            account_id=account_id,
        )
        
        transaction = transaction_repository.create_with_reference_id(
            db,
            obj_in=transaction_in,
            reference_id=reference_id,
        )
        
        # Update account balance
        await AccountService.update_balance(
            db,
            account_id=account_id,
            amount=amount,
            description=f"Deposit: {transaction.reference_id}",
            current_user_id=current_user_id,
            ip_address=ip_address,
        )
        
        # Audit deposit
        audit_repository.log_action(
            db,
            action=AuditAction.CREATE,
            entity_type="transaction",
            entity_id=transaction.id,
            user_id=current_user_id,
            data={
                "transaction_type": TransactionType.DEPOSIT.value,
                "amount": amount,
                "account_id": account_id,
                "reference_id": transaction.reference_id,
            },
            ip_address=ip_address,
        )
        
        return transaction
    
    @staticmethod
    async def create_withdrawal(
        db: Session,
        *,
        account_id: int,
        amount: float,
        description: str = None,
        currency: str = "USD",
        current_user_id: int,
        ip_address: str = None,
    ) -> Transaction:
        """
        Create a withdrawal transaction.
        
        Args:
            db: Database session
            account_id: Account ID
            amount: Withdrawal amount
            description: Transaction description
            currency: Transaction currency
            current_user_id: ID of the user performing the action (for audit)
            ip_address: Client IP address for audit logging
            
        Returns:
            Created transaction
            
        Raises:
            ValueError: If withdrawal amount is not positive or exceeds account balance
        """
        # Validate amount
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        
        # Get account
        account = account_repository.get(db, id=account_id)
        if not account:
            raise ValueError("Account not found")
        
        # Check if account is active
        if not account.is_active:
            raise ValueError("Account is inactive")
        
        # Check currency
        if currency != account.currency:
            raise ValueError(f"Currency mismatch. Account currency is {account.currency}")
        
        # Check balance
        if account.balance < amount:
            raise ValueError("Insufficient funds")
        
        # Create transaction
        reference_id = transaction_repository.generate_reference_id(db)
        transaction_in = TransactionCreate(
            transaction_type=TransactionType.WITHDRAWAL,
            amount=amount,
            currency=currency,
            description=description or "Withdrawal",
            status=TransactionStatus.COMPLETED,
            account_id=account_id,
        )
        
        transaction = transaction_repository.create_with_reference_id(
            db,
            obj_in=transaction_in,
            reference_id=reference_id,
        )
        
        # Update account balance
        await AccountService.update_balance(
            db,
            account_id=account_id,
            amount=-amount,  # Negative for withdrawal
            description=f"Withdrawal: {transaction.reference_id}",
            current_user_id=current_user_id,
            ip_address=ip_address,
        )
        
        # Audit withdrawal
        audit_repository.log_action(
            db,
            action=AuditAction.CREATE,
            entity_type="transaction",
            entity_id=transaction.id,
            user_id=current_user_id,
            data={
                "transaction_type": TransactionType.WITHDRAWAL.value,
                "amount": amount,
                "account_id": account_id,
                "reference_id": transaction.reference_id,
            },
            ip_address=ip_address,
        )
        
        return transaction
    
    @staticmethod
    async def create_transfer(
        db: Session,
        *,
        source_account_id: int,
        destination_account_id: int,
        amount: float,
        description: str = None,
        currency: str = "USD",
        current_user_id: int,
        ip_address: str = None,
    ) -> Transaction:
        """
        Create a transfer transaction.
        
        Args:
            db: Database session
            source_account_id: Source account ID
            destination_account_id: Destination account ID
            amount: Transfer amount
            description: Transaction description
            currency: Transaction currency
            current_user_id: ID of the user performing the action (for audit)
            ip_address: Client IP address for audit logging
            
        Returns:
            Created transaction
            
        Raises:
            ValueError: If transfer amount is not positive, exceeds source account balance,
                        or if source and destination accounts have different currencies
        """
        # Validate amount
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")
        
        # Get source account
        source_account = account_repository.get(db, id=source_account_id)
        if not source_account:
            raise ValueError("Source account not found")
        
        # Check if source account is active
        if not source_account.is_active:
            raise ValueError("Source account is inactive")
        
        # Get destination account
        destination_account = account_repository.get(db, id=destination_account_id)
        if not destination_account:
            raise ValueError("Destination account not found")
        
        # Check if destination account is active
        if not destination_account.is_active:
            raise ValueError("Destination account is inactive")
        
        # Check currency
        if currency != source_account.currency:
            raise ValueError(f"Currency mismatch. Source account currency is {source_account.currency}")
        
        if currency != destination_account.currency:
            raise ValueError(f"Currency mismatch. Destination account currency is {destination_account.currency}")
        
        # Check balance
        if source_account.balance < amount:
            raise ValueError("Insufficient funds")
        
        # Create transaction
        reference_id = transaction_repository.generate_reference_id(db)
        transaction_in = TransactionCreate(
            transaction_type=TransactionType.TRANSFER,
            amount=amount,
            currency=currency,
            description=description or f"Transfer to {destination_account.account_number}",
            status=TransactionStatus.COMPLETED,
            account_id=source_account_id,
            recipient_account_id=destination_account_id,
        )
        
        transaction = transaction_repository.create_with_reference_id(
            db,
            obj_in=transaction_in,
            reference_id=reference_id,
        )
        
        # Update source account balance
        await AccountService.update_balance(
            db,
            account_id=source_account_id,
            amount=-amount,  # Negative for outgoing transfer
            description=f"Transfer to {destination_account.account_number}: {transaction.reference_id}",
            current_user_id=current_user_id,
            ip_address=ip_address,
        )
        
        # Update destination account balance
        await AccountService.update_balance(
            db,
            account_id=destination_account_id,
            amount=amount,  # Positive for incoming transfer
            description=f"Transfer from {source_account.account_number}: {transaction.reference_id}",
            current_user_id=current_user_id,
            ip_address=ip_address,
        )
        
        # Audit transfer
        audit_repository.log_action(
            db,
            action=AuditAction.CREATE,
            entity_type="transaction",
            entity_id=transaction.id,
            user_id=current_user_id,
            data={
                "transaction_type": TransactionType.TRANSFER.value,
                "amount": amount,
                "source_account_id": source_account_id,
                "destination_account_id": destination_account_id,
                "reference_id": transaction.reference_id,
            },
            ip_address=ip_address,
        )
        
        return transaction
    
    @staticmethod
    async def create_payment(
        db: Session,
        *,
        account_id: int,
        amount: float,
        recipient: str,
        description: str = None,
        currency: str = "USD",
        current_user_id: int,
        ip_address: str = None,
    ) -> Transaction:
        """
        Create a payment transaction.
        
        Args:
            db: Database session
            account_id: Account ID
            amount: Payment amount
            recipient: Payment recipient
            description: Transaction description
            currency: Transaction currency
            current_user_id: ID of the user performing the action (for audit)
            ip_address: Client IP address for audit logging
            
        Returns:
            Created transaction
            
        Raises:
            ValueError: If payment amount is not positive or exceeds account balance
        """
        # Validate amount
        if amount <= 0:
            raise ValueError("Payment amount must be positive")
        
        # Get account
        account = account_repository.get(db, id=account_id)
        if not account:
            raise ValueError("Account not found")
        
        # Check if account is active
        if not account.is_active:
            raise ValueError("Account is inactive")
        
        # Check currency
        if currency != account.currency:
            raise ValueError(f"Currency mismatch. Account currency is {account.currency}")
        
        # Check balance
        if account.balance < amount:
            raise ValueError("Insufficient funds")
        
        # Create transaction
        reference_id = transaction_repository.generate_reference_id(db)
        payment_description = description or f"Payment to {recipient}"
        transaction_in = TransactionCreate(
            transaction_type=TransactionType.PAYMENT,
            amount=amount,
            currency=currency,
            description=payment_description,
            status=TransactionStatus.COMPLETED,
            account_id=account_id,
        )
        
        transaction = transaction_repository.create_with_reference_id(
            db,
            obj_in=transaction_in,
            reference_id=reference_id,
        )
        
        # Update account balance
        await AccountService.update_balance(
            db,
            account_id=account_id,
            amount=-amount,  # Negative for payment
            description=f"Payment: {transaction.reference_id}",
            current_user_id=current_user_id,
            ip_address=ip_address,
        )
        
        # Audit payment
        audit_repository.log_action(
            db,
            action=AuditAction.CREATE,
            entity_type="transaction",
            entity_id=transaction.id,
            user_id=current_user_id,
            data={
                "transaction_type": TransactionType.PAYMENT.value,
                "amount": amount,
                "account_id": account_id,
                "recipient": recipient,
                "reference_id": transaction.reference_id,
            },
            ip_address=ip_address,
        )
        
        return transaction
    
    @staticmethod
    async def update_transaction_status(
        db: Session,
        *,
        transaction_id: int,
        status: TransactionStatus,
        current_user_id: int,
        ip_address: str = None,
    ) -> Optional[Transaction]:
        """
        Update a transaction status.
        
        Args:
            db: Database session
            transaction_id: Transaction ID
            status: New status
            current_user_id: ID of the user performing the action (for audit)
            ip_address: Client IP address for audit logging
            
        Returns:
            Updated transaction if found, None otherwise
        """
        transaction = transaction_repository.get(db, id=transaction_id)
        if not transaction:
            return None
        
        # Save old status for audit
        old_status = transaction.status
        
        # Update status
        transaction = transaction_repository.update(
            db, 
            db_obj=transaction, 
            obj_in={"status": status},
        )
        
        # Audit status update
        audit_repository.log_action(
            db,
            action=AuditAction.UPDATE,
            entity_type="transaction",
            entity_id=transaction.id,
            user_id=current_user_id,
            data={
                "previous_status": old_status.value,
                "new_status": status.value,
                "reference_id": transaction.reference_id,
            },
            ip_address=ip_address,
        )
        
        return transaction
    
    @staticmethod
    async def get_transaction_stats(
        db: Session,
        *,
        account_id: int,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get transaction statistics for an account.
        
        Args:
            db: Database session
            account_id: Account ID
            days: Number of days to include
            
        Returns:
            Transaction statistics
        """
        return transaction_repository.get_transaction_stats(
            db,
            account_id=account_id,
            days=days,
        )