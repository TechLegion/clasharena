from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from typing import Generator

from app.core.config import settings

# Create database engine
engine = create_engine(settings.DATABASE_URL, echo=True)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db() -> Generator:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
    from shared.models import Base
    Base.metadata.create_all(bind=engine)
