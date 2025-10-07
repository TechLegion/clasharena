from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.tasks.match_tasks import (
    create_match_task, 
    update_match_result_task, 
    get_user_matches_task, 
    get_leaderboard_task
)
from shared.models import User

router = APIRouter()

class CreateMatchRequest(BaseModel):
    game_type: str
    match_type: str = "solo"
    entry_fee: float
    game_settings: Optional[dict] = None
    player_stats: Optional[dict] = None
    match_config: Optional[dict] = None

class UpdateMatchRequest(BaseModel):
    result: str
    match_data: Optional[dict] = None
    score: Optional[dict] = None
    screenshots: Optional[List[str]] = None

class TaskResponse(BaseModel):
    task_id: str
    status: str

@router.get("/matches")
async def get_user_matches(
    status: Optional[str] = None,
    game_type: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get matches for current user (synchronous for now)"""
    try:
        from shared.models import Match
        # Get user's matches
        matches = db.query(Match).filter(Match.user_id == current_user.id).all()
        
        # Calculate stats
        total_matches = len(matches)
        won_matches = len([m for m in matches if m.result == "win"])
        total_winnings = sum([m.potential_winnings for m in matches if m.result == "win"])
        
        return {
            "matches": [
                {
                    "id": match.id,
                    "game_type": match.game_type,
                    "match_type": match.match_type,
                    "bet_amount": match.bet_amount,
                    "potential_winnings": match.potential_winnings,
                    "status": match.status,
                    "result": match.result,
                    "created_at": match.created_at
                }
                for match in matches
            ],
            "stats": {
                "total_matches": total_matches,
                "won_matches": won_matches,
                "total_winnings": total_winnings,
                "win_rate": (won_matches / total_matches * 100) if total_matches > 0 else 0
            }
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting user matches: {str(e)}")
        return {"matches": [], "stats": None}

@router.post("/matches", response_model=TaskResponse)
async def create_match(
    match_data: CreateMatchRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Create a new match (async)"""
    match_data_dict = {
        "user_id": current_user.id,
        "game_type": match_data.game_type,
        "match_type": match_data.match_type,
        "entry_fee": match_data.entry_fee,
        "game_settings": match_data.game_settings,
        "player_stats": match_data.player_stats,
        "match_config": match_data.match_config
    }
    task = create_match_task.delay(match_data_dict)
    return TaskResponse(task_id=task.id, status="queued")

@router.put("/matches/{match_id}", response_model=TaskResponse)
async def update_match_result(
    match_id: str,
    result_data: UpdateMatchRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Update match result (async)"""
    result_dict = {
        "result": result_data.result,
        "match_data": result_data.match_data,
        "score": result_data.score,
        "screenshots": result_data.screenshots,
        "won": result_data.result.lower() in ["win", "won", "victory"]
    }
    task = update_match_result_task.delay(match_id, result_dict)
    return TaskResponse(task_id=task.id, status="queued")

@router.get("/leaderboard", response_model=TaskResponse)
async def get_leaderboard(
    game_type: Optional[str] = None,
    limit: int = 100
):
    """Get leaderboard (async)"""
    task = get_leaderboard_task.delay(game_type, limit)
    return TaskResponse(task_id=task.id, status="queued")

@router.get("/games")
async def get_supported_games():
    """Get list of supported games"""
    return {
        "games": [
            {
                "id": "pubg_mobile",
                "name": "PUBG Mobile",
                "description": "Battle royale game with 100 players",
                "supported_match_types": ["solo", "duo", "squad"],
                "min_bet": 100,
                "max_bet": 10000,
                "icon": "🎯"
            },
            {
                "id": "free_fire",
                "name": "Free Fire",
                "description": "Fast-paced battle royale with 50 players",
                "supported_match_types": ["solo", "duo", "squad"],
                "min_bet": 50,
                "max_bet": 5000,
                "icon": "🔥"
            },
            {
                "id": "call_of_duty",
                "name": "Call of Duty Mobile",
                "description": "FPS battle royale and multiplayer",
                "supported_match_types": ["battle_royale", "multiplayer", "ranked"],
                "min_bet": 75,
                "max_bet": 7500,
                "icon": "🎮"
            },
            {
                "id": "fifa_mobile",
                "name": "FIFA Mobile",
                "description": "Football simulation game",
                "supported_match_types": ["friendly", "league", "tournament"],
                "min_bet": 200,
                "max_bet": 20000,
                "icon": "⚽"
            },
            {
                "id": "clash_royale",
                "name": "Clash Royale",
                "description": "Real-time strategy card game",
                "supported_match_types": ["ladder", "challenge", "tournament"],
                "min_bet": 150,
                "max_bet": 15000,
                "icon": "🏰"
            },
            {
                "id": "brawl_stars",
                "name": "Brawl Stars",
                "description": "Fast-paced multiplayer battle game",
                "supported_match_types": ["gem_grab", "brawl_ball", "heist"],
                "min_bet": 100,
                "max_bet": 10000,
                "icon": "⭐"
            }
        ]
    }