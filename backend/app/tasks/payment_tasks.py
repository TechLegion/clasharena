"""
Celery tasks for payment processing
"""
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))

from celery import current_task
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
import uuid
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

from app.core.celery_app import celery_app
from app.core.database import get_db
from app.services.paystack import paystack_service
from shared.models import User, Wallet, Transaction


@celery_app.task(bind=True)
def initialize_deposit_task(self, user_id: str, amount: float, email: str):
    """Initialize a deposit transaction with Paystack"""
    try:
        # Update task status
        self.update_state(state='PROGRESS', meta={'status': 'Initializing payment...'})
        
        # Get database session
        db = next(get_db())
        
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            db.close()
            return {'success': False, 'error': 'User not found'}
        
        # Verify user has wallet
        wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
        if not wallet:
            db.close()
            return {'success': False, 'error': 'Wallet not found'}
        
        # Generate unique reference with idempotency protection
        reference = f"deposit_{user_id}_{uuid.uuid4().hex[:8]}"
        
        # Check for duplicate transaction (idempotency protection)
        existing_transaction = db.query(Transaction).filter(
            Transaction.reference == reference
        ).first()
        
        if existing_transaction:
            db.close()
            return {
                'success': False, 
                'error': 'Duplicate transaction detected',
                'transaction_id': existing_transaction.id,
                'reference': reference
            }
        
        # Create transaction record - DO NOT update balance yet!
        # Balance will only be updated via webhook verification
        transaction = Transaction(
            id=str(uuid.uuid4()),
            wallet_id=wallet.id,
            transaction_type='deposit',
            amount=Decimal(str(amount)),
            status='pending',
            description=f'Deposit via Paystack - Awaiting payment confirmation',
            reference=reference,
            external_reference=reference  # Paystack reference
        )
        
        db.add(transaction)
        db.commit()
        
        # Update task status
        self.update_state(state='PROGRESS', meta={'status': 'Creating payment link...'})
        
        # Initialize Paystack transaction
        paystack_response = paystack_service.initialize_transaction(
            email=email,
            amount=amount,
            reference=reference,
            metadata={
                'user_id': user_id,
                'transaction_id': transaction.id
            }
        )
        
        if not paystack_response.get('status'):
            transaction.status = 'failed'
            transaction.metadata['error'] = paystack_response.get('message', 'Payment initialization failed')
            db.commit()
            db.close()
            return {'success': False, 'error': paystack_response.get('message', 'Payment initialization failed')}
        
        # Update transaction with Paystack reference (store in description or external_reference)
        transaction.external_reference = paystack_response['data']['reference']
        transaction.description = f'Deposit via Paystack - Access Code: {paystack_response["data"]["access_code"]}'
        db.commit()
        
        db.close()
        
        logger.info(
            f"Deposit initialized successfully: {reference}",
            extra={
                "user_id": user_id,
                "amount": amount,
                "transaction_id": transaction.id,
                "reference": reference
            }
        )
        
        return {
            'success': True,
            'authorization_url': paystack_response['data']['authorization_url'],
            'access_code': paystack_response['data']['access_code'],
            'reference': reference,
            'transaction_id': transaction.id
        }
        
    except Exception as e:
        db.close()
        return {'success': False, 'error': str(e)}


