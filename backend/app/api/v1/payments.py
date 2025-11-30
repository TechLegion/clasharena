"""
Payment API endpoints for deposits and withdrawals
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, List
import json
import logging

logger = logging.getLogger(__name__)

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.core.config import settings
from sqlalchemy.orm import Session
from app.services.paystack import paystack_service
from shared.models import User

router = APIRouter()


class DepositRequest(BaseModel):
    amount: float = Field(..., ge=100, le=1000000, description="Amount in NGN")
    email: EmailStr


class WithdrawalRequest(BaseModel):
    amount: float = Field(..., ge=500, le=500000, description="Amount in NGN")
    account_number: str = Field(..., pattern=r'^\d{10}$', description="10-digit account number")
    bank_code: str = Field(..., min_length=3, max_length=10, description="Bank code from Paystack")
    account_name: str = Field(..., min_length=2, max_length=100, description="Account holder name")


class VerifyDepositRequest(BaseModel):
    reference: str = Field(..., min_length=1, max_length=100, description="Transaction reference to verify")


class ValidateAccountRequest(BaseModel):
    account_number: str = Field(..., pattern=r'^\d{10}$', description="10-digit account number")
    bank_code: str = Field(..., min_length=3, max_length=10, description="Bank code")


class TaskResponse(BaseModel):
    task_id: str
    status: str


class BulkPaymentRecipient(BaseModel):
    user_id: str = Field(..., description="User ID to send payment to")
    amount: float = Field(..., gt=0, le=500000, description="Amount to send (max ₦500,000)")
    reason: str = Field(..., min_length=1, max_length=200, description="Reason for payment")
    account_number: str = Field(..., pattern=r'^\d{10}$', description="10-digit account number")
    bank_code: str = Field(..., min_length=3, max_length=10, description="Bank code")
    account_name: str = Field(..., min_length=2, max_length=100, description="Account holder name")


class BulkPaymentRequest(BaseModel):
    recipients: List[BulkPaymentRecipient] = Field(..., min_items=1, max_items=100, description="List of recipients")
    description: str = Field(..., min_length=1, max_length=200, description="Overall description for bulk payment")
    notify_recipients: bool = Field(default=True, description="Whether to notify recipients via SMS/email")


class BulkPaymentStatus(BaseModel):
    id: str
    status: str
    total_amount: float
    total_recipients: int
    successful_count: int
    failed_count: int
    created_at: str
    description: str


@router.post("/deposit/initialize")
async def initialize_deposit(
    deposit_data: DepositRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Initialize a deposit transaction with Paystack"""
    logger.info(f"Deposit initialization request from user: {current_user.id}")
    
    try:
        # Check if Paystack is configured
        if not settings.PAYSTACK_SECRET_KEY or settings.PAYSTACK_SECRET_KEY.strip() == "":
            logger.error("Paystack secret key is not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Payment service is not configured. Please contact support."
            )
        
        # Get user's wallet
        from shared.models import Wallet
        wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        
        # Initialize Paystack payment
        import httpx
        import uuid
        
        reference = f"dep_{uuid.uuid4()}"
        
        # Validate secret key before making request
        secret_key = settings.PAYSTACK_SECRET_KEY.strip()
        if not secret_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Payment service configuration error"
            )
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.paystack.co/transaction/initialize",
                headers={
                    "Authorization": f"Bearer {secret_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "email": deposit_data.email,
                    "amount": int(deposit_data.amount * 100),  # Convert to kobo
                    "reference": reference,
                    "callback_url": f"{settings.FRONTEND_URL}/dashboard"
                }
            )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "status": "success",
                "message": "Payment initialized successfully",
                "authorization_url": result["data"]["authorization_url"],
                "reference": reference,
                "access_code": result["data"]["access_code"]
            }
        else:
            logger.error(f"Paystack initialization failed: {response.status_code}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment initialization failed"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deposit initialization error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Deposit initialization failed. Please try again."
        )


