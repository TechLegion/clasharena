import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))

from celery import current_task
from sqlalchemy.orm import Session
from app.core.celery_app import celery_app
from app.core.database import get_db
from shared.models import User, Match, Transaction, AdminLog
import uuid
from datetime import datetime
from typing import List

@celery_app.task(bind=True)
def get_all_users_task(self, limit: int = 100, offset: int = 0):
    """Get all users with pagination"""
    try:
        # Get database session
        db = next(get_db())
        
        users = db.query(User).offset(offset).limit(limit).all()
        total_users = db.query(User).count()
        
        db.close()
        
        user_list = []
        for user in users:
            user_list.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_active': user.is_active,
                'is_admin': user.is_admin,
                'created_at': user.created_at.isoformat() if user.created_at else None
            })
        
        return {
            'success': True,
            'users': user_list,
            'total': total_users,
            'limit': limit,
            'offset': offset
        }
        
    except Exception as e:
        db.close()
        return {'success': False, 'error': str(e)}

@celery_app.task(bind=True)
def update_user_status_task(self, user_id: str, is_active: bool, admin_user_id: str):
    """Update user active status"""
    try:
        # Update task status
        self.update_state(state='PROGRESS', meta={'status': 'Updating user status...'})
        
        # Get database session
        db = next(get_db())
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            db.close()
            return {'success': False, 'error': 'User not found'}
        
        old_status = user.is_active
        user.is_active = is_active
        
        # Log admin action
        admin_log = AdminLog(
            id=str(uuid.uuid4()),
            admin_id=admin_user_id,
            action="update_user_status",
            details=f"Changed user {user.username} active status from {old_status} to {is_active}",
            created_at=datetime.utcnow()
        )
        
        db.add(admin_log)
        db.commit()
        db.refresh(user)
        db.refresh(admin_log)
        
        db.close()
        
        return {
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_active': user.is_active,
                'is_admin': user.is_admin
            },
            'action_logged': admin_log.id
        }
        
    except Exception as e:
        db.close()
        return {'success': False, 'error': str(e)}

@celery_app.task(bind=True)
def get_all_matches_task(self, limit: int = 100, offset: int = 0):
    """Get all matches with pagination"""
    try:
        # Get database session
        db = next(get_db())
        
        matches = db.query(Match).offset(offset).limit(limit).all()
        total_matches = db.query(Match).count()
        
        db.close()
        
        match_list = []
        for match in matches:
            match_list.append({
                'id': match.id,
                'user_id': match.user_id,
                'game_type': match.game_type,
                'match_type': match.match_type,
                'entry_fee': float(match.entry_fee),
                'prize_pool': float(match.prize_pool),
                'status': match.status,
                'result': match.result,
                'created_at': match.created_at.isoformat() if match.created_at else None,
                'updated_at': match.updated_at.isoformat() if match.updated_at else None
            })
        
        return {
            'success': True,
            'matches': match_list,
            'total': total_matches,
            'limit': limit,
            'offset': offset
        }
        
    except Exception as e:
        db.close()
        return {'success': False, 'error': str(e)}

@celery_app.task(bind=True)
def get_all_transactions_task(self, limit: int = 100, offset: int = 0):
    """Get all transactions with pagination"""
    try:
        # Get database session
        db = next(get_db())
        
        transactions = db.query(Transaction).offset(offset).limit(limit).all()
        total_transactions = db.query(Transaction).count()
        
        db.close()
        
        transaction_list = []
        for tx in transactions:
            transaction_list.append({
                'id': tx.id,
                'user_id': tx.user_id,
                'amount': float(tx.amount),
                'transaction_type': tx.transaction_type,
                'status': tx.status,
                'description': tx.description,
                'created_at': tx.created_at.isoformat() if tx.created_at else None
            })
        
        return {
            'success': True,
            'transactions': transaction_list,
            'total': total_transactions,
            'limit': limit,
            'offset': offset
        }
        
    except Exception as e:
        db.close()
        return {'success': False, 'error': str(e)}

@celery_app.task(bind=True)
def get_dashboard_stats_task(self):
    """Get admin dashboard statistics"""
    try:
        # Get database session
        db = next(get_db())
        
        # Count users
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        admin_users = db.query(User).filter(User.is_admin == True).count()
        
        # Count matches
        total_matches = db.query(Match).count()
        active_matches = db.query(Match).filter(Match.status == "active").count()
        completed_matches = db.query(Match).filter(Match.status == "completed").count()
        
        # Count transactions
        total_transactions = db.query(Transaction).count()
        completed_transactions = db.query(Transaction).filter(Transaction.status == "completed").count()
        
        # Calculate total volume
        total_volume = db.query(Transaction).filter(
            Transaction.status == "completed",
            Transaction.amount > 0
        ).all()
        
        total_volume_amount = sum(tx.amount for tx in total_volume)
        
        db.close()
        
        return {
            'success': True,
            'stats': {
                'users': {
                    'total': total_users,
                    'active': active_users,
                    'admins': admin_users
                },
                'matches': {
                    'total': total_matches,
                    'active': active_matches,
                    'completed': completed_matches
                },
                'transactions': {
                    'total': total_transactions,
                    'completed': completed_transactions,
                    'total_volume': float(total_volume_amount)
                }
            }
        }
        
    except Exception as e:
        db.close()
        return {'success': False, 'error': str(e)}

@celery_app.task(bind=True)
def get_admin_logs_task(self, limit: int = 100, offset: int = 0):
    """Get admin activity logs"""
    try:
        # Get database session
        db = next(get_db())
        
        logs = db.query(AdminLog).offset(offset).limit(limit).all()
        total_logs = db.query(AdminLog).count()
        
        db.close()
        
        log_list = []
        for log in logs:
            log_list.append({
                'id': log.id,
                'admin_id': log.admin_id,
                'action': log.action,
                'details': log.details,
                'created_at': log.created_at.isoformat() if log.created_at else None
            })
        
        return {
            'success': True,
            'logs': log_list,
            'total': total_logs,
            'limit': limit,
            'offset': offset
        }
        
    except Exception as e:
        db.close()
        return {'success': False, 'error': str(e)}