@celery_app.task(bind=True)
def verify_deposit_task(self, reference: str):
    """Verify a deposit transaction with Paystack"""
    try:
        # Update task status
        self.update_state(state='PROGRESS', meta={'status': 'Verifying payment...'})
        
        # Get database session
        db = next(get_db())
        
        # Find transaction by reference or external_reference
        transaction = db.query(Transaction).filter(
            (Transaction.reference == reference) | (Transaction.external_reference == reference)
        ).first()
        if not transaction:
            db.close()
            return {'success': False, 'error': 'Transaction not found'}
        
        if transaction.status != 'pending':
            db.close()
            return {'success': False, 'error': f'Transaction already {transaction.status}'}
        
        # Verify with Paystack
        paystack_response = paystack_service.verify_transaction(reference)
        
        if not paystack_response.get('status'):
            transaction.status = 'failed'
            transaction.description += f" - Error: {paystack_response.get('message', 'Payment verification failed')}"
            db.commit()
            db.close()
            return {'success': False, 'error': paystack_response.get('message', 'Payment verification failed')}
        
        transaction_data = paystack_response['data']
        
        # Check if transaction was successful
        if transaction_data['status'] == 'success':
            # Update transaction status
            transaction.status = 'completed'
            transaction.updated_at = datetime.utcnow()
            
            # Credit user's wallet using atomic operation (thread-safe)
            wallet = transaction.wallet
            if wallet:
                # Use atomic update to prevent race conditions
                result = db.query(Wallet).filter(
                    Wallet.id == wallet.id
                ).update({
                    Wallet.balance: Wallet.balance + transaction.amount,
                    Wallet.updated_at: datetime.utcnow()
                })
                
                if result == 0:
                    logger.error(f"Failed to update wallet balance for wallet: {wallet.id}")
                    db.close()
                    return {'success': False, 'error': 'Failed to update wallet balance'}
            
            db.commit()
            db.close()
            
            return {
                'success': True,
                'transaction_id': transaction.id,
                'amount': float(transaction.amount),
                'new_balance': float(wallet.balance) if wallet else 0
            }
        else:
            # Transaction failed
            transaction.status = 'failed'
            transaction.description += f" - Failed: {transaction_data.get('gateway_response', 'Unknown error')}"
            db.commit()
            db.close()
            
            return {
                'success': False,
                'error': f'Payment failed: {transaction_data.get("gateway_response", "Unknown error")}'
            }
        
    except Exception as e:
        db.close()
        return {'success': False, 'error': str(e)}


@celery_app.task(bind=True)
def create_withdrawal_task(self, user_id: str, amount: float, account_details: dict):
    """Create a withdrawal request"""
    try:
        # Update task status
        self.update_state(state='PROGRESS', meta={'status': 'Processing withdrawal...'})
        
        # Get database session
        db = next(get_db())
        
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            db.close()
            return {'success': False, 'error': 'User not found'}
        
        # Check wallet balance
        wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
        if not wallet:
            db.close()
            return {'success': False, 'error': 'Wallet not found'}
        
        if wallet.balance < Decimal(str(amount)):
            db.close()
            return {'success': False, 'error': 'Insufficient balance'}
        
        # Generate unique reference
        reference = f"withdrawal_{user_id}_{uuid.uuid4().hex[:8]}"
        
        # Create transaction record
        transaction = Transaction(
            id=str(uuid.uuid4()),
            wallet_id=wallet.id,
            transaction_type='withdrawal',
            amount=Decimal(str(amount)),
            status='pending',
            description=f'Withdrawal to {account_details.get("account_name", "Bank Account")}',
            reference=reference,
            external_reference=reference
        )
        
        db.add(transaction)
        
        # Reserve amount from wallet using atomic operation with balance check
        result = db.query(Wallet).filter(
            Wallet.id == wallet.id,
            Wallet.balance >= Decimal(str(amount))
        ).update({
            Wallet.balance: Wallet.balance - Decimal(str(amount)),
            Wallet.updated_at: datetime.utcnow()
        })
        
        if result == 0:
            db.close()
            logger.warning(f"Insufficient balance for withdrawal: user {user_id}, amount {amount}")
            return {'success': False, 'error': 'Insufficient balance'}
        
        db.commit()
        db.refresh(transaction)
        
        db.close()
        
        return {
            'success': True,
            'transaction_id': transaction.id,
            'reference': reference,
            'amount': amount,
            'new_balance': float(wallet.balance)
        }
        
    except Exception as e:
        db.close()
        return {'success': False, 'error': str(e)}


