import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))

from celery import current_task
from sqlalchemy.orm import Session
from app.core.celery_app import celery_app
from app.core.database import get_db
from shared.models import User, Wallet, Transaction
import uuid
from decimal import Decimal
from datetime import datetime

@celery_app.task(bind=True)
def get_wallet_balance_task(self, user_id: str):
    """Get user's wallet balance"""
    try:
        # Get database session
        db = next(get_db())
        
        wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
        if not wallet:
            db.close()
            return {'success': False, 'error': 'Wallet not found'}
        
        db.close()
        
        return {
            'success': True,
            'balance': float(wallet.balance),
            'wallet_id': wallet.id
        }
        
    except Exception as e:
        db.close()
        return {'success': False, 'error': str(e)}

@celery_app.task(bind=True)
def deposit_funds_task(self, user_id: str, amount: float, payment_method: str = "manual"):
    """Deposit funds to user's wallet"""
    try:
        # Update task status
        self.update_state(state='PROGRESS', meta={'status': 'Processing deposit...'})
        
        # Get database session
        db = next(get_db())
        
        wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
        if not wallet:
            db.close()
            return {'success': False, 'error': 'Wallet not found'}
        
        # Create transaction record
        transaction = Transaction(
            id=str(uuid.uuid4()),
            wallet_id=wallet.id,
            amount=Decimal(str(amount)),
            transaction_type="deposit",
            status="pending",
            description=f"Deposit via {payment_method}",
            created_at=datetime.utcnow()
        )
        
        db.add(transaction)
        
        # Update task status
        self.update_state(state='PROGRESS', meta={'status': 'Updating balance...'})
        
        # Update wallet balance
        wallet.balance += Decimal(str(amount))
        
        # Update transaction status
        transaction.status = "completed"
        
        db.commit()
        db.refresh(wallet)
        db.refresh(transaction)
        
        db.close()
        
        return {
            'success': True,
            'new_balance': float(wallet.balance),
            'transaction_id': transaction.id,
            'amount': amount
        }
        
    except Exception as e:
        db.close()
        return {'success': False, 'error': str(e)}

@celery_app.task(bind=True)
def withdraw_funds_task(self, user_id: str, amount: float, payment_method: str = "manual"):
    """Withdraw funds from user's wallet"""
    try:
        # Update task status
        self.update_state(state='PROGRESS', meta={'status': 'Processing withdrawal...'})
        
        # Get database session
        db = next(get_db())
        
        wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
        if not wallet:
            db.close()
            return {'success': False, 'error': 'Wallet not found'}
        
        # Check sufficient balance
        if wallet.balance < Decimal(str(amount)):
            db.close()
            return {'success': False, 'error': 'Insufficient balance'}
        
        # Create transaction record
        transaction = Transaction(
            id=str(uuid.uuid4()),
            wallet_id=wallet.id,
            amount=-Decimal(str(amount)),  # Negative for withdrawal
            transaction_type="withdrawal",
            status="pending",
            description=f"Withdrawal via {payment_method}",
            created_at=datetime.utcnow()
        )
        
        db.add(transaction)
        
        # Update task status
        self.update_state(state='PROGRESS', meta={'status': 'Updating balance...'})
        
        # Update wallet balance
        wallet.balance -= Decimal(str(amount))
        
        # Update transaction status
        transaction.status = "completed"
        
        db.commit()
        db.refresh(wallet)
        db.refresh(transaction)
        
        db.close()
        
        return {
            'success': True,
            'new_balance': float(wallet.balance),
            'transaction_id': transaction.id,
            'amount': amount
        }
        
    except Exception as e:
        db.close()
        return {'success': False, 'error': str(e)}

@celery_app.task(bind=True)
def get_transactions_task(self, user_id: str, limit: int = 50):
    """Get user's transaction history"""
    try:
        # Get database session
        db = next(get_db())
        
        transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id
        ).order_by(Transaction.created_at.desc()).limit(limit).all()
        
        db.close()
        
        transaction_list = []
        for tx in transactions:
            transaction_list.append({
                'id': tx.id,
                'amount': float(tx.amount),
                'transaction_type': tx.transaction_type,
                'status': tx.status,
                'description': tx.description,
                'created_at': tx.created_at.isoformat() if tx.created_at else None
            })
        
        return {
            'success': True,
            'transactions': transaction_list,
            'count': len(transaction_list)
        }
        
    except Exception as e:
        db.close()
        return {'success': False, 'error': str(e)}

