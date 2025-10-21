"""
Webhook endpoints for receiving game data from external sources
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any
import hashlib
import hmac
import json
import logging
from datetime import datetime
from app.core.database import get_db
from app.tasks.match_tasks import process_game_data_task
from shared.models import Match

router = APIRouter()
logger = logging.getLogger(__name__)

class GameDataPayload(BaseModel):
    """Standardized game data payload"""
    match_id: str
    game_type: str
    player_id: str
    event_type: str  # match_start, match_end, score_update, etc.
    timestamp: datetime
    data: Dict[str, Any]
    verification_hash: Optional[str] = None

class MatchResultData(BaseModel):
    """Match result data from game"""
    match_id: str
    player_id: str
    final_score: Optional[Dict[str, Any]] = None
    placement: Optional[int] = None
    kills: Optional[int] = None
    damage: Optional[float] = None
    survival_time: Optional[int] = None
    screenshots: Optional[list] = None
    replay_data: Optional[Dict[str, Any]] = None
    verification_data: Optional[Dict[str, Any]] = None

class GameEventData(BaseModel):
    """Real-time game event data"""
    match_id: str
    player_id: str
    event_type: str
    timestamp: datetime
    event_data: Dict[str, Any]

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify webhook signature for security"""
    try:
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {str(e)}")
        return False

@router.post("/game-data")
async def receive_game_data(
    request: Request,
    game_data: GameDataPayload,
    db = Depends(get_db)
):
    """
    Receive game data from external game clients or third-party services
    This endpoint handles real-time game data updates
    """
    try:
        # Verify webhook signature if provided
        if game_data.verification_hash:
            body = await request.body()
            signature = request.headers.get("X-Signature", "")
            webhook_secret = "your-webhook-secret"  # Get from config
            
            if not verify_webhook_signature(body, signature, webhook_secret):
                raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Process game data asynchronously
        task = process_game_data_task.delay(game_data.dict())
        
        logger.info(f"Received game data for match {game_data.match_id}, event: {game_data.event_type}")
        
        return {
            "status": "success",
            "message": "Game data received and queued for processing",
            "task_id": task.id,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error processing game data: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/match-result")
async def receive_match_result(
    request: Request,
    result_data: MatchResultData,
    db = Depends(get_db)
):
    """
    Receive final match results from game clients
    This is the primary endpoint for match completion data
    """
    try:
        # Verify the match exists and is active
        match = db.query(Match).filter(Match.id == result_data.match_id).first()
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        
        if match.status != "active":
            raise HTTPException(status_code=400, detail="Match is not active")
        
        # Verify webhook signature
        body = await request.body()
        signature = request.headers.get("X-Signature", "")
        webhook_secret = "your-webhook-secret"  # Get from config
        
        if not verify_webhook_signature(body, signature, webhook_secret):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Process match result asynchronously
        from app.tasks.match_tasks import process_match_result_task
        task = process_match_result_task.delay(result_data.dict())
        
        logger.info(f"Received match result for match {result_data.match_id}")
        
        return {
            "status": "success",
            "message": "Match result received and queued for processing",
            "task_id": task.id,
            "timestamp": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing match result: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/game-events")
async def receive_game_events(
    request: Request,
    events: list[GameEventData],
    db = Depends(get_db)
):
    """
    Receive real-time game events (kills, deaths, score updates, etc.)
    This endpoint handles streaming game data
    """
    try:
        # Verify webhook signature
        body = await request.body()
        signature = request.headers.get("X-Signature", "")
        webhook_secret = "your-webhook-secret"  # Get from config
        
        if not verify_webhook_signature(body, signature, webhook_secret):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Process events asynchronously
        from app.tasks.match_tasks import process_game_events_task
        task = process_game_events_task.delay([event.dict() for event in events])
        
        logger.info(f"Received {len(events)} game events")
        
        return {
            "status": "success",
            "message": f"Processed {len(events)} game events",
            "task_id": task.id,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error processing game events: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/match/{match_id}/status")
async def get_match_status(
    match_id: str,
    db = Depends(get_db)
):
    """Get real-time match status"""
    try:
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        
        return {
            "match_id": match_id,
            "status": match.status,
            "result": match.result,
            "updated_at": match.updated_at,
            "game_data": json.loads(match.match_data) if match.match_data else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting match status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/verify-match")
async def verify_match_integrity(
    request: Request,
    match_id: str,
    verification_data: Dict[str, Any],
    db = Depends(get_db)
):
    """
    Verify match integrity and detect cheating
    This endpoint handles anti-cheat verification
    """
    try:
        # Verify webhook signature
        body = await request.body()
        signature = request.headers.get("X-Signature", "")
        webhook_secret = "your-webhook-secret"  # Get from config
        
        if not verify_webhook_signature(body, signature, webhook_secret):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Process verification asynchronously
        from app.tasks.match_tasks import verify_match_integrity_task
        task = verify_match_integrity_task.delay(match_id, verification_data)
        
        logger.info(f"Received verification request for match {match_id}")
        
        return {
            "status": "success",
            "message": "Match verification queued",
            "task_id": task.id,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error processing match verification: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
