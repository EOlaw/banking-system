# backend/app/config/settings.py
import os
from typing import Optional, Dict, Any

class Settings:
    PROJECT_NAME: str = "Banking System"
    PROJECT_VERSION: str = "1.0.0"
    
    # Database settings
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "banking_db")
    DATABASE_URL: str = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
    
    # JWT settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "very-secret-key-for-development-only")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Security
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8000"]
    
settings = Settings()


# backend/app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Enables reconnection on disconnection
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()