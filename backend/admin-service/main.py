from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import json

from shared.database import get_db, init_db
from shared.models import User, Match, Wallet, Transaction, Referral, AdminLog

app = FastAPI(title="ClashArena Admin Service", version="1.0.0")

# Initialize database
init_db()

def log_admin_action(admin_id: str, action: str, target_type: str, target_id: str, details: str, ip_address: str, db: Session):
    """Log admin action for audit trail"""
    admin_log = AdminLog(
        admin_id=admin_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=ip_address
    )
    db.add(admin_log)
    db.commit()

@app.get("/")
async def root():
    return {"message": "ClashArena Admin Service", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "admin-service"}

@app.get("/users")
async def get_all_users(
    page: int = 1,
    limit: int = 20,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get all users with filtering and pagination"""
    try:
        query = db.query(User)
        
        if search:
            query = query.filter(
                (User.username.ilike(f"%{search}%")) |
                (User.email.ilike(f"%{search}%")) |
                (User.full_name.ilike(f"%{search}%"))
            )
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        # Pagination
        offset = (page - 1) * limit
        users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()
        total = query.count()
        
        return {
            "users": [
                {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "full_name": user.full_name,
                    "is_active": user.is_active,
                    "is_admin": user.is_admin,
                    "created_at": user.created_at,
                    "updated_at": user.updated_at
                }
                for user in users
            ],
            "total": total,
            "page": page,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.put("/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    status_data: dict,
    admin_id: str,
    ip_address: str = "127.0.0.1",
    db: Session = Depends(get_db)
):
    """Update user active status"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        old_status = user.is_active
        user.is_active = status_data["is_active"]
        user.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Log admin action
        log_admin_action(
            admin_id=admin_id,
            action="update_user_status",
            target_type="user",
            target_id=user_id,
            details=f"Changed user status from {old_status} to {user.is_active}",
            ip_address=ip_address,
            db=db
        )
        
        return {
            "status": "success",
            "message": f"User status updated to {'active' if user.is_active else 'inactive'}",
            "user_id": user_id,
            "new_status": user.is_active
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.get("/matches")
async def get_all_matches(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    game_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all matches with filtering and pagination"""
    try:
        query = db.query(Match)
        
        if status:
            query = query.filter(Match.status == status)
        if game_type:
            query = query.filter(Match.game_type == game_type)
        
        # Pagination
        offset = (page - 1) * limit
        matches = query.order_by(Match.created_at.desc()).offset(offset).limit(limit).all()
        total = query.count()
        
        return {
            "matches": [
                {
                    "id": match.id,
                    "user_id": match.user_id,
                    "game_type": match.game_type,
                    "match_type": match.match_type,
                    "status": match.status,
                    "result": match.result,
                    "bet_amount": match.bet_amount,
                    "potential_winnings": match.potential_winnings,
                    "created_at": match.created_at,
                    "updated_at": match.updated_at
                }
                for match in matches
            ],
            "total": total,
            "page": page,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.get("/transactions")
async def get_all_transactions(
    page: int = 1,
    limit: int = 20,
    transaction_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all transactions with filtering and pagination"""
    try:
        query = db.query(Transaction)
        
        if transaction_type:
            query = query.filter(Transaction.transaction_type == transaction_type)
        if status:
            query = query.filter(Transaction.status == status)
        
        # Pagination
        offset = (page - 1) * limit
        transactions = query.order_by(Transaction.created_at.desc()).offset(offset).limit(limit).all()
        total = query.count()
        
        return {
            "transactions": [
                {
                    "id": t.id,
                    "wallet_id": t.wallet_id,
                    "amount": t.amount,
                    "transaction_type": t.transaction_type,
                    "status": t.status,
                    "reference": t.reference,
                    "description": t.description,
                    "external_reference": t.external_reference,
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

@app.get("/dashboard/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    try:
        # User statistics
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        new_users_today = db.query(User).filter(
            User.created_at >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        
        # Match statistics
        total_matches = db.query(Match).count()
        active_matches = db.query(Match).filter(Match.status == "active").count()
        completed_matches = db.query(Match).filter(Match.status == "completed").count()
        
        # Transaction statistics
        total_transactions = db.query(Transaction).count()
        total_deposits = db.query(Transaction).filter(Transaction.transaction_type == "deposit").count()
        total_withdrawals = db.query(Transaction).filter(Transaction.transaction_type == "withdrawal").count()
        
        # Revenue statistics
        total_bets = db.query(Match).with_entities(db.func.sum(Match.bet_amount)).scalar() or 0
        total_winnings = db.query(Match).with_entities(db.func.sum(Match.potential_winnings)).filter(
            Match.result == "win"
        ).scalar() or 0
        
        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "new_today": new_users_today
            },
            "matches": {
                "total": total_matches,
                "active": active_matches,
                "completed": completed_matches
            },
            "transactions": {
                "total": total_transactions,
                "deposits": total_deposits,
                "withdrawals": total_withdrawals
            },
            "revenue": {
                "total_bets": float(total_bets),
                "total_winnings": float(total_winnings),
                "net_revenue": float(total_bets - total_winnings)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.get("/admin-logs")
async def get_admin_logs(
    page: int = 1,
    limit: int = 20,
    admin_id: Optional[str] = None,
    action: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get admin action logs"""
    try:
        query = db.query(AdminLog)
        
        if admin_id:
            query = query.filter(AdminLog.admin_id == admin_id)
        if action:
            query = query.filter(AdminLog.action == action)
        
        # Pagination
        offset = (page - 1) * limit
        logs = query.order_by(AdminLog.created_at.desc()).offset(offset).limit(limit).all()
        total = query.count()
        
        return {
            "logs": [
                {
                    "id": log.id,
                    "admin_id": log.admin_id,
                    "action": log.action,
                    "target_type": log.target_type,
                    "target_id": log.target_id,
                    "details": log.details,
                    "ip_address": log.ip_address,
                    "created_at": log.created_at
                }
                for log in logs
            ],
            "total": total,
            "page": page,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