@router.post("/deposit/verify")
async def verify_deposit(
    verify_data: VerifyDepositRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Verify a deposit transaction with proper transaction handling"""
    try:
        import httpx
        from sqlalchemy.exc import IntegrityError
        
        # Check if Paystack is configured
        if not settings.PAYSTACK_SECRET_KEY or settings.PAYSTACK_SECRET_KEY.strip() == "":
            logger.error("Paystack secret key is not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Payment service is not configured. Please contact support."
            )
        
        # Verify with Paystack first
        secret_key = settings.PAYSTACK_SECRET_KEY.strip()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"https://api.paystack.co/transaction/verify/{verify_data.reference}",
                headers={
                    "Authorization": f"Bearer {secret_key}",
                    "Content-Type": "application/json"
                }
            )
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to verify transaction")
        
        result = response.json()
        
        if result["data"]["status"] != "success":
            return {
                "status": "failed",
                "message": "Payment not successful"
            }
        
        # Use database transaction for atomicity
        from shared.models import Wallet, Transaction
        
        try:
            # Start transaction with row locking
            wallet = db.query(Wallet).filter(
                Wallet.user_id == current_user.id
            ).with_for_update().first()
            
            if not wallet:
                raise HTTPException(status_code=404, detail="Wallet not found")
            
            amount = result["data"]["amount"] / 100
            
            # Create transaction record (unique constraint will prevent duplicates)
            transaction = Transaction(
                wallet_id=wallet.id,
                amount=amount,
                transaction_type="deposit",
                status="completed",
                reference=verify_data.reference,
                external_reference=result["data"]["reference"],
                description=f"Deposit via Paystack"
            )
            db.add(transaction)
            
            # Update wallet balance
            wallet.balance += amount
            
            # Commit all changes atomically
            db.commit()
            db.refresh(wallet)
            
            logger.info(f"Deposit verified: {amount} for user {current_user.id}")
            
            return {
                "status": "success",
                "message": f"Deposit of ₦{amount:,.2f} credited successfully",
                "amount": amount,
                "balance": wallet.balance
            }
            
        except IntegrityError:
            db.rollback()
            return {
                "status": "already_credited",
                "message": "Transaction already processed"
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Database error during deposit verification: {type(e).__name__}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Verification failed. Please contact support."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deposit verification error: {type(e).__name__}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Verification failed. Please contact support."
        )


@router.post("/withdrawal/request")
async def request_withdrawal(
    withdrawal_data: WithdrawalRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Request a withdrawal to bank account"""
    try:
        from shared.models import Wallet
        
        # Get wallet with lock
        wallet = db.query(Wallet).filter(
            Wallet.user_id == current_user.id
        ).with_for_update().first()
        
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        
        # Check sufficient balance
        if wallet.balance < withdrawal_data.amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient balance. Available: ₦{wallet.balance:,.2f}"
            )
        
        # TODO: Implement Paystack transfer
        # For now, return not implemented
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Withdrawal processing not yet implemented"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Withdrawal request error: {type(e).__name__}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Withdrawal request failed. Please try again."
        )


@router.get("/banks")
async def get_banks():
    """Get list of Nigerian banks for account validation"""
    try:
        banks_response = paystack_service.get_banks()
        
        if not banks_response.get('status'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch banks"
            )
        
        return {
            "success": True,
            "banks": banks_response['data']
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching banks: {type(e).__name__}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch banks. Please try again."
        )


@router.get("/banks/flutterwave")
async def get_banks_flutterwave():
    """Get list of Nigerian banks from Flutterwave (for bulk payments)"""
    try:
        from app.services.flutterwave import flutterwave_service
        
        banks_response = await flutterwave_service.get_banks()
        
        if not banks_response.get('status'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch banks from Flutterwave"
            )
        
        return {
            "success": True,
            "banks": banks_response['data']
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Flutterwave banks: {type(e).__name__}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch banks from Flutterwave. Please try again."
        )


