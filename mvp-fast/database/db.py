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

# Construct DATABASE_URL - prefer Railway private URL when available (more stable)
DATABASE_URL = os.getenv("DATABASE_PRIVATE_URL") or os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Railway/cloud: convert postgres:// to postgresql:// (SQLAlchemy/psycopg2 expect postgresql://)
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Detect Railway (rlwy.net proxy, railway.internal, or railway in URL)
IS_RAILWAY = DATABASE_URL and (
    "rlwy.net" in DATABASE_URL or
    "railway.internal" in DATABASE_URL or
    "railway" in DATABASE_URL.lower()
)

# Create database engine
try:
    if IS_RAILWAY:
        # Railway: small pool, short recycle (connection limits + idle timeout)
        _pool_size = 1
        _max_overflow = 2
        _pool_recycle = 300  # 5 min - Railway may close idle connections
        _connect_timeout = 30  # Longer for cold starts
        # SSL required for public proxy (rlwy.net), not for internal (railway.internal)
        if "rlwy.net" in DATABASE_URL:
            if "?" not in DATABASE_URL:
                DATABASE_URL = f"{DATABASE_URL}?sslmode=require"
            elif "sslmode" not in DATABASE_URL:
                DATABASE_URL = f"{DATABASE_URL}&sslmode=require"
            _connect_args = {"connect_timeout": _connect_timeout, "sslmode": "require"}
        else:
            _connect_args = {"connect_timeout": _connect_timeout}
    else:
        _pool_size = 5
        _max_overflow = 10
        _pool_recycle = 3600
        _connect_timeout = 10
        _connect_args = {"connect_timeout": _connect_timeout}
    
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,  # Verify connections before using (critical for Railway)
        pool_size=_pool_size,
        max_overflow=_max_overflow,
        pool_recycle=_pool_recycle,
        pool_timeout=60,  # Wait up to 60s for a connection from pool
        connect_args=_connect_args
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
    """Dependency to get database session with retry logic (Railway-friendly)"""
    from sqlalchemy import text
    max_retries = 5 if IS_RAILWAY else 3
    retry_count = 0
    db = None
    
    while retry_count < max_retries:
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            yield db
            return
        except Exception as e:
            retry_count += 1
            if db:
                try:
                    db.close()
                except Exception:
                    pass
            if retry_count >= max_retries:
                raise
            import time
            # Exponential backoff: 1s, 2s, 4s, 8s (helps Railway cold starts)
            delay = min(2 ** (retry_count - 1), 8)
            time.sleep(delay)
        finally:
            if db and retry_count < max_retries:
                try:
                    db.close()
                except Exception:
                    pass

def init_db():
    """Initialize database tables"""
    from database.models import Base
    Base.metadata.create_all(bind=engine)

