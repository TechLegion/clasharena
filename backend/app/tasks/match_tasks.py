"""
Enhanced match tasks for handling game data integration
"""

from celery import Celery
from sqlalchemy.orm import Session
from app.core.database import get_db
from shared.models import Match, User, Wallet, Transaction
from typing import Dict, Any, List
import json
import logging
from datetime import datetime, timedelta
import requests
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Celery app (this should be imported from your main app)
from app.core.celery_app import celery_app

@celery_app.task(bind=True)
def create_match_task(self, match_data: Dict[str, Any]):
    """Create a new match with proper validation"""
    try:
        db = next(get_db())
        
        # Validate user has sufficient balance
        user = db.query(User).filter(User.id == match_data["user_id"]).first()
        if not user:
            raise Exception("User not found")
        
        wallet = db.query(Wallet).filter(Wallet.user_id == user.id).first()
        if not wallet or wallet.balance < match_data["entry_fee"]:
            raise Exception("Insufficient balance")
        
        # Create match
        match = Match(
            user_id=match_data["user_id"],
            game_type=match_data["game_type"],
            match_type=match_data["match_type"],
            entry_fee=match_data["entry_fee"],
            prize_pool=match_data["entry_fee"] * 1.8,  # 80% return to winner
            status="pending",
            match_data=json.dumps({
                "game_settings": match_data.get("game_settings", {}),
                "player_stats": match_data.get("player_stats", {}),
                "match_config": match_data.get("match_config", {}),
                "created_at": datetime.utcnow().isoformat()
            })
        )
        
        db.add(match)
        
        # Deduct entry fee from wallet
        wallet.balance -= match_data["entry_fee"]
        
        # Create transaction record
        transaction = Transaction(
            wallet_id=wallet.id,
            amount=-match_data["entry_fee"],
            transaction_type="bet",
            status="completed",
            reference=f"MATCH_{match.id}",
            description=f"Entry fee for {match_data['game_type']} match"
        )
        
        db.add(transaction)
        db.commit()
        
        logger.info(f"Match created successfully: {match.id}")
        return {"status": "success", "match_id": match.id}
        
    except Exception as e:
        logger.error(f"Error creating match: {str(e)}")
        db.rollback()
        raise self.retry(exc=e, countdown=60, max_retries=3)

@celery_app.task(bind=True)
def process_game_data_task(self, game_data: Dict[str, Any]):
    """Process incoming game data and update match status"""
    try:
        db = next(get_db())
        
        match = db.query(Match).filter(Match.id == game_data["match_id"]).first()
        if not match:
            raise Exception("Match not found")
        
        # Update match data with new game data
        current_data = json.loads(match.match_data) if match.match_data else {}
        current_data[game_data["event_type"]] = {
            "timestamp": game_data["timestamp"],
            "data": game_data["data"]
        }
        
        match.match_data = json.dumps(current_data)
        
        # Update match status based on event type
        if game_data["event_type"] == "match_start":
            match.status = "active"
        elif game_data["event_type"] == "match_end":
            match.status = "completed"
        
        db.commit()
        
        # Send real-time update via WebSocket (if implemented)
        send_match_update.delay(match.id, game_data)
        
        logger.info(f"Processed game data for match {match.id}")
        return {"status": "success", "event_type": game_data["event_type"]}
        
    except Exception as e:
        logger.error(f"Error processing game data: {str(e)}")
        raise self.retry(exc=e, countdown=30, max_retries=3)