@router.post("/validate-account/flutterwave")
async def validate_account_flutterwave(
    request: ValidateAccountRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Validate bank account number using Flutterwave"""
    try:
        from app.services.flutterwave import flutterwave_service
        
        account_response = await flutterwave_service.resolve_account_number(
            request.account_number, 
            request.bank_code
        )
        
        if not account_response.get('status'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid account number or bank code"
            )
        
        return {
            "success": True,
            "account_name": account_response['data']['account_name'],
            "account_number": account_response['data']['account_number'],
            "bank_code": account_response['data']['bank_code']
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Flutterwave account validation error: {type(e).__name__}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Account validation failed. Please try again."
        )


@router.post("/validate-account")
async def validate_account_number(
    request: ValidateAccountRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Validate bank account number and get account name"""
    try:
        account_response = paystack_service.resolve_account_number(
            request.account_number, 
            request.bank_code
        )
        
        if not account_response.get('status'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid account number or bank code"
            )
        
        return {
            "success": True,
            "account_name": account_response['data']['account_name'],
            "account_number": account_response['data']['account_number'],
            "bank_code": account_response['data']['bank_code']
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Account validation error: {type(e).__name__}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Account validation failed. Please try again."
        )


@router.get("/transactions")
async def get_transaction_history(
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's transaction history"""
    try:
        from shared.models import Wallet, Transaction
        
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 20
        
        # Get user's wallet
        wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        
        # Get transactions with pagination
        offset = (page - 1) * limit
        transactions = db.query(Transaction).filter(
            Transaction.wallet_id == wallet.id
        ).order_by(Transaction.created_at.desc()).offset(offset).limit(limit).all()
        
        # Get total count
        total = db.query(Transaction).filter(Transaction.wallet_id == wallet.id).count()
        
        return {
            "success": True,
            "transactions": [
                {
                    "id": t.id,
                    "amount": t.amount,
                    "type": t.transaction_type,
                    "status": t.status,
                    "reference": t.reference,
                    "description": t.description,
                    "created_at": t.created_at.isoformat()
                }
                for t in transactions
            ],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transaction history error: {type(e).__name__}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch transaction history."
        )


@router.post("/webhook/paystack")
async def paystack_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Paystack webhook notifications with proper signature verification"""
    try:
        # Get the raw body
        body = await request.body()
        
        # Enhanced logging for webhook debugging
        logger.info(f"Webhook received from IP: {request.client.host}")
        logger.info(f"Webhook headers: {dict(request.headers)}")
        logger.info(f"Webhook body length: {len(body)} bytes")
        
        # Get the signature header
        signature = request.headers.get('x-paystack-signature')
        if not signature:
            logger.warning("Webhook received without signature")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing webhook signature"
            )
        
        # Verify webhook signature (CRITICAL SECURITY CHECK)
        if not paystack_service.verify_webhook_signature(body.decode('utf-8'), signature):
            logger.error("Invalid webhook signature received")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )
        
        # Parse webhook data
        webhook_data = json.loads(body.decode('utf-8'))
        event_type = webhook_data.get('event')
        
        logger.info(f"Webhook received: {event_type}")
        
        if event_type == 'charge.success':
            # Handle successful payment
            transaction_data = webhook_data.get('data', {})
            reference = transaction_data.get('reference')
            
            if reference:
                # Check for idempotency - has this webhook been processed?
                from shared.models import Transaction, Wallet
                existing = db.query(Transaction).filter(
                    Transaction.reference == reference
                ).first()
                
                if existing:
                    logger.info(f"Webhook for {reference} already processed")
                    return {"status": "success", "message": "already_processed"}
                
                logger.info(f"Processing new payment webhook: {reference}")
                
                # Get the user from the transaction data
                customer_email = transaction_data.get('customer', {}).get('email')
                if not customer_email:
                    logger.error(f"No customer email in webhook for {reference}")
                    return {"status": "error", "message": "no_customer_email"}
                
                # Find user by email
                from shared.models import User
                user = db.query(User).filter(User.email == customer_email).first()
                if not user:
                    logger.error(f"User not found for email: {customer_email}")
                    return {"status": "error", "message": "user_not_found"}
                
                # Get user's wallet with lock
                wallet = db.query(Wallet).filter(
                    Wallet.user_id == user.id
                ).with_for_update().first()
                
                if not wallet:
                    logger.error(f"Wallet not found for user: {user.id}")
                    return {"status": "error", "message": "wallet_not_found"}
                
                # Process the payment
                try:
                    amount = transaction_data.get('amount', 0) / 100  # Convert from kobo
                    
                    # Create transaction record
                    transaction = Transaction(
                        wallet_id=wallet.id,
                        amount=amount,
                        transaction_type="deposit",
                        status="completed",
                        reference=reference,
                        external_reference=transaction_data.get('reference'),
                        description=f"Deposit via Paystack - {customer_email}"
                    )
                    db.add(transaction)
                    
                    # Update wallet balance
                    wallet.balance += amount
                    
                    # Commit all changes
                    db.commit()
                    db.refresh(wallet)
                    
                    logger.info(f"✅ Webhook processed: {amount} credited to user {user.id}")
                    return {"status": "success", "message": "payment_processed", "amount": amount}
                    
                except Exception as e:
                    db.rollback()
                    logger.error(f"Error processing webhook payment: {str(e)}")
                    return {"status": "error", "message": "processing_failed"}
        
        elif event_type == 'transfer.success':
            logger.info("Transfer success webhook received")
            pass
        
        elif event_type == 'transfer.failed':
            logger.info("Transfer failed webhook received")
            pass
        
        return {"status": "success"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {type(e).__name__}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )


@router.post("/bulk/initiate")
async def initiate_bulk_payment(
    bulk_data: BulkPaymentRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Initiate bulk payments to multiple users"""
    
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can initiate bulk payments"
        )
    
    try:
        import uuid
        from shared.models import BulkPayment, BulkPaymentRecipient as BulkRecipientDB
        
        # Validate total amount doesn't exceed limits
        total_amount = sum(recipient.amount for recipient in bulk_data.recipients)
        if total_amount > 10000000:  # ₦10M limit per batch
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Total bulk payment amount cannot exceed ₦10,000,000"
            )
        
        # Create bulk payment record
        bulk_payment_id = str(uuid.uuid4())
        bulk_payment = BulkPayment(
            id=bulk_payment_id,
            admin_id=current_user.id,
            description=bulk_data.description,
            total_amount=total_amount,
            total_recipients=len(bulk_data.recipients),
            status="pending",
            notify_recipients=bulk_data.notify_recipients
        )
        db.add(bulk_payment)
        
        # Create recipient records
        for recipient in bulk_data.recipients:
            bulk_recipient = BulkRecipientDB(
                bulk_payment_id=bulk_payment_id,
                user_id=recipient.user_id,
                amount=recipient.amount,
                reason=recipient.reason,
                account_number=recipient.account_number,
                bank_code=recipient.bank_code,
                account_name=recipient.account_name,
                status="pending"
            )
            db.add(bulk_recipient)
        
        db.commit()
        db.refresh(bulk_payment)
        
        logger.info(f"Bulk payment initiated: {bulk_payment_id} by admin {current_user.id}")
        
        # TODO: Start background task to process bulk payments
        # This would typically use Celery or similar
        
        return {
            "status": "success",
            "bulk_payment_id": bulk_payment_id,
            "message": f"Bulk payment initiated for {len(bulk_data.recipients)} recipients",
            "total_amount": total_amount
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Bulk payment initiation error: {type(e).__name__}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate bulk payment"
        )


