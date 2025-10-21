"""
Rate limiting configuration for ClashArena
Safe implementation that won't break existing functionality
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException, status
import logging

# Create logger
logger = logging.getLogger(__name__)

# Initialize rate limiter with Redis backend (optional - falls back to memory if Redis unavailable)
try:
    limiter = Limiter(
        key_func=get_remote_address,
        storage_uri="redis://localhost:6379",  # Use Redis if available
        default_limits=["1000/hour"],  # Global limit as fallback
        headers_enabled=True,
    )
    # Reduce noise: do not log successful init at info in production
    logger.debug("Rate limiter initialized with Redis backend")
except Exception as e:
    # Fallback to in-memory storage if Redis is not available
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["1000/hour"]
    )
    logger.debug(f"Rate limiter initialized with in-memory storage: {e}")

def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded errors"""
    # Avoid noisy logs on normal user behavior; keep it at debug or structured security logs
    logger.debug(f"Rate limit exceeded for IP {get_remote_address(request)}")
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "error": "Rate limit exceeded",
            "message": f"Too many requests. Try again in {exc.retry_after} seconds",
            "retry_after": exc.retry_after
        }
    )

# Rate limiting decorators for different endpoints
def auth_rate_limit():
    """Rate limiting for authentication endpoints"""
    return limiter.limit("10 per minute")

def registration_rate_limit():
    """Rate limiting for registration endpoint"""
    return limiter.limit("3 per minute")

def login_rate_limit():
    """Rate limiting for login endpoint"""
    return limiter.limit("5 per minute")

def general_rate_limit():
    """General rate limiting for API endpoints"""
    return limiter.limit("100 per minute")

# Safe rate limiting decorator that won't break if rate limiting fails
def safe_rate_limit(limit_string: str):
    """Safe rate limiting that gracefully handles errors"""
    def decorator(func):
        try:
            # Apply rate limiting
            decorated_func = limiter.limit(limit_string)(func)
            
            # Wrap to handle request parameter properly
            async def wrapper(request: Request, *args, **kwargs):
                try:
                    return await decorated_func(request, *args, **kwargs)
                except Exception as e:
                    logger.debug(f"Rate limiting failed, continuing without limits: {e}")
                    return await func(request, *args, **kwargs)
            return wrapper
        except Exception as e:
            logger.debug(f"Rate limiting setup failed, continuing without limits: {e}")
            return func
    return decorator
