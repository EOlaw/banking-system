# backend/app/api/v1/accounts/routes.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import AccountService, AuthService
from app.schemas.account import Account, AccountCreate, AccountUpdate, AccountList
from app.db.models.user import User as UserModel
from app.db.models.account import AccountType

router = APIRouter()

@router.get("/", response_model=AccountList)
async def read_accounts(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    account_type: Optional[AccountType] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(AuthService.get_current_user),
):
    """
    Retrieve accounts for the current user.
    Superusers can access all accounts by setting all_users=True.
    """
    # Check if user is superuser and wants to see all accounts
    all_users = request.query_params.get("all_users", "").lower() == "true"
    
    if all_users and current_user.is_superuser:
        # Get all accounts for superuser
        from app.db.repositories import account_repository
        accounts = account_repository.get_multi(
            db,
            skip=skip,
            limit=limit,
            account_type=account_type,
            is_active=is_active,
        )
        total = account_repository.count(db)
    else:
        # Get accounts for current user
        accounts = await AccountService.get_user_accounts(
            db,
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            account_type=account_type,
            is_active=is_active,
        )
        
        # Count total accounts for current user
        from app.db.repositories import account_repository
        total = account_repository.count(db, user_id=current_user.id)
    
    return {
        "items": accounts,
        "total": total,
    }

@router.post("/", response_model=Account)
async def create_account(
    request: Request,
    account_in: AccountCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(AuthService.get_current_user),
):
    """
    Create a new account.
    Regular users can only create accounts for themselves.
    Superusers can create accounts for any user by providing user_id.
    """
    # Check if user is superuser and wants to create account for another user
    user_id = current_user.id
    if current_user.is_superuser and request.query_params.get("user_id"):
        try:
            user_id = int(request.query_params.get("user_id"))
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user_id",
            )
    
    # Get client IP for audit
    client_ip = request.client.host if request.client else None
    
    account = await AccountService.create(
        db,
        obj_in=account_in,
        user_id=user_id,
        current_user_id=current_user.id,
        ip_address=client_ip,
    )
    
    # Send notification for new account
    from app.services import NotificationService
    await NotificationService.send_account_created_notification(
        db,
        account_id=account.id,
    )
    
    return account

@router.get("/{account_id}", response_model=Account)
async def read_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(AuthService.get_current_user),
):
    """
    Get a specific account by id.
    Regular users can only get their own accounts.
    Superusers can get any account.
    """
    account = await AccountService.get(db, account_id=account_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    
    # Check if user has permission to access this account
    if account.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this account",
        )
    
    return account

@router.put("/{account_id}", response_model=Account)
async def update_account(
    request: Request,
    account_id: int,
    account_in: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(AuthService.get_current_user),
):
    """
    Update an account.
    Regular users can only update their own accounts.
    Superusers can update any account.
    """
    account = await AccountService.get(db, account_id=account_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    
    # Check if user has permission to update this account
    if account.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this account",
        )
    
    # Get client IP for audit
    client_ip = request.client.host if request.client else None
    
    updated_account = await AccountService.update(
        db,
        account_id=account_id,
        obj_in=account_in,
        current_user_id=current_user.id,
        ip_address=client_ip,
    )
    
    return updated_account

@router.post("/{account_id}/deactivate", response_model=Account)
async def deactivate_account(
    request: Request,
    account_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(AuthService.get_current_user),
):
    """
    Deactivate an account.
    Regular users can only deactivate their own accounts.
    Superusers can deactivate any account.
    """
    account = await AccountService.get(db, account_id=account_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    
    # Check if user has permission to deactivate this account
    if account.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to deactivate this account",
        )
    
    # Get client IP for audit
    client_ip = request.client.host if request.client else None
    
    deactivated_account = await AccountService.deactivate(
        db,
        account_id=account_id,
        current_user_id=current_user.id,
        ip_address=client_ip,
    )
    
    return deactivated_account

@router.post("/{account_id}/reactivate", response_model=Account)
async def reactivate_account(
    request: Request,
    account_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(AuthService.get_current_user),
):
    """
    Reactivate an account.
    Regular users can only reactivate their own accounts.
    Superusers can reactivate any account.
    """
    account = await AccountService.get(db, account_id=account_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    
    # Check if user has permission to reactivate this account
    if account.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to reactivate this account",
        )
    
    # Get client IP for audit
    client_ip = request.client.host if request.client else None
    
    reactivated_account = await AccountService.reactivate(
        db,
        account_id=account_id,
        current_user_id=current_user.id,
        ip_address=client_ip,
    )
    
    return reactivated_account

@router.delete("/{account_id}", response_model=Account)
async def delete_account(
    request: Request,
    account_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(AuthService.get_current_active_superuser),
):
    """
    Delete an account. Only superusers can delete accounts.
    """
    account = await AccountService.get(db, account_id=account_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    
    # Get client IP for audit
    client_ip = request.client.host if request.client else None
    
    deleted_account = await AccountService.delete(
        db,
        account_id=account_id,
        current_user_id=current_user.id,
        ip_address=client_ip,
    )
    
    return deleted_account