@celery_app.task(bind=True)
def process_match_result_task(self, result_data: Dict[str, Any]):
    """Process final match results and distribute winnings"""
    try:
        db = next(get_db())
        
        match = db.query(Match).filter(Match.id == result_data["match_id"]).first()
        if not match:
            raise Exception("Match not found")
        
        # Validate match result
        if not validate_match_result(result_data):
            raise Exception("Invalid match result")
        
        # Update match with result
        match.status = "completed"
        match.result = "win" if result_data.get("placement", 0) <= 1 else "loss"
        
        # Update match data with final result
        current_data = json.loads(match.match_data) if match.match_data else {}
        current_data["final_result"] = {
            "placement": result_data.get("placement"),
            "kills": result_data.get("kills"),
            "damage": result_data.get("damage"),
            "survival_time": result_data.get("survival_time"),
            "screenshots": result_data.get("screenshots", []),
            "replay_data": result_data.get("replay_data", {}),
            "timestamp": datetime.utcnow().isoformat()
        }
        match.match_data = json.dumps(current_data)
        
        # Distribute winnings if player won
        if match.result == "win":
            distribute_winnings.delay(match.id)
        
        db.commit()
        
        # Send notification
        send_match_notification.delay(match.user_id, match.id, match.result)
        
        logger.info(f"Processed match result for match {match.id}")
        return {"status": "success", "result": match.result}
        
    except Exception as e:
        logger.error(f"Error processing match result: {str(e)}")
        raise self.retry(exc=e, countdown=60, max_retries=3)

@celery_app.task(bind=True)
def process_game_events_task(self, events: List[Dict[str, Any]]):
    """Process real-time game events"""
    try:
        db = next(get_db())
        
        for event in events:
            match = db.query(Match).filter(Match.id == event["match_id"]).first()
            if match:
                # Update match data with event
                current_data = json.loads(match.match_data) if match.match_data else {}
                if "events" not in current_data:
                    current_data["events"] = []
                
                current_data["events"].append({
                    "type": event["event_type"],
                    "timestamp": event["timestamp"],
                    "data": event["event_data"]
                })
                
                match.match_data = json.dumps(current_data)
        
        db.commit()
        
        # Send real-time updates
        for event in events:
            send_match_update.delay(event["match_id"], event)
        
        logger.info(f"Processed {len(events)} game events")
        return {"status": "success", "events_processed": len(events)}
        
    except Exception as e:
        logger.error(f"Error processing game events: {str(e)}")
        raise self.retry(exc=e, countdown=30, max_retries=3)

@celery_app.task(bind=True)
def verify_match_integrity_task(self, match_id: str, verification_data: Dict[str, Any]):
    """Verify match integrity and detect cheating"""
    try:
        db = next(get_db())
        
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            raise Exception("Match not found")
        
        # Perform integrity checks
        integrity_score = perform_integrity_checks(match, verification_data)
        
        # Update match with verification results
        current_data = json.loads(match.match_data) if match.match_data else {}
        current_data["verification"] = {
            "integrity_score": integrity_score,
            "verification_data": verification_data,
            "timestamp": datetime.utcnow().isoformat(),
            "passed": integrity_score >= 0.8
        }
        match.match_data = json.dumps(current_data)
        
        # If integrity check fails, flag for review
        if integrity_score < 0.8:
            flag_match_for_review.delay(match_id, integrity_score)
        
        db.commit()
        
        logger.info(f"Verified match integrity for match {match_id}: {integrity_score}")
        return {"status": "success", "integrity_score": integrity_score}
        
    except Exception as e:
        logger.error(f"Error verifying match integrity: {str(e)}")
        raise self.retry(exc=e, countdown=60, max_retries=3)

@celery_app.task(bind=True)
def distribute_winnings_task(self, match_id: str):
    """Distribute winnings to the winner"""
    try:
        db = next(get_db())
        
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match or match.result != "win":
            raise Exception("Match not found or not won")
        
        user = db.query(User).filter(User.id == match.user_id).first()
        wallet = db.query(Wallet).filter(Wallet.user_id == user.id).first()
        
        if not wallet:
            raise Exception("Wallet not found")
        
        # Add winnings to wallet
        wallet.balance += match.prize_pool
        
        # Create transaction record
        transaction = Transaction(
            wallet_id=wallet.id,
            amount=match.prize_pool,
            transaction_type="win",
            status="completed",
            reference=f"WIN_{match.id}",
            description=f"Winnings from {match.game_type} match"
        )
        
        db.add(transaction)
        db.commit()
        
        logger.info(f"Distributed winnings for match {match_id}: {match.prize_pool}")
        return {"status": "success", "winnings": match.prize_pool}
        
    except Exception as e:
        logger.error(f"Error distributing winnings: {str(e)}")
        raise self.retry(exc=e, countdown=60, max_retries=3)

