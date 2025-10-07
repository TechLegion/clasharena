import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))

from celery import current_task
from sqlalchemy.orm import Session
from app.core.celery_app import celery_app
from app.core.database import get_db
from shared.models import User, Referral, Wallet, Transaction
import uuid
from decimal import Decimal
from datetime import datetime
import secrets
import string

@celery_app.task(bind=True)
def create_referral_code_task(self, user_id: str):
    """Create a referral code for user"""
    try:
        # Update task status
        self.update_state(state='PROGRESS', meta={'status': 'Creating referral code...'})
        
        # Get database session
        db = next(get_db())
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            db.close()
            return {'success': False, 'error': 'User not found'}
        
        # Check if user already has a referral code
        existing_referral = db.query(Referral).filter(
            Referral.referrer_id == user_id,
            Referral.is_active == True
        ).first()
        
        if existing_referral:
            db.close()
            return {
                'success': True,
                'referral_code': existing_referral.referral_code,
                'message': 'Referral code already exists'
            }
        
        # Generate unique referral code
        referral_code = ''.join(secrets.choices(string.ascii_uppercase + string.digits, k=8))
        
        # Ensure uniqueness
        while db.query(Referral).filter(Referral.referral_code == referral_code).first():
            referral_code = ''.join(secrets.choices(string.ascii_uppercase + string.digits, k=8))
        
        # Create referral record
        referral = Referral(
            id=str(uuid.uuid4()),
            referrer_id=user_id,
            referral_code=referral_code,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        db.add(referral)
        db.commit()
        db.refresh(referral)
        
        db.close()
        
        return {
            'success': True,
            'referral_code': referral_code,
            'referral_id': referral.id
        }
        
    except Exception as e:
        db.close()
        return {'success': False, 'error': str(e)}

@celery_app.task(bind=True)
def use_referral_code_task(self, referral_code: str, referred_user_id: str):
    """Use a referral code for new user"""
    try:
        # Update task status
        self.update_state(state='PROGRESS', meta={'status': 'Processing referral...'})
        
        # Get database session
        db = next(get_db())
        
        # Find active referral code
        referral = db.query(Referral).filter(
            Referral.referral_code == referral_code,
            Referral.is_active == True
        ).first()
        
        if not referral:
            db.close()
            return {'success': False, 'error': 'Invalid or inactive referral code'}
        
        # Check if user is trying to refer themselves
        if referral.referrer_id == referred_user_id:
            db.close()
            return {'success': False, 'error': 'Cannot refer yourself'}
        
        # Check if user already used a referral code
        existing_usage = db.query(Referral).filter(
            Referral.referred_id == referred_user_id
        ).first()
        
        if existing_usage:
            db.close()
            return {'success': False, 'error': 'User has already used a referral code'}
        
        # Update referral record with referred user
        referral.referred_id = referred_user_id
        referral.used_at = datetime.utcnow()
        
        # Update task status
        self.update_state(state='PROGRESS', meta={'status': 'Processing referral bonus...'})
        
        # Give bonus to referrer
        referrer_wallet = db.query(Wallet).filter(Wallet.user_id == referral.referrer_id).first()
        if referrer_wallet:
            bonus_amount = Decimal('100.00')  # $100 referral bonus
            
            # Create bonus transaction for referrer
            referrer_transaction = Transaction(
                id=str(uuid.uuid4()),
                wallet_id=referrer_wallet.id,
                amount=bonus_amount,
                transaction_type="referral_bonus",
                status="completed",
                description=f"Referral bonus for {referral_code}",
                created_at=datetime.utcnow()
            )
            
            db.add(referrer_transaction)
            referrer_wallet.balance += bonus_amount
        
        # Give bonus to referred user
        referred_wallet = db.query(Wallet).filter(Wallet.user_id == referred_user_id).first()
        if referred_wallet:
            welcome_bonus = Decimal('50.00')  # $50 welcome bonus
            
            # Create welcome bonus transaction
            welcome_transaction = Transaction(
                id=str(uuid.uuid4()),
                wallet_id=referred_wallet.id,
                amount=welcome_bonus,
                transaction_type="welcome_bonus",
                status="completed",
                description=f"Welcome bonus from referral {referral_code}",
                created_at=datetime.utcnow()
            )
            
            db.add(welcome_transaction)
            referred_wallet.balance += welcome_bonus
        
        db.commit()
        db.refresh(referral)
        
        db.close()
        
        return {
            'success': True,
            'referral_code': referral_code,
            'referrer_bonus': 100.00,
            'referred_bonus': 50.00,
            'message': 'Referral bonus applied successfully'
        }
        
    except Exception as e:
        db.close()
        return {'success': False, 'error': str(e)}

@celery_app.task(bind=True)
def get_referral_stats_task(self, user_id: str):
    """Get user's referral statistics"""
    try:
        # Get database session
        db = next(get_db())
        
        # Get user's referral code
        referral = db.query(Referral).filter(
            Referral.referrer_id == user_id,
            Referral.is_active == True
        ).first()
        
        if not referral:
            db.close()
            return {'success': False, 'error': 'No referral code found'}
        
        # Count successful referrals
        successful_referrals = db.query(Referral).filter(
            Referral.referrer_id == user_id,
            Referral.referred_id.isnot(None)
        ).count()
        
        # Calculate total earnings from referrals
        referral_transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "referral_bonus"
        ).all()
        
        total_earnings = sum(tx.amount for tx in referral_transactions)
        
        db.close()
        
        return {
            'success': True,
            'referral_code': referral.referral_code,
            'successful_referrals': successful_referrals,
            'total_earnings': float(total_earnings),
            'referral_link': f"https://clasharena.com/register?ref={referral.referral_code}"
        }
        
    except Exception as e:
        db.close()
        return {'success': False, 'error': str(e)}

@celery_app.task(bind=True)
def get_referrals_list_task(self, user_id: str):
    """Get list of users referred by this user"""
    try:
        # Get database session
        db = next(get_db())
        
        # Get all referrals made by this user
        referrals = db.query(Referral).filter(
            Referral.referrer_id == user_id,
            Referral.referred_id.isnot(None)
        ).all()
        
        referral_list = []
        for referral in referrals:
            referred_user = db.query(User).filter(User.id == referral.referred_id).first()
            if referred_user:
                referral_list.append({
                    'referred_user': {
                        'id': referred_user.id,
                        'username': referred_user.username,
                        'email': referred_user.email,
                        'created_at': referred_user.created_at.isoformat() if referred_user.created_at else None
                    },
                    'used_at': referral.used_at.isoformat() if referral.used_at else None
                })
        
        db.close()
        
        return {
            'success': True,
            'referrals': referral_list,
            'count': len(referral_list)
        }
        
    except Exception as e:
        db.close()
        return {'success': False, 'error': str(e)}

