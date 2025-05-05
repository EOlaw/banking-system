# backend/app/db/session.py
from typing import Any, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from app.config.settings import settings

# Construct database URL based on configuration
SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)

# Configure the SQLAlchemy engine with connection pooling
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,  # Verify connections before usage to avoid stale connections
    echo=settings.DB_ECHO_SQL,  # Log generated SQL (useful for debugging)
)

# Create a session factory configured with the engine
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)

# Function to get a database session
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a SQLAlchemy Session.
    
    Usage:
        @app.get("/users/")
        def read_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    
    Yields:
        Session: SQLAlchemy Session object
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to get a transactional session with automatic commit/rollback
def get_transactional_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a SQLAlchemy Session with transaction management.
    The transaction is automatically committed if no exceptions occur,
    or rolled back if an exception is raised.
    
    Usage:
        @app.post("/users/")
        def create_user(user: UserCreate, db: Session = Depends(get_transactional_db)):
            db_user = User(**user.dict())
            db.add(db_user)
            return db_user  # Transaction automatically committed if no exceptions
    
    Yields:
        Session: SQLAlchemy Session object
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# Function to execute raw SQL queries
def execute_raw_sql(query: str, params: dict = None) -> list[Any]:
    """
    Execute a raw SQL query and return the results.
    
    Args:
        query: SQL query string
        params: Dictionary of parameters to bind to the query
    
    Returns:
        List of results
    """
    with engine.connect() as connection:
        result = connection.execute(query, params or {})
        return [dict(row) for row in result]

# Function to ensure all tables exist in the database
def create_all_tables() -> None:
    """Create all tables defined in models if they don't exist."""
    from .base import Base
    Base.metadata.create_all(bind=engine)

# Function to drop all tables (use with caution)
def drop_all_tables() -> None:
    """Drop all tables defined in models (DESTRUCTIVE OPERATION)."""
    from .base import Base
    Base.metadata.drop_all(bind=engine)