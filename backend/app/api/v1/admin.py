from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from app.core.database import get_db
from app.api.deps import get_current_admin_user
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
from shared.models import User, Match, Transaction, AdminLog

router = APIRouter()

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

@router.get("/dashboard/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_admin_user), 
    db: Session = Depends(get_db)
):
    """Get dashboard statistics (admin only)"""
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
        total_bets = db.query(func.sum(Match.bet_amount)).scalar() or 0
        total_winnings = db.query(func.sum(Match.potential_winnings)).filter(
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

@router.get("/users")
async def get_all_users(
    page: int = 1,
    limit: int = 20,
    search: str = None,
    is_active: bool = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all users with filtering and pagination (admin only)"""
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

@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    status_data: dict,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update user active status (admin only)"""
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
            admin_id=current_user.id,
            action="update_user_status",
            target_type="user",
            target_id=user_id,
            details=f"Changed user status from {old_status} to {user.is_active}",
            ip_address="127.0.0.1",  # In production, get from request
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

@router.post("/users/{user_id}/promote")
async def promote_user_to_admin(
    user_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Promote a user to admin (admin only)"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        old_admin_status = user.is_admin
        user.is_admin = True
        user.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Log admin action
        log_admin_action(
            admin_id=current_user.id,
            action="promote_user",
            target_type="user",
            target_id=user_id,
            details=f"Promoted user {user.username} to admin",
            ip_address="127.0.0.1",  # In production, get from request
            db=db
        )
        
        return {
            "status": "success",
            "message": f"User {user.username} promoted to admin",
            "user_id": user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
