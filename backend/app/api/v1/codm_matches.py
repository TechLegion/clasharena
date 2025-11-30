"""
CODM-specific match endpoints for ClashArena
Handles Call of Duty Mobile match automation and result processing
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.api.deps import get_current_active_user, get_current_admin_user
from app.core.database import get_db
from app.services.codm_integration import CODMIntegrationService, CODMAdminTools, CODMWorkflowAutomation
from shared.models import User
import json
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class CODMSubmissionRequest(BaseModel):
    """CODM match result submission request"""
    match_id: str
    game_mode: str  # battle_royale, multiplayer, ranked, etc.
    kills: int
    deaths: int
    assists: int
    score: int
    placement: Optional[int] = None  # For battle royale
    match_duration: Optional[int] = None  # In seconds
    weapon_stats: Optional[Dict[str, Any]] = None
    additional_notes: Optional[str] = None

class CODMAdminDecision(BaseModel):
    """Admin decision for CODM match verification"""
    approved: bool
    admin_notes: str
    confidence_score: Optional[float] = None
    flag_reason: Optional[str] = None

class CODMSubmissionResponse(BaseModel):
    """Response for CODM submission"""
    status: str
    message: str
    submission_id: Optional[str] = None
    requires_review: bool = False
    estimated_processing_time: Optional[str] = None

@router.post("/submit-result", response_model=CODMSubmissionResponse)
async def submit_codm_result(
    submission: CODMSubmissionRequest,
    screenshots: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Submit CODM match result with screenshots
    This is the primary endpoint for CODM match automation
    """
    try:
        # Initialize CODM integration service
        codm_service = CODMIntegrationService()
        
        # Process uploaded screenshots
        screenshot_urls = []
        for screenshot in screenshots:
            # In a real implementation, you'd upload to cloud storage
            # For now, we'll store the file info
            screenshot_urls.append({
                "filename": screenshot.filename,
                "content_type": screenshot.content_type,
                "size": screenshot.size
            })
        
        # Prepare submission data
        submission_data = {
            "match_id": submission.match_id,
            "player_id": current_user.id,
            "game_mode": submission.game_mode,
            "kills": submission.kills,
            "deaths": submission.deaths,
            "assists": submission.assists,
            "score": submission.score,
            "placement": submission.placement,
            "match_duration": submission.match_duration,
            "weapon_stats": submission.weapon_stats,
            "additional_notes": submission.additional_notes,
            "screenshots": screenshot_urls,
            "submitted_at": datetime.utcnow().isoformat()
        }
        
        # Process submission
        result = await codm_service.process_manual_submission(submission_data)
        
        if result["status"] == "success":
            return CODMSubmissionResponse(
                status="success",
                message="CODM match result submitted successfully",
                submission_id=result["match_report"]["match_id"],
                requires_review=result["match_report"]["requires_admin_review"],
                estimated_processing_time="5-15 minutes"
            )
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    
    except Exception as e:
        logger.error(f"Error submitting CODM result: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/submissions")
