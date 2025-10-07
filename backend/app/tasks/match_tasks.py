import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))

from celery import current_task
from sqlalchemy.orm import Session
from app.core.celery_app import celery_app
from app.core.database import get_db
from shared.models import User, Match, Transaction, Wallet
import uuid
from decimal import Decimal
from datetime import datetime
from typing import List, Dict, Any
import json

@celery_app.task(bind=True)
def create_match_task(self, match_data: dict):
    """Create a new match with comprehensive validation and processing"""
    try:
        # Update task status
        self.update_state(state='PROGRESS', meta={'status': 'Creating match...'})
        
        # Get database session
        db = next(get_db())
        
        # Verify user exists and is active
        user = db.query(User).filter(User.id == match_data['user_id']).first()
        if not user or not user.is_active:
            db.close()
            return {'success': False, 'error': 'User not found or inactive'}
        
        # Validate match data
        game_type = match_data['game_type']
        match_type = match_data.get('match_type', 'solo')
        entry_fee = Decimal(str(match_data['entry_fee']))
        
        # Validate entry fee
        if entry_fee <= 0:
            db.close()
            return {'success': False, 'error': 'Invalid entry fee'}
        
        # Update task status
        self.update_state(state='PROGRESS', meta={'status': 'Checking wallet balance...'})
        
        # Check wallet balance
        wallet = db.query(Wallet).filter(Wallet.user_id == match_data['user_id']).first()
        if not wallet:
            db.close()
            return {'success': False, 'error': 'Wallet not found'}
        
        if wallet.balance < entry_fee:
            db.close()
            return {'success': False, 'error': 'Insufficient balance'}
        
        # Calculate prize pool based on match type
        prize_multipliers = {
            'solo': 1.8,
            'duo': 2.0,
            'squad': 2.2,
            'battle_royale': 2.5,
            'multiplayer': 1.8,
            'ranked': 2.0,
            'tournament': 2.5,
            'friendly': 1.5,
            'league': 2.0,
            'ladder': 1.8,
            'challenge': 2.2
        }
        
        multiplier = prize_multipliers.get(match_type, 1.8)
        prize_pool = entry_fee * Decimal(str(multiplier))
        
        # Update task status
        self.update_state(state='PROGRESS', meta={'status': 'Creating match record...'})
        
        # Create match
        match = Match(
            id=str(uuid.uuid4()),
            user_id=match_data['user_id'],
            game_type=game_type,
            match_type=match_type,
            entry_fee=entry_fee,
            prize_pool=prize_pool,
            status="pending",
            created_at=datetime.utcnow()
        )
        
        db.add(match)
        
        # Update task status
        self.update_state(state='PROGRESS', meta={'status': 'Processing payment...'})
        
        # Deduct entry fee from wallet
        wallet.balance -= entry_fee
        
        # Create transaction record
        transaction = Transaction(
            id=str(uuid.uuid4()),
            wallet_id=wallet.id,
            amount=-entry_fee,
            transaction_type="match_entry",
            status="completed",
            description=f"Entry fee for {game_type} {match_type} match",
            created_at=datetime.utcnow()
        )
        
        db.add(transaction)
        
        # Update match status to active
        match.status = "active"
        
        db.commit()
        db.refresh(match)
        db.refresh(wallet)
        
        db.close()
        
        return {
            'success': True,
            'match': {
                'id': match.id,
                'game_type': match.game_type,
                'match_type': match.match_type,
                'entry_fee': float(match.entry_fee),
                'prize_pool': float(match.prize_pool),
                'status': match.status,
                'created_at': match.created_at.isoformat(),
                'new_balance': float(wallet.balance)
            }
        }
        
    except Exception as e:
        db.close()
        return {'success': False, 'error': str(e)}

@celery_app.task(bind=True)
def update_match_result_task(self, match_id: str, result_data: dict):
    """Update match result and distribute prizes"""
    try:
        # Update task status
        self.update_state(state='PROGRESS', meta={'status': 'Updating match result...'})
        
        # Get database session
        db = next(get_db())
        
        # Find match
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            db.close()
            return {'success': False, 'error': 'Match not found'}
        
        if match.status not in ['active', 'pending']:
            db.close()
            return {'success': False, 'error': 'Match is not active'}
        
        # Update match with results
        match.status = "completed"
        match.result = result_data.get('result', 'completed')
        match.updated_at = datetime.utcnow()
        
        # Update task status
        self.update_state(state='PROGRESS', meta={'status': 'Processing winnings...'})
        
        # If user won, add prize to wallet
        if result_data.get('won', False):
            wallet = db.query(Wallet).filter(Wallet.user_id == match.user_id).first()
            if wallet:
                # Create winning transaction
                winning_transaction = Transaction(
                    id=str(uuid.uuid4()),
                    wallet_id=wallet.id,
                    amount=match.prize_pool,
                    transaction_type="match_win",
                    status="completed",
                    description=f"Prize for winning {match.game_type} {match.match_type} match",
                    created_at=datetime.utcnow()
                )
                
                db.add(winning_transaction)
                wallet.balance += match.prize_pool
        
        db.commit()
        db.refresh(match)
        
        db.close()
        
        return {
            'success': True,
            'match': {
                'id': match.id,
                'status': match.status,
                'result': match.result,
                'updated_at': match.updated_at.isoformat(),
                'won': result_data.get('won', False)
            }
        }
        
    except Exception as e:
        db.close()
        return {'success': False, 'error': str(e)}

