from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_active_user
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
from shared.models import User, Wallet, Transaction

router = APIRouter()

@router.get("/balance")
async def get_wallet_balance(
    current_user: User = Depends(get_current_active_user), 
    db: Session = Depends(get_db)
):
    """Get wallet balance for current user"""
    try:
        wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
        
        if not wallet:
            # Create wallet if it doesn't exist
            wallet = Wallet(user_id=current_user.id, balance=0.0)
            db.add(wallet)
            db.commit()
            db.refresh(wallet)
        
        return {
            "user_id": current_user.id,
            "balance": wallet.balance,
            "currency": wallet.currency,
            "is_active": wallet.is_active
        }
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/deposit")
async def deposit_funds(
    deposit_data: dict, 
    current_user: User = Depends(get_current_active_user), 
    db: Session = Depends(get_db)
):
    """Process deposit request"""
    try:
        amount = deposit_data["amount"]
        payment_method = deposit_data.get("payment_method", "paystack")
        reference = deposit_data.get("reference", f"dep_{current_user.id}_{db.query(Transaction).count()}")
        
        # Get or create wallet
        wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
        if not wallet:
            wallet = Wallet(user_id=current_user.id, balance=0.0)
            db.add(wallet)
            db.commit()
            db.refresh(wallet)
        
        # Create transaction record
        transaction = Transaction(
            wallet_id=wallet.id,
            amount=amount,
            transaction_type="deposit",
            status="pending",
            reference=reference,
            description=f"Deposit via {payment_method}"
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        # Simulate payment processing (in production, integrate with actual payment gateways)
        if amount > 0:
            # Simulate successful payment
            wallet.balance += amount
            transaction.status = "completed"
            transaction.external_reference = f"PAY_{reference}"
            db.commit()
            
            return {
                "status": "success",
                "message": "Deposit successful",
                "transaction_id": transaction.id,
                "new_balance": wallet.balance,
                "reference": reference
            }
        else:
            transaction.status = "failed"
            db.commit()
            
            return {
                "status": "failed",
                "message": "Invalid amount",
                "transaction_id": transaction.id
            }
            
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/transactions")
async def get_transactions(
    page: int = 1, 
    limit: int = 20, 
    current_user: User = Depends(get_current_active_user), 
    db: Session = Depends(get_db)
):
    """Get transaction history for current user"""
    try:
        # Get wallet
        wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
        if not wallet:
            return {"transactions": [], "total": 0, "page": page, "limit": limit}
        
        # Get transactions with pagination
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
                    "created_at": t.created_at
                }
                for t in transactions
            ],
            "total": total,
            "page": page,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