@router.get("/bulk/{bulk_payment_id}/status")
async def get_bulk_payment_status(
    bulk_payment_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get status of a bulk payment"""
    
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view bulk payment status"
        )
    
    try:
        from shared.models import BulkPayment, BulkPaymentRecipient as BulkRecipientDB
        
        bulk_payment = db.query(BulkPayment).filter(BulkPayment.id == bulk_payment_id).first()
        if not bulk_payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bulk payment not found"
            )
        
        # Count successful and failed recipients
        recipients = db.query(BulkRecipientDB).filter(
            BulkRecipientDB.bulk_payment_id == bulk_payment_id
        ).all()
        
        successful_count = sum(1 for r in recipients if r.status == "completed")
        failed_count = sum(1 for r in recipients if r.status == "failed")
        
        return {
            "id": bulk_payment.id,
            "status": bulk_payment.status,
            "total_amount": bulk_payment.total_amount,
            "total_recipients": bulk_payment.total_recipients,
            "successful_count": successful_count,
            "failed_count": failed_count,
            "created_at": bulk_payment.created_at.isoformat(),
            "description": bulk_payment.description,
            "admin_id": bulk_payment.admin_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk payment status error: {type(e).__name__}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get bulk payment status"
        )


@router.get("/bulk/{bulk_payment_id}/recipients")
async def get_bulk_payment_recipients(
    bulk_payment_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get list of recipients for a bulk payment"""
    
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view bulk payment recipients"
        )
    
    try:
        from shared.models import BulkPayment, BulkPaymentRecipient as BulkRecipientDB, User
        
        # Verify bulk payment exists
        bulk_payment = db.query(BulkPayment).filter(BulkPayment.id == bulk_payment_id).first()
        if not bulk_payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bulk payment not found"
            )
        
        # Get recipients with user details
        recipients = db.query(BulkRecipientDB, User).join(
            User, BulkRecipientDB.user_id == User.id
        ).filter(BulkRecipientDB.bulk_payment_id == bulk_payment_id).all()
        
        result = []
        for recipient, user in recipients:
            result.append({
                "id": recipient.id,
                "user_id": recipient.user_id,
                "username": user.username,
                "email": user.email,
                "amount": recipient.amount,
                "reason": recipient.reason,
                "account_number": recipient.account_number,
                "bank_code": recipient.bank_code,
                "account_name": recipient.account_name,
                "status": recipient.status,
                "error_message": recipient.error_message,
                "paystack_reference": recipient.paystack_reference,
                "created_at": recipient.created_at.isoformat(),
                "updated_at": recipient.updated_at.isoformat()
            })
        
        return {
            "bulk_payment_id": bulk_payment_id,
            "recipients": result,
            "total": len(result)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk payment recipients error: {type(e).__name__}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get bulk payment recipients"
        )


@router.get("/bulk/history")
async def get_bulk_payment_history(
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get history of bulk payments"""
    
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view bulk payment history"
        )
    
    try:
        from shared.models import BulkPayment
        
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 20
        
        offset = (page - 1) * limit
        
        # Get bulk payments
        bulk_payments = db.query(BulkPayment).order_by(
            BulkPayment.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        total = db.query(BulkPayment).count()
        
        result = []
        for bp in bulk_payments:
            result.append({
                "id": bp.id,
                "status": bp.status,
                "total_amount": bp.total_amount,
                "total_recipients": bp.total_recipients,
                "description": bp.description,
                "admin_id": bp.admin_id,
                "created_at": bp.created_at.isoformat(),
                "updated_at": bp.updated_at.isoformat()
            })
        
        return {
            "bulk_payments": result,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk payment history error: {type(e).__name__}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get bulk payment history"
        )