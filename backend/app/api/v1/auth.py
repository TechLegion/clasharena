from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
# Removed unused Celery task imports
from app.core.rate_limiting import safe_rate_limit, registration_rate_limit, login_rate_limit
from app.core.database import get_db
from shared.models import User
import sys
import os
import logging
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))

# Create logger for this module
logger = logging.getLogger(__name__)

router = APIRouter()

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: str
    password: str

class TaskResponse(BaseModel):
    task_id: str
    status: str

@router.post("/register")
@safe_rate_limit(registration_rate_limit)
async def register_user(user: UserRegister, db: Session = Depends(get_db)):
    """Register a new user (synchronous)"""
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == user.email) | (User.username == user.username)
        ).first()
        
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Check if this is the first user (make them admin)
        existing_users = db.query(User).count()
        is_first_user = existing_users == 0
        
        # Create user
        from app.core.security import get_password_hash, create_access_token
        hashed_password = get_password_hash(user.password)
        new_user = User(
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            password_hash=hashed_password,
            is_active=True,
            is_admin=is_first_user  # First user becomes admin automatically
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Create wallet for user
        from shared.models import Wallet
        wallet = Wallet(user_id=new_user.id, balance=0.0)
        db.add(wallet)
        db.commit()
        
        # Create access token
        access_token = create_access_token(subject=new_user.id)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": new_user.id,
                "email": new_user.email,
                "username": new_user.username,
                "full_name": new_user.full_name,
                "is_active": new_user.is_active,
                "is_admin": new_user.is_admin
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/login-direct")
# @safe_rate_limit(login_rate_limit)  # Temporarily disabled for debugging
async def login_user(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user (synchronous)"""
    logger.info(f"Login request received for: {credentials.email}")
    try:
        # Look up user by email
        user = db.query(User).filter(User.email == credentials.email).first()
        
        if not user or not user.password_hash:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Verify password
        from app.core.security import verify_password
        if not verify_password(credentials.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is inactive")
        
        # Create access token
        from app.core.security import create_access_token
        access_token = create_access_token(subject=user.id)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_admin": user.is_admin
            }
        }
    except HTTPException as he:
        logger.error(f"HTTP Exception in login: {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@router.get("/test")
async def test_endpoint(db: Session = Depends(get_db)):
    """Test endpoint to verify database connection"""
    try:
        user_count = db.query(User).count()
        return {"status": "success", "user_count": user_count}
    except Exception as e:
        logger.error(f"Test endpoint error: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}

@router.get("/me", response_model=TaskResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user info (async)"""
    task = get_user_task.delay(current_user.id)
    return TaskResponse(task_id=task.id, status="queued")