@celery_app.task(bind=True)
def process_withdrawal_task(self, transaction_id: str):
    """Process a withdrawal transaction"""
    try:
        # Update task status
        self.update_state(state='PROGRESS', meta={'status': 'Processing withdrawal...'})
        
        # Get database session
        db = next(get_db())
        
        # Find transaction
        transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not transaction:
            db.close()
            return {'success': False, 'error': 'Transaction not found'}
        
        if transaction.transaction_type != 'withdrawal':
            db.close()
            return {'success': False, 'error': 'Invalid transaction type'}
        
        if transaction.status != 'pending':
            db.close()
            return {'success': False, 'error': f'Transaction already {transaction.status}'}
        
        # Get account details from description (we'll need to store this differently)
        # For now, let's assume we have the account details from the withdrawal request
        # TODO: Store account details in a separate field or table
        account_details = {
            'account_number': '1234567890',  # This should come from the withdrawal request
            'bank_code': '058',  # This should come from the withdrawal request  
            'account_name': 'Test Account'  # This should come from the withdrawal request
        }
        
        # Create transfer recipient
        recipient_response = paystack_service.create_transfer_recipient(
            account_number=account_details['account_number'],
            bank_code=account_details['bank_code'],
            account_name=account_details['account_name'],
            email=transaction.wallet.user.email
        )
        
        if not recipient_response.get('status'):
            # Refund the amount back to wallet
            wallet = transaction.wallet
            if wallet:
                wallet.balance += transaction.amount
                wallet.updated_at = datetime.utcnow()
            
            transaction.status = 'failed'
            transaction.description += f" - Error: {recipient_response.get('message', 'Failed to create recipient')}"
            db.commit()
            db.close()
            
            return {'success': False, 'error': recipient_response.get('message', 'Failed to create recipient')}
        
        recipient_code = recipient_response['data']['recipient_code']
        
        # Update task status
        self.update_state(state='PROGRESS', meta={'status': 'Initiating transfer...'})
        
        # Initiate transfer
        transfer_response = paystack_service.initiate_transfer(
            amount=float(transaction.amount),
            recipient_code=recipient_code,
            reference=transaction.reference,
            reason=f"Withdrawal for {transaction.wallet.user.username}"
        )
        
        if not transfer_response.get('status'):
            # Refund the amount back to wallet
            wallet = transaction.wallet
            if wallet:
                wallet.balance += transaction.amount
                wallet.updated_at = datetime.utcnow()
            
            transaction.status = 'failed'
            transaction.description += f" - Transfer Error: {transfer_response.get('message', 'Transfer failed')}"
            db.commit()
            db.close()
            
            return {'success': False, 'error': transfer_response.get('message', 'Transfer failed')}
        
        # Update transaction status
        transaction.status = 'completed'
        transaction.updated_at = datetime.utcnow()
        transaction.description += f" - Transfer Code: {transfer_response['data'].get('transfer_code', 'N/A')}"
        
        db.commit()
        db.close()
        
        return {
            'success': True,
            'transaction_id': transaction.id,
            'transfer_code': transfer_response['data']['transfer_code']
        }
        
    except Exception as e:
        db.close()
        return {'success': False, 'error': str(e)}


@celery_app.task(bind=True)
def get_transaction_history_task(self, user_id: str, page: int = 1, limit: int = 20):
    """Get user's transaction history"""
    try:
        # Get database session
        db = next(get_db())
        
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            db.close()
            return {'success': False, 'error': 'User not found'}
        
        # Get user's wallet first
        wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
        if not wallet:
            db.close()
            return {'success': False, 'error': 'Wallet not found'}
        
        # Get transactions with pagination
        offset = (page - 1) * limit
        transactions = db.query(Transaction).filter(
            Transaction.wallet_id == wallet.id
        ).order_by(Transaction.created_at.desc()).offset(offset).limit(limit).all()
        
        # Get total count
        total_count = db.query(Transaction).filter(Transaction.wallet_id == wallet.id).count()
        
        db.close()
        
        transaction_list = []
        for transaction in transactions:
            transaction_list.append({
                'id': transaction.id,
                'type': transaction.transaction_type,
                'amount': float(transaction.amount),
                'status': transaction.status,
                'description': transaction.description,
                'reference': transaction.reference,
                'created_at': transaction.created_at.isoformat() if transaction.created_at else None,
                'updated_at': transaction.updated_at.isoformat() if transaction.updated_at else None
            })
        
        return {
            'success': True,
            'transactions': transaction_list,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_count,
                'pages': (total_count + limit - 1) // limit
            }
        }
        
    except Exception as e:
        db.close()
        return {'success': False, 'error': str(e)}

