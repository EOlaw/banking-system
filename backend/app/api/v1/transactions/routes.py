# backend/app/api/v1/transactions/routes.py
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import TransactionService, AccountService, AuthService, NotificationService
from app.schemas.transaction import (
    Transaction, TransactionList, TransactionWithAccount,
    DepositCreate, WithdrawalCreate, TransferCreate, PaymentCreate
)
from app.db.models.user import User as UserModel
from app.db.models.transaction import TransactionType, TransactionStatus

router = APIRouter()

@router.get("/", response_model=TransactionList)
async def read_transactions(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    account_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    transaction_type: Optional[TransactionType] = None,
    status: Optional[TransactionStatus] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(AuthService.get_current_user),
):
    """
    Retrieve transactions.
    Regular users can only get their own transactions.
    Superusers can get any transaction by setting all_users=True.
    """
    # Check if user is superuser and wants to see all transactions
    all_users = request.query_params.get("all_users", "").lower() == "true"
    
    if account_id:
        # Check if user has permission to access this account
        account = await AccountService.get(db, account_id=account_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found",
            )
            
        if account.user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to access this account",
            )
            
        # Get transactions for specific account
        transactions = await TransactionService.get_account_transactions(
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
        
        # Count total transactions for this account
        from app.db.repositories import transaction_repository
        total = transaction_repository.count(
            db, 
            account_id=account_id,
        )
    elif all_users and current_user.is_superuser:
        # Get all transactions for superuser
        from app.db.repositories import transaction_repository
        
        # Build filter conditions
        filter_args = {}
        if transaction_type:
            filter_args["transaction_type"] = transaction_type
        if status:
            filter_args["status"] = status
        
        transactions = transaction_repository.get_multi(
            db,
            skip=skip,
            limit=limit,
            **filter_args,
        )
        
        # Count total transactions
        total = transaction_repository.count(db, **filter_args)
    else:
        # Get transactions for current user
        from app.db.repositories import transaction_repository
        transactions = transaction_repository.get_user_transactions(
            db,
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            start_date=start_date,
            end_date=end_date,
            transaction_type=transaction_type,
            status=status,
        )
        
        # Count total transactions for current user
        # This is an approximation
        total = len(transactions)
        if skip == 0 and len(transactions) < limit:
            total = len(transactions)
        else:
            # We need to count all transactions
            # This could be optimized with a separate count query
            total = transaction_repository.count_user_transactions(
                db,
                user_id=current_user.id,
                start_date=start_date,
                end_date=end_date,
                transaction_type=transaction_type,
                status=status,
            )
    
    return {
        "items": transactions,
        "total": total,
    }

@router.get("/{transaction_id}", response_model=Transaction)
async def read_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(AuthService.get_current_user),
):
    """
    Get a specific transaction by id.
    Regular users can only get their own transactions.
    Superusers can get any transaction.
    """
    transaction = await TransactionService.get(db, transaction_id=transaction_id)
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    
    # Get account for permission check
    account = await AccountService.get(db, account_id=transaction.account_id)
    
    # Check if user has permission to access this transaction
    if account.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this transaction",
        )
    
    return transaction

