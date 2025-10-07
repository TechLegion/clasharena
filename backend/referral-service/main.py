from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import string
import random

from shared.database import get_db, init_db
from shared.models import User, Referral, Wallet, Transaction

app = FastAPI(title="ClashArena Referral Service", version="1.0.0")

# Initialize database
init_db()

def generate_referral_code(length: int = 8) -> str:
    """Generate a random referral code"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

@app.get("/")
async def root():
    return {"message": "ClashArena Referral Service", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "referral-service"}

@app.get("/referrals")
async def get_referrals(user_id: str, db: Session = Depends(get_db)):
    """Get referrals for a user"""
    try:
        referrals = db.query(Referral).filter(Referral.referrer_id == user_id).all()
        
        return {
            "referrals": [
                {
                    "id": ref.id,
                    "referred_id": ref.referred_id,
                    "referral_code": ref.referral_code,
                    "status": ref.status,
                    "reward_amount": ref.reward_amount,
                    "created_at": ref.created_at
                }
                for ref in referrals
            ],
            "total_referrals": len(referrals),
            "total_rewards": sum(ref.reward_amount for ref in referrals if ref.status == "completed")
        }
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.post("/referrals")
async def create_referral(referral_data: dict, db: Session = Depends(get_db)):
    """Create a referral code for a user"""
    try:
        user_id = referral_data["user_id"]
        
        # Check if user already has a referral code
        existing_referral = db.query(Referral).filter(Referral.referrer_id == user_id).first()
        if existing_referral:
            return {
                "status": "success",
                "referral_code": existing_referral.referral_code,
                "message": "Referral code already exists"
            }
        
        # Generate unique referral code
        while True:
            referral_code = generate_referral_code()
            existing_code = db.query(Referral).filter(Referral.referral_code == referral_code).first()
            if not existing_code:
                break
        
        # Create referral record
        new_referral = Referral(
            referrer_id=user_id,
            referral_code=referral_code,
            referred_id=None,  # Will be set when someone uses the code
            status="pending"
        )
        
        db.add(new_referral)
        db.commit()
        db.refresh(new_referral)
        
        return {
            "status": "success",
            "referral_code": referral_code,
            "message": "Referral code created successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.post("/referrals/use")
async def use_referral_code(referral_data: dict, db: Session = Depends(get_db)):
    """Use a referral code"""
    try:
        referral_code = referral_data["referral_code"]
        referred_user_id = referral_data["referred_user_id"]
        
        # Check if referral code exists
        referral = db.query(Referral).filter(Referral.referral_code == referral_code).first()
        if not referral:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid referral code"
            )
        
        # Check if user is trying to refer themselves
        if referral.referrer_id == referred_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot use your own referral code"
            )
        
        # Check if user has already used a referral code
        existing_referral = db.query(Referral).filter(Referral.referred_id == referred_user_id).first()
        if existing_referral:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User has already used a referral code"
            )
        
        # Update referral record
        referral.referred_id = referred_user_id
        referral.status = "completed"
        referral.reward_amount = 500.0  # Reward amount for successful referral
        
        # Add reward to referrer's wallet
        referrer_wallet = db.query(Wallet).filter(Wallet.user_id == referral.referrer_id).first()
        if referrer_wallet:
            referrer_wallet.balance += referral.reward_amount
            
            # Create transaction record
            transaction = Transaction(
                wallet_id=referrer_wallet.id,
                amount=referral.reward_amount,
                transaction_type="referral_bonus",
                status="completed",
                reference=f"ref_{referral.id}",
                description=f"Referral bonus for referring user {referred_user_id}"
            )
            db.add(transaction)
        
        # Add bonus to referred user's wallet
        referred_wallet = db.query(Wallet).filter(Wallet.user_id == referred_user_id).first()
        if referred_wallet:
            referred_wallet.balance += 200.0  # Bonus for new user
            
            # Create transaction record
            transaction = Transaction(
                wallet_id=referred_wallet.id,
                amount=200.0,
                transaction_type="signup_bonus",
                status="completed",
                reference=f"signup_{referred_user_id}",
                description="Sign-up bonus from referral"
            )
            db.add(transaction)
        
        db.commit()
        
        return {
            "status": "success",
            "message": "Referral code used successfully",
            "referrer_reward": 500.0,
            "referred_bonus": 200.0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.get("/referrals/stats")
async def get_referral_stats(user_id: str, db: Session = Depends(get_db)):
    """Get referral statistics for a user"""
    try:
        # Get all referrals made by user
        referrals = db.query(Referral).filter(Referral.referrer_id == user_id).all()
        
        stats = {
            "total_referrals": len(referrals),
            "completed_referrals": len([r for r in referrals if r.status == "completed"]),
            "pending_referrals": len([r for r in referrals if r.status == "pending"]),
            "total_rewards_earned": sum(r.reward_amount for r in referrals if r.status == "completed"),
            "referral_code": referrals[0].referral_code if referrals else None
        }
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