@celery_app.task(bind=True)
def get_user_matches_task(self, user_id: str, limit: int = 50):
    """Get user's match history with comprehensive data"""
    try:
        # Get database session
        db = next(get_db())
        
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            db.close()
            return {'success': False, 'error': 'User not found'}
        
        # Get matches with pagination
        matches = db.query(Match).filter(
            Match.user_id == user_id
        ).order_by(Match.created_at.desc()).limit(limit).all()
        
        db.close()
        
        match_list = []
        total_winnings = 0
        total_bets = 0
        wins = 0
        
        for match in matches:
            match_data = {
                'id': match.id,
                'game_type': match.game_type,
                'match_type': match.match_type,
                'entry_fee': float(match.entry_fee),
                'prize_pool': float(match.prize_pool),
                'status': match.status,
                'result': match.result,
                'created_at': match.created_at.isoformat() if match.created_at else None,
                'updated_at': match.updated_at.isoformat() if match.updated_at else None
            }
            
            match_list.append(match_data)
            
            # Calculate stats
            total_bets += float(match.entry_fee)
            if match.result and match.result.lower() in ['win', 'won', 'victory']:
                wins += 1
                total_winnings += float(match.prize_pool)
        
        win_rate = (wins / len(matches) * 100) if matches else 0
        
        return {
            'success': True,
            'matches': match_list,
            'stats': {
                'total_matches': len(matches),
                'wins': wins,
                'win_rate': round(win_rate, 2),
                'total_bets': total_bets,
                'total_winnings': total_winnings,
                'net_profit': total_winnings - total_bets
            },
            'count': len(match_list)
        }
        
    except Exception as e:
        db.close()
        return {'success': False, 'error': str(e)}

@celery_app.task(bind=True)
def get_leaderboard_task(self, game_type: str = None, limit: int = 100):
    """Get comprehensive leaderboard with user statistics"""
    try:
        # Get database session
        db = next(get_db())
        
        # Query for completed matches with wins
        query = db.query(Match).filter(
            Match.status == "completed",
            Match.result.in_(["win", "won", "victory"])
        )
        
        if game_type:
            query = query.filter(Match.game_type == game_type)
        
        matches = query.all()
        
        # Calculate leaderboard
        user_stats = {}
        for match in matches:
            if match.user_id not in user_stats:
                user_stats[match.user_id] = {
                    'user_id': match.user_id,
                    'wins': 0,
                    'total_prizes': Decimal('0'),
                    'games_played': 0,
                    'total_bets': Decimal('0'),
                    'win_rate': 0,
                    'net_profit': Decimal('0')
                }
            
            user_stats[match.user_id]['wins'] += 1
            user_stats[match.user_id]['total_prizes'] += match.prize_pool
            user_stats[match.user_id]['total_bets'] += match.entry_fee
            user_stats[match.user_id]['net_profit'] += (match.prize_pool - match.entry_fee)
        
        # Get total games played for win rate calculation
        all_matches_query = db.query(Match).filter(Match.status == "completed")
        if game_type:
            all_matches_query = all_matches_query.filter(Match.game_type == game_type)
        
        all_matches = all_matches_query.all()
        for match in all_matches:
            if match.user_id in user_stats:
                user_stats[match.user_id]['games_played'] += 1
        
        # Calculate win rates
        for user_id, stats in user_stats.items():
            if stats['games_played'] > 0:
                stats['win_rate'] = round((stats['wins'] / stats['games_played']) * 100, 2)
        
        # Sort by wins, then by net profit
        leaderboard = sorted(
            user_stats.values(),
            key=lambda x: (x['wins'], float(x['net_profit'])),
            reverse=True
        )[:limit]
        
        # Convert Decimal to float for JSON serialization
        for entry in leaderboard:
            entry['total_prizes'] = float(entry['total_prizes'])
            entry['total_bets'] = float(entry['total_bets'])
            entry['net_profit'] = float(entry['net_profit'])
        
        db.close()
        
        return {
            'success': True,
            'leaderboard': leaderboard,
            'count': len(leaderboard),
            'game_type': game_type or 'all'
        }
        
    except Exception as e:
        db.close()
        return {'success': False, 'error': str(e)}

@celery_app.task(bind=True)
def get_match_statistics_task(self, user_id: str = None, game_type: str = None):
    """Get comprehensive match statistics"""
    try:
        # Get database session
        db = next(get_db())
        
        # Build query
        query = db.query(Match).filter(Match.status == "completed")
        
        if user_id:
            query = query.filter(Match.user_id == user_id)
        if game_type:
            query = query.filter(Match.game_type == game_type)
        
        matches = query.all()
        
        # Calculate statistics
        total_matches = len(matches)
        total_volume = sum(float(match.entry_fee) for match in matches)
        total_prizes = sum(float(match.prize_pool) for match in matches)
        
        wins = sum(1 for match in matches if match.result and match.result.lower() in ['win', 'won', 'victory'])
        win_rate = (wins / total_matches * 100) if total_matches > 0 else 0
        
        # Game type distribution
        game_types = {}
        match_types = {}
        
        for match in matches:
            game_types[match.game_type] = game_types.get(match.game_type, 0) + 1
            match_types[match.match_type] = match_types.get(match.match_type, 0) + 1
        
        db.close()
        
        return {
            'success': True,
            'statistics': {
                'total_matches': total_matches,
                'total_volume': total_volume,
                'total_prizes': total_prizes,
                'wins': wins,
                'win_rate': round(win_rate, 2),
                'game_types': game_types,
                'match_types': match_types,
                'average_bet': total_volume / total_matches if total_matches > 0 else 0
            }
        }
        
    except Exception as e:
        db.close()
        return {'success': False, 'error': str(e)}