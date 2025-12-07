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
# For Railway, increase timeout and add SSL mode
try:
    # Parse DATABASE_URL to add SSL mode if needed (Railway requires SSL)
    if DATABASE_URL and "railway" in DATABASE_URL.lower() or "rlwy.net" in DATABASE_URL:
        # Railway requires SSL connections
        if "?" not in DATABASE_URL:
            DATABASE_URL = f"{DATABASE_URL}?sslmode=require"
        elif "sslmode" not in DATABASE_URL:
            DATABASE_URL = f"{DATABASE_URL}&sslmode=require"
    
    engine = create_engine(
        DATABASE_URL, 
        echo=False,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=5,  # Reduced for Railway
        max_overflow=10,  # Reduced for Railway
        pool_recycle=3600,  # Recycle connections after 1 hour
        connect_args={
            "connect_timeout": 10,  # Increased timeout for Railway
            "sslmode": "require" if "railway" in DATABASE_URL.lower() or "rlwy.net" in DATABASE_URL else None
        }
    )
except Exception as e:
    print(f"Warning: Could not create database engine: {e}")
    if "@" in DATABASE_URL:
        print(f"Database URL: {DATABASE_URL.split('@')[0]}@***")  # Hide password in error
    else:
        print(f"Database URL: {DATABASE_URL[:20]}...")  # Show partial URL
    raise

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency to get database session with retry logic"""
    from sqlalchemy import text
    max_retries = 3
    retry_count = 0
    db = None
    
    while retry_count < max_retries:
        try:
            db = SessionLocal()
            # Test connection with a simple query
            db.execute(text("SELECT 1"))
            yield db
            return  # Success, exit function
        except Exception as e:
            retry_count += 1
            if db:
                try:
                    db.close()
                except:
                    pass
            if retry_count >= max_retries:
                # Re-raise the last exception
                raise
            import time
            time.sleep(1)  # Wait 1 second before retry
        finally:
            if db and retry_count < max_retries:
                # Only close if we're not yielding
                try:
                    db.close()
                except:
                    pass

def init_db():
    """Initialize database tables"""
    from database.models import Base
    Base.metadata.create_all(bind=engine)

