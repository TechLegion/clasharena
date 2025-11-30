from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path

# Database configuration - PostgreSQL
# Format: postgresql://username:password@host:port/database_name
# Using same credentials as main app
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "clasharena_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "clasharena_password")
DB_NAME = os.getenv("DB_NAME", "clasharena_fastmvp")

# Construct DATABASE_URL from environment variables or use provided DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create database engine
# PostgreSQL doesn't need check_same_thread
# Use connect_args to handle connection errors gracefully
try:
    engine = create_engine(
        DATABASE_URL, 
        echo=False,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=10,
        max_overflow=20,
        connect_args={
            "connect_timeout": 5  # 5 second timeout
        }
    )
except Exception as e:
    print(f"Warning: Could not create database engine: {e}")
    print(f"Database URL: {DATABASE_URL.split('@')[0]}@***")  # Hide password in error
    raise

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    from database.models import Base
    Base.metadata.create_all(bind=engine)

