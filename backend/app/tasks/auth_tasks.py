import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))

from celery import current_task
from sqlalchemy.orm import Session
from app.core.celery_app import celery_app
from app.core.database import get_db
from app.core.security import get_password_hash, create_access_token
from shared.models import User, Wallet
import uuid

@celery_app.task(bind=True)
def create_user_task(self, user_data: dict):
    """Create a new user and their wallet"""
    try:
        # Update task status
        self.update_state(state='PROGRESS', meta={'status': 'Creating user...'})
        
        # Get database session
        db = next(get_db())
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data['email']).first()
        if existing_user:
            return {'success': False, 'error': 'User already exists'}
        
        # Create user
        user = User(
            id=str(uuid.uuid4()),
            username=user_data['username'],
            email=user_data['email'],
            full_name=user_data['full_name'],
            password_hash=get_password_hash(user_data['password']),
            is_active=True,
            is_admin=False
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Update task status
        self.update_state(state='PROGRESS', meta={'status': 'Creating wallet...'})
        
        # Create wallet for user
        wallet = Wallet(
            id=str(uuid.uuid4()),
            user_id=user.id,
            balance=0.0
        )
        
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
        
        # Create access token
        access_token = create_access_token(subject=user.id)
        
        db.close()
        
        return {
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'is_active': user.is_active,
                'is_admin': user.is_admin
            },
            'access_token': access_token,
            'token_type': 'bearer'
        }
        
    except Exception as e:
        db.close()
        return {'success': False, 'error': str(e)}

@celery_app.task(bind=True)
def authenticate_user_task(self, email_or_username: str, password: str):
    """Authenticate user and return token"""
    try:
        # Update task status
        self.update_state(state='PROGRESS', meta={'status': 'Authenticating user...'})
        
        # Get database session
        db = next(get_db())
        
        # Find user by email or username
        user = db.query(User).filter(
            (User.email == email_or_username) | 
            (User.username == email_or_username)
        ).first()
        if not user:
            db.close()
            return {'success': False, 'error': 'Invalid credentials'}
        
        # Verify password
        from app.core.security import verify_password
        if not verify_password(password, user.password_hash):
            db.close()
            return {'success': False, 'error': 'Invalid credentials'}
        
        # Create access token
        access_token = create_access_token(subject=user.id)
        
        db.close()
        
        return {
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'is_active': user.is_active,
                'is_admin': user.is_admin
            },
            'access_token': access_token,
            'token_type': 'bearer'
        }
        
    except Exception as e:
        db.close()
        return {'success': False, 'error': str(e)}

@celery_app.task(bind=True)
def get_user_task(self, user_id: str):
    """Get user by ID"""
    try:
        # Get database session
        db = next(get_db())
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            db.close()
            return {'success': False, 'error': 'User not found'}
        
        db.close()
        
        return {
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'is_active': user.is_active,
                'is_admin': user.is_admin,
                'created_at': user.created_at.isoformat() if user.created_at else None
            }
        }
        
    except Exception as e:
        db.close()
        return {'success': False, 'error': str(e)}
