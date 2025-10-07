from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr, Field, validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import secrets
import re
import logging
from typing import Optional
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from shared.database import get_db, init_db
from shared.models import User

app = FastAPI(title="ClashArena Auth Service", version="1.0.0")

# CRITICAL SECURITY: Validate SECRET_KEY configuration
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY or SECRET_KEY == "your-secret-key-here" or len(SECRET_KEY) < 32:
    raise ValueError(
        "SECRET_KEY must be set in environment variables and be at least 32 characters long. "
        "Generate a secure key with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Shorter expiry for better security
REFRESH_TOKEN_EXPIRE_DAYS = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Initialize rate limiting (safe implementation)
try:
    from app.core.rate_limiting import safe_rate_limit, limiter, rate_limit_exceeded_handler
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    rate_limiter = safe_rate_limit
except ImportError:
    # Fallback for standalone service
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    # Simple fallback decorator
    def rate_limiter(limit_string):
        def decorator(func):
            return func  # No rate limiting if setup fails
        return decorator

# Security middleware
app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://clasharena.com", "http://localhost:3000"],  # Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

# Initialize database
init_db()

# Pydantic Models for Request Validation
class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=30, pattern="^[a-zA-Z0-9_-]+$")
    full_name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)
    
    @validator('password')
    def validate_password_strength(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain special character')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        forbidden = ['admin', 'root', 'system', 'null', 'undefined', 'api', 'www']
        if v.lower() in forbidden:
            raise ValueError('Username not allowed')
        return v

class LoginRequest(BaseModel):
    email_or_username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=128)

class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=20)

class GoogleAuthRequest(BaseModel):
    id_token: str = Field(..., min_length=10)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token with proper security"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({
        "exp": expire,
        "type": "access",  # Token type for validation
        "iat": datetime.utcnow()  # Issued at time
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    """Create JWT refresh token"""
    to_encode = {
        "sub": user_id,
        "type": "refresh",
        "exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        "iat": datetime.utcnow()
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get current user with proper JWT validation and security checks"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # CRITICAL: Explicitly specify algorithms and security options
        payload = jwt.decode(
            credentials.credentials, 
            SECRET_KEY, 
            algorithms=["HS256"],  # Only allow specific algorithm
            options={"verify_signature": True, "verify_exp": True}
        )
        
        # Validate token type
        if payload.get("type") != "access":
            raise HTTPException(401, detail="Invalid token type")
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
    except JWTError as e:
        logger.warning(f"JWT validation failed: {str(e)}")
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        logger.warning(f"User not found for JWT: {user_id}")
        raise credentials_exception
    
    if not user.is_active:
        logger.warning(f"Inactive user attempted access: {user_id}")
        raise HTTPException(403, detail="Account is inactive")
    
    return user

@app.get("/")
async def root():
    return {"message": "ClashArena Auth Service", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "auth-service"}

@app.post("/register")
@rate_limiter("3/hour")  # Rate limiting to prevent spam
async def register_user(
    request: Request,
    user_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """Register a new user with proper validation and security"""
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == user_data.email) | (User.username == user_data.username)
        ).first()
        
        if existing_user:
            # Don't reveal which field already exists (prevent enumeration)
            logger.warning(f"Registration attempt with existing email/username")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration failed"
            )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            password_hash=hashed_password,
            is_active=True,
            email_verified=False  # Require email verification
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Create tokens
        access_token = create_access_token(data={"sub": new_user.id})
        refresh_token = create_refresh_token(new_user.id)
        
        logger.info(f"User registered successfully: {new_user.id}")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": new_user.id,
                "email": new_user.email,
                "username": new_user.username,
                "full_name": new_user.full_name,
                "is_active": new_user.is_active,
                "email_verified": new_user.email_verified
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Registration error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Registration failed"
        )

@app.post("/login")
@rate_limiter("5/minute")  # Rate limiting to prevent brute force
async def login_user(
    request: Request,
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login user with timing attack protection and rate limiting"""
    try:
        # Look up user
        user = db.query(User).filter(
            (User.email == credentials.email_or_username) | 
            (User.username == credentials.email_or_username)
        ).first()
        
        # CRITICAL: Always hash password to prevent timing attacks
        if not user or not user.password_hash:
            pwd_context.hash("dummy_password_for_timing_protection")
            logger.warning(f"Login attempt for non-existent user")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Verify password
        if not verify_password(credentials.password, user.password_hash):
            logger.warning(f"Failed login attempt for user: {user.id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        if not user.is_active:
            logger.warning(f"Inactive user attempted login: {user.id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )
        
        # Create tokens
        access_token = create_access_token(data={"sub": user.id})
        refresh_token = create_refresh_token(user.id)
        
        logger.info(f"User logged in successfully: {user.id}")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "email_verified": user.email_verified
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Login failed"
        )

@app.post("/refresh")
@rate_limiter("10/minute")  # Rate limiting for refresh tokens
async def refresh_token(
    request: Request,
    token_data: RefreshRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token with proper validation"""
    try:
        # CRITICAL: Validate refresh token with proper security options
        payload = jwt.decode(
            token_data.refresh_token, 
            SECRET_KEY, 
            algorithms=["HS256"],  # Only allow specific algorithm
            options={"verify_signature": True, "verify_exp": True}
        )
        
        # Validate token type
        if payload.get("type") != "refresh":
            raise HTTPException(401, detail="Invalid token type")
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(401, detail="Invalid refresh token")
        
        # Verify user still exists and is active
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(401, detail="User not found or inactive")
        
        # Create new access token
        access_token = create_access_token(data={"sub": user_id})
        
        logger.info(f"Token refreshed for user: {user_id}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except JWTError as e:
        logger.warning(f"Invalid refresh token: {str(e)}")
        raise HTTPException(401, detail="Invalid refresh token")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Refresh token error: {str(e)}", exc_info=True)
        raise HTTPException(500, detail="Token refresh failed")

@app.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "is_admin": current_user.is_admin,
        "created_at": current_user.created_at
    }

@app.post("/google-auth")
async def google_auth(google_token: dict, db: Session = Depends(get_db)):
    """Authenticate with Google"""
    try:
        # Verify Google token with Google API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://www.googleapis.com/oauth2/v1/userinfo?access_token={google_token['access_token']}"
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Google token"
                )
            
            google_user = response.json()
            
            # Check if user exists
            user = db.query(User).filter(User.email == google_user["email"]).first()
            
            if not user:
                # Create new user
                user = User(
                    email=google_user["email"],
                    username=google_user["email"].split("@")[0],
                    full_name=google_user["name"],
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user.id}, expires_delta=access_token_expires
            )
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "full_name": user.full_name,
                    "is_active": user.is_active
                }
            }
            
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.post("/facebook-auth")
async def facebook_auth(facebook_token: dict, db: Session = Depends(get_db)):
    """Authenticate with Facebook"""
    try:
        # Verify Facebook token with Facebook API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://graph.facebook.com/me?access_token={facebook_token['access_token']}&fields=id,name,email"
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Facebook token"
                )
            
            facebook_user = response.json()
            
            # Check if user exists
            user = db.query(User).filter(User.email == facebook_user["email"]).first()
            
            if not user:
                # Create new user
                user = User(
                    email=facebook_user["email"],
                    username=facebook_user["name"].replace(" ", "_").lower(),
                    full_name=facebook_user["name"],
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user.id}, expires_delta=access_token_expires
            )
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "full_name": user.full_name,
                    "is_active": user.is_active
                }
            }
            
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
