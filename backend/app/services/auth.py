# backend/app/services/auth.py
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWTError
import jwt
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.repositories import user_repository, audit_repository
from app.db.models.audit import AuditAction
from app.models.user import User
from app.core.security import ALGORITHM, verify_password
from app.config.settings import settings

# OAuth2 token URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

class AuthService:
    """Authentication and authorization service."""
    
    @staticmethod
    async def authenticate_user(
        db: Session, 
        *, 
        email: str, 
        password: str,
        ip_address: str = None,
    ) -> Optional[User]:
        """
        Authenticate a user with email and password.
        
        Args:
            db: Database session
            email: User email
            password: Plain password
            ip_address: Client IP address for audit logging
            
        Returns:
            User if authentication successful, None otherwise
        """
        user = user_repository.get_by_email(db, email=email)
        
        if not user:
            # Audit failed login attempt
            audit_repository.log_action(
                db,
                action=AuditAction.LOGIN,
                entity_type="user",
                data={"email": email, "success": False, "reason": "user_not_found"},
                ip_address=ip_address,
            )
            return None
        
        if not verify_password(password, user.hashed_password):
            # Audit failed login attempt
            audit_repository.log_action(
                db,
                action=AuditAction.LOGIN,
                entity_type="user",
                entity_id=user.id,
                user_id=user.id,
                data={"success": False, "reason": "invalid_password"},
                ip_address=ip_address,
            )
            return None
        
        if not user.is_active:
            # Audit failed login attempt
            audit_repository.log_action(
                db,
                action=AuditAction.LOGIN,
                entity_type="user",
                entity_id=user.id,
                user_id=user.id,
                data={"success": False, "reason": "inactive_user"},
                ip_address=ip_address,
            )
            return None
        
        # Audit successful login
        audit_repository.log_action(
            db,
            action=AuditAction.LOGIN,
            entity_type="user",
            entity_id=user.id,
            user_id=user.id,
            data={"success": True},
            ip_address=ip_address,
        )
        
        return user
    
    @staticmethod
    async def get_current_user(
        db: Session = Depends(get_db), 
        token: str = Depends(oauth2_scheme)
    ) -> User:
        """
        Get the current authenticated user from the token.
        
        Args:
            db: Database session
            token: JWT token
            
        Returns:
            Current user
            
        Raises:
            HTTPException: If token is invalid or user not found
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[ALGORITHM]
            )
            user_id: str = payload.get("sub")
            if user_id is None:
                raise credentials_exception
        except PyJWTError:
            raise credentials_exception
            
        user = user_repository.get(db, id=int(user_id))
        if user is None:
            raise credentials_exception
            
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user",
            )
            
        return user
    
    @staticmethod
    async def get_current_active_superuser(
        current_user: User = Depends(get_current_user),
    ) -> User:
        """
        Get the current authenticated superuser.
        
        Args:
            current_user: Current authenticated user
            
        Returns:
            Current superuser
            
        Raises:
            HTTPException: If user is not a superuser
        """
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges",
            )
            
        return current_user
    
    @staticmethod
    async def logout(
        db: Session,
        *,
        user_id: int,
        ip_address: str = None,
    ) -> bool:
        """
        Log out a user.
        
        Args:
            db: Database session
            user_id: User ID
            ip_address: Client IP address for audit logging
            
        Returns:
            True if logout successful
        """
        # Audit logout action
        audit_repository.log_action(
            db,
            action=AuditAction.LOGOUT,
            entity_type="user",
            entity_id=user_id,
            user_id=user_id,
            ip_address=ip_address,
        )
        
        return True