@celery_app.task(bind=True)
def send_match_update_task(self, match_id: str, update_data: Dict[str, Any]):
    """Send real-time match updates via WebSocket"""
    try:
        # This would integrate with your WebSocket system
        # For now, we'll just log the update
        logger.info(f"Sending match update for {match_id}: {update_data}")
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error sending match update: {str(e)}")
        raise self.retry(exc=e, countdown=30, max_retries=3)

@celery_app.task(bind=True)
def send_match_notification_task(self, user_id: str, match_id: str, result: str):
    """Send match completion notification to user"""
    try:
        # This would integrate with your notification system (email, push, SMS)
        logger.info(f"Sending match notification to user {user_id}: {result}")
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error sending match notification: {str(e)}")
        raise self.retry(exc=e, countdown=30, max_retries=3)

@celery_app.task(bind=True)
def flag_match_for_review_task(self, match_id: str, integrity_score: float):
    """Flag match for manual review due to integrity concerns"""
    try:
        db = next(get_db())
        
        match = db.query(Match).filter(Match.id == match_id).first()
        if match:
            # Update match status to flagged
            match.status = "flagged_for_review"
            
            # Create admin notification
            # This would integrate with your admin notification system
            logger.warning(f"Match {match_id} flagged for review. Integrity score: {integrity_score}")
        
        db.commit()
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error flagging match for review: {str(e)}")
        raise self.retry(exc=e, countdown=60, max_retries=3)

def validate_match_result(result_data: Dict[str, Any]) -> bool:
    """Validate match result data for authenticity"""
    try:
        # Basic validation
        required_fields = ["match_id", "player_id"]
        for field in required_fields:
            if field not in result_data:
                return False
        
        # Validate placement
        placement = result_data.get("placement")
        if placement is not None and (placement < 1 or placement > 100):
            return False
        
        # Validate kills
        kills = result_data.get("kills")
        if kills is not None and (kills < 0 or kills > 50):
            return False
        
        # Add more validation rules as needed
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating match result: {str(e)}")
        return False

def perform_integrity_checks(match: Match, verification_data: Dict[str, Any]) -> float:
    """Perform integrity checks on match data"""
    try:
        score = 1.0
        
        # Check for suspicious patterns
        match_data = json.loads(match.match_data) if match.match_data else {}
        
        # Check for unrealistic scores
        if "final_result" in match_data:
            final_result = match_data["final_result"]
            
            # Check for unrealistic kill count
            kills = final_result.get("kills", 0)
            if kills > 30:  # Suspiciously high kill count
                score -= 0.2
            
            # Check for unrealistic damage
            damage = final_result.get("damage", 0)
            if damage > 5000:  # Suspiciously high damage
                score -= 0.2
            
            # Check for impossible placement with high kills
            placement = final_result.get("placement", 0)
            if placement > 50 and kills > 20:
                score -= 0.3
        
        # Check for replay data consistency
        if "replay_data" in match_data:
            replay_data = match_data["replay_data"]
            # Add replay-based integrity checks here
        
        # Check for screenshot authenticity
        if "screenshots" in match_data:
            screenshots = match_data["screenshots"]
            # Add screenshot verification here
        
        return max(0.0, score)
        
    except Exception as e:
        logger.error(f"Error performing integrity checks: {str(e)}")
        return 0.0

# Legacy task functions for backward compatibility
def create_match_task(match_data: Dict[str, Any]):
    return create_match_task.delay(match_data)

def update_match_result_task(match_id: str, result_data: Dict[str, Any]):
    return process_match_result_task.delay({"match_id": match_id, **result_data})

def get_user_matches_task(user_id: str):
    # This would be implemented as needed
    pass

def get_leaderboard_task(game_type: str = None, limit: int = 100):
    # This would be implemented as needed
    pass