# backend/app/db/repositories/base.py
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..base import BaseModel as DBBaseModel

# Define generic types for ORM model and schema
ModelType = TypeVar("ModelType", bound=DBBaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base class for all repositories providing common CRUD operations.
    
    Attributes:
        model: The SQLAlchemy model class
    """
    
    def __init__(self, model: Type[ModelType]):
        """
        Initialize the repository with a SQLAlchemy model.
        
        Args:
            model: SQLAlchemy model class
        """
        self.model = model
    
    def get(self, db: Session, id: int) -> Optional[ModelType]:
        """
        Get a record by ID.
        
        Args:
            db: Database session
            id: Record ID
            
        Returns:
            Record if found, None otherwise
        """
        return db.query(self.model).filter(self.model.id == id).first()
    
    def get_by(self, db: Session, **kwargs) -> Optional[ModelType]:
        """
        Get a record by arbitrary field values.
        
        Args:
            db: Database session
            **kwargs: Field values to filter by
            
        Returns:
            Record if found, None otherwise
        """
        filters = [getattr(self.model, field) == value for field, value in kwargs.items()]
        return db.query(self.model).filter(*filters).first()
    
    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        **kwargs
    ) -> List[ModelType]:
        """
        Get multiple records with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            **kwargs: Field values to filter by
            
        Returns:
            List of records
        """
        filters = [getattr(self.model, field) == value for field, value in kwargs.items()]
        query = db.query(self.model)
        
        if filters:
            query = query.filter(*filters)
            
        return query.offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record.
        
        Args:
            db: Database session
            obj_in: Input data
            
        Returns:
            Created record
        """
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.flush()  # Flush to get the ID but don't commit yet
        return db_obj
    
    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Update a record.
        
        Args:
            db: Database session
            db_obj: Record to update
            obj_in: Update data
            
        Returns:
            Updated record
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
        db.flush()  # Flush changes but don't commit yet
        return db_obj
    
    def delete(self, db: Session, *, id: int) -> Optional[ModelType]:
        """
        Delete a record by ID.
        
        Args:
            db: Database session
            id: Record ID
            
        Returns:
            Deleted record if found, None otherwise
        """
        obj = db.query(self.model).get(id)
        if obj:
            db.delete(obj)
            db.flush()  # Flush changes but don't commit yet
        return obj
    
    def count(self, db: Session, **kwargs) -> int:
        """
        Count records matching filters.
        
        Args:
            db: Database session
            **kwargs: Field values to filter by
            
        Returns:
            Number of matching records
        """
        filters = [getattr(self.model, field) == value for field, value in kwargs.items()]
        query = db.query(self.model)
        
        if filters:
            query = query.filter(*filters)
            
        return query.count()