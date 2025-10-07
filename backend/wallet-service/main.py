from fastapi import FastAPI, HTTPException, Depends, status, Header, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
import os
import httpx
import hmac
import hashlib
import logging
from typing import Optional
import uuid

from shared.database import get_db, init_db
from shared.models import User, Wallet, Transaction

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ClashArena Wallet Service", version="2.0.0")

# Payment gateway configuration
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY", "")
FLUTTERWAVE_SECRET_KEY = os.getenv("FLUTTERWAVE_SECRET_KEY", "")
API_KEY = os.getenv("WALLET_SERVICE_API_KEY", "")  # For inter-service auth

# Initialize database
init_db()


# ============= PYDANTIC MODELS =============
class DepositRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    amount: float = Field(..., ge=100, le=1000000)
    email: EmailStr
    payment_method: str = Field(default="paystack", pattern="^(paystack|flutterwave)$")


class WithdrawRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    amount: float = Field(..., ge=500, le=500000)
    bank_code: str
    account_number: str = Field(..., pattern=r'^\d{10}$')
    account_name: str


class VerifyDepositRequest(BaseModel):
    reference: str


# ============= AUTHENTICATION =============
async def verify_api_key(x_api_key: str = Header(...)):
    """Verify API key for inter-service communication"""
    if not API_KEY or x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return True


# ============= BASIC ENDPOINTS =============
@app.get("/")
async def root():
    return {"message": "ClashArena Wallet Service", "version": "2.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "wallet-service"}


@app.get("/balance/{user_id}")
async def get_wallet_balance(
    user_id: str,
    db: Session = Depends(get_db),
    authenticated: bool = Depends(verify_api_key)
):
    """Get wallet balance for a user (authenticated)"""
    try:
        wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
        
        if not wallet:
            # Create wallet if it doesn't exist
            wallet = Wallet(user_id=user_id, balance=0.0)
            db.add(wallet)
            db.commit()
            db.refresh(wallet)
        
        return {
            "user_id": user_id,
            "balance": wallet.balance,
            "currency": wallet.currency,
            "is_active": wallet.is_active
        }
        
    except Exception as e:
        logger.error(f"Error fetching balance for user {user_id}: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch balance"
        )


# ============= DEPOSIT FLOW =============
@app.post("/deposit/initialize")
async def initialize_deposit(
    deposit_data: DepositRequest,
    db: Session = Depends(get_db),
    authenticated: bool = Depends(verify_api_key)
):
    """Initialize deposit - returns payment URL (does NOT credit balance)"""
    try:
        # Get or create wallet
        wallet = db.query(Wallet).filter(
            Wallet.user_id == deposit_data.user_id
        ).first()
        
        if not wallet:
            wallet = Wallet(user_id=deposit_data.user_id, balance=0.0)
            db.add(wallet)
            db.commit()
            db.refresh(wallet)
        
        # Generate unique reference
        reference = f"dep_{uuid.uuid4()}"
        
        # Create pending transaction
        transaction = Transaction(
            wallet_id=wallet.id,
            amount=deposit_data.amount,
            transaction_type="deposit",
            status="pending",
            reference=reference,
            description=f"Deposit via {deposit_data.payment_method}"
        )
        db.add(transaction)
        db.commit()
        
        # Initialize payment gateway
        if deposit_data.payment_method == "paystack":
            payment_result = await initialize_paystack_payment(
                deposit_data.amount,
                reference,
                deposit_data.email
            )
        else:
            payment_result = await initialize_flutterwave_payment(
                deposit_data.amount,
                reference,
                deposit_data.email
            )
        
        if payment_result["status"] == "success":
            transaction.external_reference = payment_result.get("external_reference")
            db.commit()
            
            return {
                "status": "success",
                "message": "Payment initialized",
                "authorization_url": payment_result.get("authorization_url"),
                "reference": reference
            }
        else:
            transaction.status = "failed"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment initialization failed"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Deposit initialization error: {type(e).__name__}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Deposit initialization failed"
        )


@app.post("/deposit/verify")
async def verify_deposit(
    verify_data: VerifyDepositRequest,
    db: Session = Depends(get_db),
    authenticated: bool = Depends(verify_api_key)
):
    """Verify and complete deposit (called after user pays)"""
    try:
        # Find transaction
        transaction = db.query(Transaction).filter(
            Transaction.reference == verify_data.reference
        ).first()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        if transaction.status == "completed":
            return {"status": "already_completed", "message": "Transaction already processed"}
        
        # Verify with payment gateway
        if "paystack" in transaction.description.lower():
            verified = await verify_paystack_payment(transaction.external_reference)
        else:
            verified = await verify_flutterwave_payment(transaction.external_reference)
        
        if not verified:
            transaction.status = "failed"
            db.commit()
            return {"status": "failed", "message": "Payment verification failed"}
        
        # Credit wallet atomically
        try:
            wallet = db.query(Wallet).filter(
                Wallet.id == transaction.wallet_id
            ).with_for_update().first()
            
            wallet.balance += transaction.amount
            transaction.status = "completed"
            
            db.commit()
            db.refresh(wallet)
            
            logger.info(f"Deposit completed: {transaction.amount} for wallet {wallet.id}")
            
            return {
                "status": "success",
                "message": f"Deposit of ₦{transaction.amount:,.2f} completed",
                "new_balance": wallet.balance
            }
            
        except IntegrityError:
            db.rollback()
            return {"status": "already_completed", "message": "Transaction already processed"}
            
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Deposit verification error: {type(e).__name__}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verification failed"
        )


