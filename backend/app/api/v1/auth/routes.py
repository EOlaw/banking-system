# backend/app/api/v1/auth/routes.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.db.session import get_db
from app.core.security import create_access_token
from app.services import AuthService, UserService
from app.schemas.auth import Token, Login, PasswordChange
from app.schemas.user import User
from app.config.settings import settings

router = APIRouter()

@router.post("/login", response_model=Token)
async def login_access_token(
    request: Request,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    # Get client IP for audit
    client_ip = request.client.host if request.client else None
    
    user = await AuthService.authenticate_user(
        db, 
        email=form_data.username, 
        password=form_data.password,
        ip_address=client_ip,
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }

@router.post("/login/email", response_model=Token)
async def login_email_password(
    request: Request,
    login_data: Login,
    db: Session = Depends(get_db),
):
    """
    Login using email and password, get an access token for future requests.
    """
    # Get client IP for audit
    client_ip = request.client.host if request.client else None
    
    user = await AuthService.authenticate_user(
        db, 
        email=login_data.email, 
        password=login_data.password,
        ip_address=client_ip,
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }

@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Logout the current user.
    """
    # Get client IP for audit
    client_ip = request.client.host if request.client else None
    
    await AuthService.logout(
        db,
        user_id=current_user.id,
        ip_address=client_ip,
    )
    
    return {"detail": "Successfully logged out"}

@router.post("/password-change")
async def change_password(
    request: Request,
    password_data: PasswordChange,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Change the current user's password.
    """
    # Get client IP for audit
    client_ip = request.client.host if request.client else None
    
    try:
        await UserService.change_password(
            db,
            user_id=current_user.id,
            current_password=password_data.current_password,
            new_password=password_data.new_password,
            ip_address=client_ip,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    return {"detail": "Password changed successfully"}

@router.get("/me", response_model=User)
async def read_users_me(
    current_user: User = Depends(AuthService.get_current_user),
):
    """
    Get current user information.
    """
    return current_user