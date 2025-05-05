# backend/app/services/users.py
from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.repositories import user_repository, audit_repository
from app.db.models.audit import AuditAction
from app.db.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password

class UserService:
    """User management service."""
    
    @staticmethod
    async def get(db: Session, *, user_id: int) -> Optional[User]:
        """
        Get a user by ID.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            User if found, None otherwise
        """
        return user_repository.get(db, id=user_id)
    
    @staticmethod
    async def get_by_email(db: Session, *, email: str) -> Optional[User]:
        """
        Get a user by email.
        
        Args:
            db: Database session
            email: User email
            
        Returns:
            User if found, None otherwise
        """
        return user_repository.get_by_email(db, email=email)
    
    @staticmethod
    async def get_by_username(db: Session, *, username: str) -> Optional[User]:
        """
        Get a user by username.
        
        Args:
            db: Database session
            username: Username
            
        Returns:
            User if found, None otherwise
        """
        return user_repository.get_by_username(db, username=username)
    
    @staticmethod
    async def create(
        db: Session, 
        *, 
        user_in: UserCreate,
        current_user_id: int = None,
        ip_address: str = None,
    ) -> User:
        """
        Create a new user.
        
        Args:
            db: Database session
            user_in: Input data
            current_user_id: ID of the user performing the action (for audit)
            ip_address: Client IP address for audit logging
            
        Returns:
            Created user
        """
        # Check if user with same email exists
        user = await UserService.get_by_email(db, email=user_in.email)
        if user:
            raise ValueError("Email already registered")
        
        # Check if user with same username exists
        if user_in.username:
            user = await UserService.get_by_username(db, username=user_in.username)
            if user:
                raise ValueError("Username already taken")
        
        # Hash the password
        hashed_password = get_password_hash(user_in.password)
        
        # Create the user
        user = user_repository.create_with_password(
            db, 
            obj_in=user_in, 
            hashed_password=hashed_password,
        )
        
        # Audit user creation
        audit_repository.log_action(
            db,
            action=AuditAction.CREATE,
            entity_type="user",
            entity_id=user.id,
            user_id=current_user_id,
            data={"email": user.email, "username": user.username},
            ip_address=ip_address,
        )
        
        return user
    
    @staticmethod
    async def update(
        db: Session, 
        *, 
        user_id: int, 
        user_in: UserUpdate,
        current_user_id: int,
        ip_address: str = None,
    ) -> Optional[User]:
        """
        Update a user.
        
        Args:
            db: Database session
            user_id: User ID
            user_in: Update data
            current_user_id: ID of the user performing the action (for audit)
            ip_address: Client IP address for audit logging
            
        Returns:
            Updated user if found, None otherwise
        """
        user = user_repository.get(db, id=user_id)
        if not user:
            return None
        
        # Check if email is being changed and if it's already taken
        if user_in.email and user_in.email != user.email:
            existing_user = await UserService.get_by_email(db, email=user_in.email)
            if existing_user:
                raise ValueError("Email already registered")
        
        # Check if username is being changed and if it's already taken
        if user_in.username and user_in.username != user.username:
            existing_user = await UserService.get_by_username(db, username=user_in.username)
            if existing_user:
                raise ValueError("Username already taken")
        
        # Update the password if provided
        update_data = user_in.dict(exclude_unset=True)
        if user_in.password:
            hashed_password = get_password_hash(user_in.password)
            update_data["hashed_password"] = hashed_password
            # Remove the original password field
            update_data.pop("password", None)
        
        # Update the user
        user = user_repository.update(db, db_obj=user, obj_in=update_data)
        
        # Audit user update
        audit_data = {k: v for k, v in update_data.items() if k != "hashed_password"}
        if "password" in user_in.dict(exclude_unset=True):
            audit_data["password_changed"] = True
        
        audit_repository.log_action(
            db,
            action=AuditAction.UPDATE,
            entity_type="user",
            entity_id=user.id,
            user_id=current_user_id,
            data=audit_data,
            ip_address=ip_address,
        )
        
        return user
    
    @staticmethod
    async def delete(
        db: Session, 
        *, 
        user_id: int,
        current_user_id: int,
        ip_address: str = None,
    ) -> Optional[User]:
        """
        Delete a user.
        
        Args:
            db: Database session
            user_id: User ID
            current_user_id: ID of the user performing the action (for audit)
            ip_address: Client IP address for audit logging
            
        Returns:
            Deleted user if found, None otherwise
        """
        user = user_repository.get(db, id=user_id)
        if not user:
            return None
        
        # Delete the user
        user = user_repository.delete(db, id=user_id)
        
        # Audit user deletion
        audit_repository.log_action(
            db,
            action=AuditAction.DELETE,
            entity_type="user",
            entity_id=user_id,
            user_id=current_user_id,
            data={"email": user.email, "username": user.username},
            ip_address=ip_address,
        )
        
        return user
    
    @staticmethod
    async def authenticate(
        db: Session, 
        *, 
        email: str, 
        password: str
    ) -> Optional[User]:
        """
        Authenticate a user.
        
        Args:
            db: Database session
            email: User email
            password: Plain password
            
        Returns:
            User if authentication successful, None otherwise
        """
        user = await UserService.get_by_email(db, email=email)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    @staticmethod
    async def is_active(user: User) -> bool:
        """
        Check if a user is active.
        
        Args:
            user: User to check
            
        Returns:
            True if user is active, False otherwise
        """
        return user.is_active
    
    @staticmethod
    async def is_superuser(user: User) -> bool:
        """
        Check if a user is a superuser.
        
        Args:
            user: User to check
            
        Returns:
            True if user is a superuser, False otherwise
        """
        return user.is_superuser
    
    @staticmethod
    async def change_password(
        db: Session, 
        *, 
        user_id: int, 
        current_password: str, 
        new_password: str,
        ip_address: str = None,
    ) -> Optional[User]:
        """
        Change a user's password.
        
        Args:
            db: Database session
            user_id: User ID
            current_password: Current password
            new_password: New password
            ip_address: Client IP address for audit logging
            
        Returns:
            Updated user if password change successful, None otherwise
            
        Raises:
            ValueError: If current password is incorrect
        """
        user = user_repository.get(db, id=user_id)
        if not user:
            return None
        
        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            raise ValueError("Current password is incorrect")
        
        # Hash new password
        hashed_password = get_password_hash(new_password)
        
        # Update password
        user = user_repository.update(
            db, 
            db_obj=user, 
            obj_in={"hashed_password": hashed_password},
        )
        
        # Audit password change
        audit_repository.log_action(
            db,
            action=AuditAction.UPDATE,
            entity_type="user",
            entity_id=user.id,
            user_id=user.id,
            data={"password_changed": True},
            ip_address=ip_address,
        )
        
        return user