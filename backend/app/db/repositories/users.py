# backend/app/db/repositories/users.py
from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from .base import BaseRepository


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """Repository for User model operations."""

    def __init__(self):
        super().__init__(User)

    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """
        Get a user by email.
        
        Args:
            db: Database session
            email: User email
            
        Returns:
            User if found, None otherwise
        """
        return db.query(User).filter(User.email == email).first()
    
    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        """
        Get a user by username.
        
        Args:
            db: Database session
            username: Username
            
        Returns:
            User if found, None otherwise
        """
        return db.query(User).filter(User.username == username).first()
        
    def create_with_password(self, db: Session, *, obj_in: UserCreate, hashed_password: str) -> User:
        """
        Create a new user with a hashed password.
        
        Args:
            db: Database session
            obj_in: Input data
            hashed_password: Hashed password
            
        Returns:
            Created user
        """
        create_data = obj_in.dict(exclude={"password"})
        db_obj = User(**create_data, hashed_password=hashed_password)
        db.add(db_obj)
        db.flush()
        return db_obj
    
    def authenticate(self, db: Session, *, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user with email and password.
        
        Args:
            db: Database session
            email: User email
            password: Plain password
            
        Returns:
            User if authentication successful, None otherwise
        """
        from app.core.security import verify_password
        
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    def is_active(self, user: User) -> bool:
        """
        Check if a user is active.
        
        Args:
            user: User to check
            
        Returns:
            True if user is active, False otherwise
        """
        return user.is_active
    
    def is_superuser(self, user: User) -> bool:
        """
        Check if a user is a superuser.
        
        Args:
            user: User to check
            
        Returns:
            True if user is a superuser, False otherwise
        """
        return user.is_superuser
    
    def get_multi_with_pagination(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        sort_by: str = "id",
        sort_desc: bool = False,
        search: str = None,
        is_active: bool = None,
        is_superuser: bool = None,
    ) -> List[User]:
        """
        Get multiple users with advanced filtering and sorting.
        
        Args:
            db: Database session
            skip: Number of users to skip
            limit: Maximum number of users to return
            sort_by: Field to sort by
            sort_desc: Sort in descending order if True
            search: Search string to filter by username, email, or full_name
            is_active: Filter by active status if provided
            is_superuser: Filter by superuser status if provided
            
        Returns:
            List of users
        """
        query = db.query(User)
        
        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (User.username.ilike(search_term)) |
                (User.email.ilike(search_term)) |
                (User.full_name.ilike(search_term))
            )
            
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
            
        if is_superuser is not None:
            query = query.filter(User.is_superuser == is_superuser)
        
        # Apply sorting
        if hasattr(User, sort_by):
            order_column = getattr(User, sort_by)
            if sort_desc:
                order_column = order_column.desc()
            query = query.order_by(order_column)
        else:
            # Default sort by id
            query = query.order_by(User.id)
        
        return query.offset(skip).limit(limit).all()