# ============= WITHDRAWAL FLOW =============
@app.post("/withdraw")
async def withdraw_funds(
    withdraw_data: WithdrawRequest,
    db: Session = Depends(get_db),
    authenticated: bool = Depends(verify_api_key)
):
    """Process withdrawal request"""
    try:
        # Get wallet with lock
        wallet = db.query(Wallet).filter(
            Wallet.user_id == withdraw_data.user_id
        ).with_for_update().first()
        
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        
        # Check balance
        if wallet.balance < withdraw_data.amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient balance. Available: ₦{wallet.balance:,.2f}"
            )
        
        reference = f"with_{uuid.uuid4()}"
        
        # Deduct balance immediately
        wallet.balance -= withdraw_data.amount
        
        # Create transaction record
        transaction = Transaction(
            wallet_id=wallet.id,
            amount=withdraw_data.amount,
            transaction_type="withdrawal",
            status="processing",
            reference=reference,
            description=f"Withdrawal to {withdraw_data.account_number}"
        )
        db.add(transaction)
        db.commit()
        
        # TODO: Process actual bank transfer via Paystack Transfer API
        # For now, mark as completed
        transaction.status = "completed"
        db.commit()
        
        logger.info(f"Withdrawal processed: {withdraw_data.amount} for user {withdraw_data.user_id}")
        
        return {
            "status": "success",
            "message": "Withdrawal initiated",
            "reference": reference,
            "new_balance": wallet.balance
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Withdrawal error: {type(e).__name__}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Withdrawal failed"
        )


# ============= TRANSACTION HISTORY =============
@app.get("/transactions/{user_id}")
async def get_transactions(
    user_id: str,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
    authenticated: bool = Depends(verify_api_key)
):
    """Get transaction history for a user"""
    try:
        wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
        if not wallet:
            return {"transactions": [], "total": 0, "page": page, "limit": limit}
        
        offset = (page - 1) * limit
        transactions = db.query(Transaction).filter(
            Transaction.wallet_id == wallet.id
        ).order_by(Transaction.created_at.desc()).offset(offset).limit(limit).all()
        
        total = db.query(Transaction).filter(Transaction.wallet_id == wallet.id).count()
        
        return {
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
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
        
    except Exception as e:
        logger.error(f"Transaction history error: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch transactions"
        )


# ============= WEBHOOKS =============
@app.post("/webhook/paystack")
async def paystack_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Paystack webhook with signature verification"""
    try:
        body = await request.body()
        signature = request.headers.get('x-paystack-signature')
        
        if not signature:
            logger.warning("Webhook without signature")
            raise HTTPException(status_code=401, detail="No signature")
        
        # Verify signature
        computed_signature = hmac.new(
            PAYSTACK_SECRET_KEY.encode('utf-8'),
            body,
            hashlib.sha512
        ).hexdigest()
        
        if not hmac.compare_digest(signature, computed_signature):
            logger.error("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        webhook_data = await request.json()
        event = webhook_data.get("event")
        
        if event == "charge.success":
            data = webhook_data.get("data", {})
            reference = data.get("reference")
            
            # Find transaction
            transaction = db.query(Transaction).filter(
                Transaction.external_reference == reference
            ).first()
            
            if transaction and transaction.status == "pending":
                # Credit wallet
                wallet = db.query(Wallet).filter(
                    Wallet.id == transaction.wallet_id
                ).with_for_update().first()
                
                wallet.balance += transaction.amount
                transaction.status = "completed"
                db.commit()
                
                logger.info(f"Webhook processed: {reference}")
        
        return {"status": "success"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook error: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=500, detail="Webhook processing failed")


# ============= PAYMENT GATEWAY HELPERS =============
async def initialize_paystack_payment(amount: float, reference: str, email: str):
    """Initialize Paystack payment"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.paystack.co/transaction/initialize",
                headers={
                    "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "email": email,
                    "amount": int(amount * 100),
                    "reference": reference
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "status": "success",
                    "external_reference": result["data"]["reference"],
                    "authorization_url": result["data"]["authorization_url"]
                }
            
            return {"status": "failed"}
    except Exception as e:
        logger.error(f"Paystack init error: {type(e).__name__}")
        return {"status": "failed"}


async def verify_paystack_payment(reference: str) -> bool:
    """Verify payment with Paystack"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"https://api.paystack.co/transaction/verify/{reference}",
                headers={"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["data"]["status"] == "success"
            
            return False
    except Exception:
        return False


async def initialize_flutterwave_payment(amount: float, reference: str, email: str):
    """Initialize Flutterwave payment"""
    # Implementation similar to Paystack
    return {"status": "failed", "message": "Flutterwave not implemented"}


async def verify_flutterwave_payment(reference: str) -> bool:
    """Verify Flutterwave payment"""
    return False


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)