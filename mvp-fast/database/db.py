from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import os
from pathlib import Path

# Database configuration - PostgreSQL
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "clasharena_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "clasharena_password")
DB_NAME = os.getenv("DB_NAME", "clasharena_fastmvp")

# Construct DATABASE_URL - prefer Railway private URL when available (more stable)
DATABASE_URL = os.getenv("DATABASE_PRIVATE_URL") or os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Railway/cloud: convert postgres:// to postgresql://
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Detect Railway
IS_RAILWAY = DATABASE_URL and (
    "rlwy.net" in DATABASE_URL or
    "railway.internal" in DATABASE_URL or
    "railway" in DATABASE_URL.lower()
)

# Optional: DATABASE_SSL_MODE=disable for Railway when "server closed connection" persists
_DB_SSL_MODE = os.getenv("DATABASE_SSL_MODE", "").lower()

# Create database engine
try:
    if IS_RAILWAY:
        _connect_timeout = 30
        if _DB_SSL_MODE == "disable":
            _ssl_mode = "disable"
            # Strip existing sslmode, add disable
            from urllib.parse import urlparse, urlencode, parse_qs, urlunparse
            p = urlparse(DATABASE_URL)
            qs = parse_qs(p.query)
            qs["sslmode"] = ["disable"]
            new_query = urlencode(qs, doseq=True)
            DATABASE_URL = urlunparse((p.scheme, p.netloc, p.path, p.params, new_query, p.fragment))
        elif "rlwy.net" in DATABASE_URL:
            _ssl_mode = "require"
            if "sslmode" not in DATABASE_URL:
                sep = "&" if "?" in DATABASE_URL else "?"
                DATABASE_URL = f"{DATABASE_URL}{sep}sslmode=require"
        else:
            _ssl_mode = None
        _connect_args = {"connect_timeout": _connect_timeout}
        if _ssl_mode:
            _connect_args["sslmode"] = _ssl_mode
        # NullPool: fresh connection per request - avoids Railway proxy connection issues
        engine = create_engine(
            DATABASE_URL,
            echo=False,
            poolclass=NullPool,
            connect_args=_connect_args
        )
    else:
        _connect_args = {"connect_timeout": 10}
        engine = create_engine(
            DATABASE_URL,
            echo=False,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            pool_recycle=3600,
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
    """
    FastAPI dependency that yields a SQLAlchemy session.

    Important: retries must happen *before* yielding. If we retry around `yield`,
    FastAPI may throw into the generator on exceptions, which can lead to:
    `RuntimeError: generator didn't stop after throw()`.
    """
    from sqlalchemy import text
    import time

    max_retries = 5 if IS_RAILWAY else 3
    last_exc: Exception | None = None

    for attempt in range(1, max_retries + 1):
        db = SessionLocal()
        try:
            # Validate connection before the first `yield`.
            db.execute(text("SELECT 1"))
            try:
                yield db
            finally:
                db.close()
            return
        except Exception as exc:
            last_exc = exc
            try:
                db.close()
            except Exception:
                pass

            if attempt >= max_retries:
                raise

            # Exponential backoff: 1s, 2s, 4s, 8s (helps Railway cold starts)
            delay = min(2 ** (attempt - 1), 8)
            time.sleep(delay)

    # Should be unreachable; `raise` happens on final attempt.
    if last_exc:
        raise last_exc

def init_db():
    """Initialize database tables"""
    from database.models import Base
    Base.metadata.create_all(bind=engine)