@router.post("/deposit", response_model=Transaction)
async def create_deposit(
    request: Request,
    deposit_in: DepositCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(AuthService.get_current_user),
):
    """
    Create a deposit transaction.
    """
    # Check if user has permission to deposit to this account
    account = await AccountService.get(db, account_id=deposit_in.account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
        
    if account.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to deposit to this account",
        )
    
    # Get client IP for audit
    client_ip = request.client.host if request.client else None
    
    try:
        transaction = await TransactionService.create_deposit(
            db,
            account_id=deposit_in.account_id,
            amount=deposit_in.amount,
            description=deposit_in.description,
            currency=deposit_in.currency,
            current_user_id=current_user.id,
            ip_address=client_ip,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    # Send transaction notification
    await NotificationService.send_transaction_notification(
        db,
        transaction_id=transaction.id,
    )
    
    return transaction

@router.post("/withdrawal", response_model=Transaction)
async def create_withdrawal(
    request: Request,
    withdrawal_in: WithdrawalCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(AuthService.get_current_user),
):
    """
    Create a withdrawal transaction.
    """
    # Check if user has permission to withdraw from this account
    account = await AccountService.get(db, account_id=withdrawal_in.account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
        
    if account.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to withdraw from this account",
        )
    
    # Get client IP for audit
    client_ip = request.client.host if request.client else None
    
    try:
        transaction = await TransactionService.create_withdrawal(
            db,
            account_id=withdrawal_in.account_id,
            amount=withdrawal_in.amount,
            description=withdrawal_in.description,
            currency=withdrawal_in.currency,
            current_user_id=current_user.id,
            ip_address=client_ip,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    # Send transaction notification
    await NotificationService.send_transaction_notification(
        db,
        transaction_id=transaction.id,
    )
    
    # Check if balance is low and send notification if needed
    low_balance_threshold = 100.0  # Example threshold
    await NotificationService.send_low_balance_notification(
        db,
        account_id=withdrawal_in.account_id,
        threshold=low_balance_threshold,
    )
    
    return transaction

@router.post("/transfer", response_model=Transaction)
async def create_transfer(
    request: Request,
    transfer_in: TransferCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(AuthService.get_current_user),
):
    """
    Create a transfer transaction.
    """
    # Check if user has permission to transfer from this account
    source_account = await AccountService.get(db, account_id=transfer_in.source_account_id)
    if not source_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source account not found",
        )
        
    if source_account.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to transfer from this account",
        )
    
    # Check if destination account exists
    destination_account = await AccountService.get(db, account_id=transfer_in.destination_account_id)
    if not destination_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Destination account not found",
        )
    
    # Get client IP for audit
    client_ip = request.client.host if request.client else None
    
    try:
        transaction = await TransactionService.create_transfer(
            db,
            source_account_id=transfer_in.source_account_id,
            destination_account_id=transfer_in.destination_account_id,
            amount=transfer_in.amount,
            description=transfer_in.description,
            currency=transfer_in.currency,
            current_user_id=current_user.id,
            ip_address=client_ip,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    # Send transaction notification
    await NotificationService.send_transaction_notification(
        db,
        transaction_id=transaction.id,
    )
    
    # Check if balance is low and send notification if needed
    low_balance_threshold = 100.0  # Example threshold
    await NotificationService.send_low_balance_notification(
        db,
        account_id=transfer_in.source_account_id,
        threshold=low_balance_threshold,
    )
    
    return transaction

@router.post("/payment", response_model=Transaction)
async def create_payment(
    request: Request,
    payment_in: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(AuthService.get_current_user),
):
    """
    Create a payment transaction.
    """
    # Check if user has permission to make payment from this account
    account = await AccountService.get(db, account_id=payment_in.account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
        
    if account.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to make payment from this account",
        )
    
    # Get client IP for audit
    client_ip = request.client.host if request.client else None
    
    try:
        transaction = await TransactionService.create_payment(
            db,
            account_id=payment_in.account_id,
            amount=payment_in.amount,
            recipient=payment_in.recipient,
            description=payment_in.description,
            currency=payment_in.currency,
            current_user_id=current_user.id,
            ip_address=client_ip,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    # Send transaction notification
    await NotificationService.send_transaction_notification(
        db,
        transaction_id=transaction.id,
    )
    
    # Check if balance is low and send notification if needed
    low_balance_threshold = 100.0  # Example threshold
    await NotificationService.send_low_balance_notification(
        db,
        account_id=payment_in.account_id,
        threshold=low_balance_threshold,
    )
    
    return transaction

@router.get("/stats/{account_id}")
async def get_transaction_stats(
    account_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(AuthService.get_current_user),
):
    """
    Get transaction statistics for an account.
    """
    # Check if user has permission to access this account
    account = await AccountService.get(db, account_id=account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
        
    if account.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this account",
        )
    
    stats = await TransactionService.get_transaction_stats(
        db,
        account_id=account_id,
        days=days,
    )
    
    return stats