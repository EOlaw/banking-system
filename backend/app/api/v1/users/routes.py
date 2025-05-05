# backend/app/api/v1/users/routes.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import UserService, AuthService
from app.schemas.user import User, UserCreate, UserUpdate
from app.db.models.user import User as UserModel

router = APIRouter()

@router.get("/", response_model=List[User])
async def read_users(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(AuthService.get_current_active_superuser),
):
    """
    Retrieve users. Only superusers can access this endpoint.
    """
    # Using UserRepository directly since we need more complex filtering
    from app.db.repositories import user_repository
    
    users = user_repository.get_multi_with_pagination(
        db,
        skip=skip,
        limit=limit,
        search=search,
        is_active=is_active,
    )
    
    return users

@router.post("/", response_model=User)
async def create_user(
    request: Request,
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(AuthService.get_current_active_superuser),
):
    """
    Create new user. Only superusers can create other users.
    Regular users can register themselves via /auth/register.
    """
    # Get client IP for audit
    client_ip = request.client.host if request.client else None
    
    try:
        user = await UserService.create(
            db, 
            user_in=user_in, 
            current_user_id=current_user.id if current_user else None,
            ip_address=client_ip,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    return user

@router.get("/{user_id}", response_model=User)
async def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(AuthService.get_current_user),
):
    """
    Get a specific user by id.
    Regular users can only get their own user information.
    Superusers can get any user.
    """
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this user",
        )
    
    user = await UserService.get(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return user

@router.put("/{user_id}", response_model=User)
async def update_user(
    request: Request,
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(AuthService.get_current_user),
):
    """
    Update a user.
    Regular users can only update their own user information.
    Superusers can update any user.
    """
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this user",
        )
    
    # Get client IP for audit
    client_ip = request.client.host if request.client else None
    
    try:
        user = await UserService.update(
            db, 
            user_id=user_id, 
            user_in=user_in,
            current_user_id=current_user.id,
            ip_address=client_ip,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return user

@router.delete("/{user_id}", response_model=User)
async def delete_user(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(AuthService.get_current_active_superuser),
):
    """
    Delete a user. Only superusers can delete users.
    """
    # Get client IP for audit
    client_ip = request.client.host if request.client else None
    
    user = await UserService.delete(
        db, 
        user_id=user_id,
        current_user_id=current_user.id,
        ip_address=client_ip,
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return user