async def get_codm_submissions(
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get CODM submissions for current user"""
    try:
        # This would query your database for user's CODM submissions
        # For now, return mock data
        submissions = [
            {
                "id": "sub_123",
                "match_id": "match_456",
                "game_mode": "battle_royale",
                "kills": 15,
                "deaths": 3,
                "score": 2500,
                "placement": 1,
                "status": "pending",
                "submitted_at": "2024-01-15T10:00:00Z"
            }
        ]
        
        return {
            "submissions": submissions,
            "total": len(submissions),
            "page": page,
            "limit": limit
        }
    
    except Exception as e:
        logger.error(f"Error getting CODM submissions: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/admin/pending")
async def get_pending_codm_submissions(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get pending CODM submissions for admin review"""
    try:
        admin_tools = CODMAdminTools()
        pending_submissions = await admin_tools.get_pending_submissions()
        
        return {
            "pending_submissions": pending_submissions,
            "total_pending": len(pending_submissions)
        }
    
    except Exception as e:
        logger.error(f"Error getting pending submissions: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/admin/verify/{match_id}")
async def verify_codm_submission(
    match_id: str,
    decision: CODMAdminDecision,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Admin verification of CODM submission"""
    try:
        codm_service = CODMIntegrationService()
        
        admin_decision = {
            "approved": decision.approved,
            "admin_notes": decision.admin_notes,
            "confidence_score": decision.confidence_score,
            "flag_reason": decision.flag_reason,
            "admin_id": current_user.id,
            "processed_at": datetime.utcnow().isoformat()
        }
        
        result = await codm_service.process_admin_verification(match_id, admin_decision)
        
        if result["status"] == "success":
            return {
                "status": "success",
                "message": f"Match {match_id} verification processed",
                "verification_result": result["verification_result"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    
    except Exception as e:
        logger.error(f"Error verifying CODM submission: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/admin/approve/{match_id}")
async def approve_codm_submission(
    match_id: str,
    admin_notes: str = "",
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Approve CODM submission"""
    try:
        admin_tools = CODMAdminTools()
        result = await admin_tools.approve_submission(match_id, admin_notes)
        
        if result["status"] == "success":
            return {
                "status": "success",
                "message": f"Match {match_id} approved",
                "processed_at": result["processed_at"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    
    except Exception as e:
        logger.error(f"Error approving CODM submission: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/admin/reject/{match_id}")
async def reject_codm_submission(
    match_id: str,
    rejection_reason: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Reject CODM submission"""
    try:
        admin_tools = CODMAdminTools()
        result = await admin_tools.reject_submission(match_id, rejection_reason)
        
        if result["status"] == "success":
            return {
                "status": "success",
                "message": f"Match {match_id} rejected: {rejection_reason}",
                "processed_at": result["processed_at"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    
    except Exception as e:
        logger.error(f"Error rejecting CODM submission: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/admin/flag/{match_id}")
async def flag_codm_submission(
    match_id: str,
    flag_reason: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Flag CODM submission for additional review"""
    try:
        admin_tools = CODMAdminTools()
        result = await admin_tools.flag_for_review(match_id, flag_reason)
        
        if result["status"] == "success":
            return {
                "status": "success",
                "message": f"Match {match_id} flagged for review: {flag_reason}",
                "processed_at": result["processed_at"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    
    except Exception as e:
        logger.error(f"Error flagging CODM submission: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/stats")
async def get_codm_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get CODM player statistics"""
    try:
        # This would calculate stats from user's CODM matches
        stats = {
            "total_matches": 0,
            "wins": 0,
            "losses": 0,
            "total_kills": 0,
            "total_deaths": 0,
            "average_kd": 0.0,
            "best_kills": 0,
            "win_rate": 0.0,
            "total_earnings": 0.0
        }
        
        return {
            "player_id": current_user.id,
            "stats": stats,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting CODM stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/leaderboard")
async def get_codm_leaderboard(
    game_mode: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get CODM leaderboard"""
    try:
        # This would query your database for CODM leaderboard
        leaderboard = [
            {
                "rank": 1,
                "player_id": "player_123",
                "player_name": "ProGamer",
                "total_kills": 1500,
                "total_wins": 100,
                "kd_ratio": 3.5,
                "win_rate": 85.5
            }
        ]
        
        return {
            "game_mode": game_mode or "all",
            "leaderboard": leaderboard,
            "total_players": len(leaderboard),
            "updated_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting CODM leaderboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/game-modes")
async def get_codm_game_modes():
    """Get supported CODM game modes"""
    return {
        "game_modes": [
            {
                "id": "battle_royale",
                "name": "Battle Royale",
                "description": "100-player battle royale",
                "max_players": 100,
                "min_bet": 100,
                "max_bet": 10000
            },
            {
                "id": "multiplayer",
                "name": "Multiplayer",
                "description": "Team-based multiplayer matches",
                "max_players": 10,
                "min_bet": 50,
                "max_bet": 5000
            },
            {
                "id": "ranked",
                "name": "Ranked",
                "description": "Competitive ranked matches",
                "max_players": 10,
                "min_bet": 200,
                "max_bet": 20000
            }
        ]
    }
