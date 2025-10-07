from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
import json
import uuid
import logging

logger = logging.getLogger(__name__)

from shared.database import get_db, init_db
from shared.models import User, Match, Wallet, Transaction

app = FastAPI(title="ClashArena Match Service", version="1.0.0")

# Initialize database
init_db()

# Pydantic Models for Request Validation
class GameSettings(BaseModel):
    max_players: Optional[int] = Field(None, ge=2, le=10)
    duration: Optional[int] = Field(None, ge=60, le=3600)
    map_type: Optional[str] = Field(None, pattern="^(arena|clan_wars|challenges)$")

class CreateMatchRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100)
    bet_amount: float = Field(..., gt=0, le=1000000, description="Bet amount in NGN")
    game_type: str = Field(..., pattern="^(clash_royale|clash_of_clans|brawl_stars)$")
    match_type: str = Field(..., pattern="^(casual|ranked|tournament)$")
    game_settings: Optional[GameSettings] = Field(default_factory=GameSettings)
    
    @validator('bet_amount')
    def validate_bet_amount(cls, v, values):
        if 'game_type' in values and 'match_type' in values:
            game = values['game_type']
            match_type = values['match_type']
            
            # Minimum bet requirements
            min_bets = {
                'clash_royale': {'casual': 100, 'ranked': 500, 'tournament': 1000},
                'clash_of_clans': {'casual': 200, 'ranked': 1000, 'tournament': 2000},
                'brawl_stars': {'casual': 150, 'ranked': 750, 'tournament': 1500}
            }
            
            # Maximum bet limits
            max_bets = {
                'clash_royale': {'casual': 10000, 'ranked': 50000, 'tournament': 100000},
                'clash_of_clans': {'casual': 20000, 'ranked': 100000, 'tournament': 200000},
                'brawl_stars': {'casual': 15000, 'ranked': 75000, 'tournament': 150000}
            }
            
            min_bet = min_bets.get(game, {}).get(match_type, 0)
            max_bet = max_bets.get(game, {}).get(match_type, float('inf'))
            
            if v < min_bet:
                raise ValueError(f'Bet amount {v} too low for {game} {match_type}. Minimum: {min_bet}')
            if v > max_bet:
                raise ValueError(f'Bet amount {v} too high for {game} {match_type}. Maximum: {max_bet}')
        
        return v

class UpdateMatchRequest(BaseModel):
    status: Optional[str] = Field(None, pattern="^(pending|in_progress|completed|cancelled)$")
    result: Optional[str] = Field(None, pattern="^(win|loss|draw)$")
    match_data: Optional[dict] = Field(default_factory=dict)

@app.get("/")
async def root():
    return {"message": "ClashArena Match Service", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "match-service"}

@app.get("/matches")
async def get_matches(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    game_type: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get matches with optional filtering"""
    try:
        query = db.query(Match)
        
        if user_id:
            query = query.filter(Match.user_id == user_id)
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
                    "bet_amount": match.bet_amount,
                    "potential_winnings": match.potential_winnings,
                    "opponent_id": match.opponent_id,
                    "result": match.result,
                    "match_data": json.loads(match.match_data) if match.match_data else None,
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

@app.post("/matches")
async def create_match(
    match_data: CreateMatchRequest, 
    current_user_id: str,  # From auth middleware
    db: Session = Depends(get_db)
):
    """Create a new match with proper security and race condition prevention"""
    try:
        # CRITICAL: Verify user is creating match for themselves
        if match_data.user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create match for another user"
            )
        
        # CRITICAL: Lock wallet for atomic operation (prevents race conditions)
        wallet = db.query(Wallet).filter(
            Wallet.user_id == match_data.user_id
        ).with_for_update().first()
        
        if not wallet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Wallet not found"
            )
        
        # Calculate potential winnings based on match type
        multipliers = {
            "tournament": 2.5,
            "ranked": 2.0,
            "casual": 1.8
        }
        potential_winnings = match_data.bet_amount * multipliers[match_data.match_type]
        
        # Create match (not committed yet)
        new_match = Match(
            user_id=match_data.user_id,
            game_type=match_data.game_type,
            match_type=match_data.match_type,
            bet_amount=match_data.bet_amount,
            potential_winnings=potential_winnings,
            match_data=json.dumps({
                "game_settings": match_data.game_settings.dict() if match_data.game_settings else {},
                "created_at": datetime.utcnow().isoformat()
            })
        )
        db.add(new_match)
        db.flush()  # Get ID without committing
        
        # CRITICAL: Atomically deduct bet with balance check (prevents race conditions)
        result = db.query(Wallet).filter(
            Wallet.id == wallet.id,
            Wallet.balance >= match_data.bet_amount
        ).update({
            Wallet.balance: Wallet.balance - match_data.bet_amount,
            Wallet.updated_at: datetime.utcnow()
        }, synchronize_session=False)
        
        if result == 0:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient balance"
            )
        
        # Create transaction record
        transaction = Transaction(
            wallet_id=wallet.id,
            amount=-match_data.bet_amount,
            transaction_type="bet",
            status="completed",
            reference=f"bet_{new_match.id}",
            description=f"Bet for {match_data.game_type} {match_data.match_type} match"
        )
        db.add(transaction)
        
        # CRITICAL: Commit everything together (atomic transaction)
        db.commit()
        db.refresh(new_match)
        
        logger.info(
            f"Match created successfully: {new_match.id}",
            extra={
                "user_id": match_data.user_id,
                "bet_amount": match_data.bet_amount,
                "match_type": match_data.match_type,
                "game_type": match_data.game_type
            }
        )
        
        return {
            "status": "success",
            "match": {
                "id": new_match.id,
                "user_id": new_match.user_id,
                "game_type": new_match.game_type,
                "match_type": new_match.match_type,
                "status": new_match.status,
                "bet_amount": new_match.bet_amount,
                "potential_winnings": new_match.potential_winnings,
                "created_at": new_match.created_at
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Match creation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Match creation failed"
        )

@app.put("/matches/{match_id}")
async def update_match(
    match_id: str, 
    update_data: UpdateMatchRequest,
    current_user_id: str,  # From auth middleware
    db: Session = Depends(get_db)
):
    """Update match details with proper authorization and idempotency"""
    try:
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Match not found"
            )
        
        # CRITICAL: Authorization check - only match owner can update
        if match.user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this match"
            )
        
        # Update match fields with state machine validation
        if update_data.status:
            # Validate state transitions
            valid_transitions = {
                'pending': ['in_progress', 'cancelled'],
                'in_progress': ['completed', 'cancelled'],
                'completed': [],  # Terminal state
                'cancelled': []   # Terminal state
            }
            
            if update_data.status not in valid_transitions.get(match.status, []):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot transition from {match.status} to {update_data.status}"
                )
            
            match.status = update_data.status
        
        # CRITICAL: Prevent users from setting their own result (only game server should)
        if update_data.result:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Match result must be set by game server only"
            )
        
        if update_data.match_data:
            # Validate and sanitize match data
            match.match_data = json.dumps(update_data.match_data)
        
        match.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(
            f"Match updated: {match_id}",
            extra={
                "user_id": current_user_id,
                "match_id": match_id,
                "status": match.status,
                "updated_fields": list(update_data.dict(exclude_unset=True).keys())
            }
        )
        
        return {
            "status": "success",
            "match": {
                "id": match.id,
                "user_id": match.user_id,
                "game_type": match.game_type,
                "match_type": match.match_type,
                "status": match.status,
                "result": match.result,
                "bet_amount": match.bet_amount,
                "potential_winnings": match.potential_winnings,
                "updated_at": match.updated_at
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Match update failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Match update failed"
        )

@app.post("/matches/{match_id}/result")
async def set_match_result(
    match_id: str,
    result_data: dict,
    db: Session = Depends(get_db)
):
    """Set match result - ONLY for game servers (secure endpoint)"""
    try:
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Match not found"
            )
        
        # CRITICAL: Only allow result to be set once
        if match.result is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Match result already set"
            )
        
        result = result_data.get("result")
        if result not in ["win", "loss", "draw"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid result. Must be 'win', 'loss', or 'draw'"
            )
        
        # Set result and status
        match.result = result
        match.status = "completed"
        match.updated_at = datetime.utcnow()
        
        # Process match result with idempotency protection
        await process_match_result(match, db)
        
        db.commit()
        db.refresh(match)
        
        logger.info(
            f"Match result set: {match_id} = {result}",
            extra={
                "match_id": match_id,
                "user_id": match.user_id,
                "result": result,
                "bet_amount": match.bet_amount,
                "potential_winnings": match.potential_winnings
            }
        )
        
        return {
            "status": "success",
            "message": f"Match result set to {result}",
            "match": {
                "id": match.id,
                "result": match.result,
                "status": match.status,
                "bet_amount": match.bet_amount,
                "potential_winnings": match.potential_winnings
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Set match result failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set match result"
        )

@app.get("/matches/{match_id}")
async def get_match(match_id: str, db: Session = Depends(get_db)):
    """Get specific match details"""
    try:
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Match not found"
            )
        
        return {
            "id": match.id,
            "user_id": match.user_id,
            "game_type": match.game_type,
            "match_type": match.match_type,
            "status": match.status,
            "result": match.result,
            "bet_amount": match.bet_amount,
            "potential_winnings": match.potential_winnings,
            "opponent_id": match.opponent_id,
            "match_data": json.loads(match.match_data) if match.match_data else None,
            "created_at": match.created_at,
            "updated_at": match.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

async def process_match_result(match: Match, db: Session):
    """Process match result with idempotency protection and atomic operations"""
    try:
        # CRITICAL: Check for existing transaction to prevent double-payout
        existing_win_tx = db.query(Transaction).filter(
            Transaction.reference == f"win_{match.id}"
        ).first()
        
        existing_refund_tx = db.query(Transaction).filter(
            Transaction.reference == f"refund_{match.id}"
        ).first()
        
        if existing_win_tx or existing_refund_tx:
            logger.warning(f"Match result already processed: {match.id}")
            return  # Already processed, prevent double-payout
        
        wallet = db.query(Wallet).filter(Wallet.user_id == match.user_id).first()
        if not wallet:
            logger.error(f"Wallet not found for user: {match.user_id}")
            return
        
        if match.result == "win":
            # CRITICAL: Use atomic update to prevent race conditions
            result = db.query(Wallet).filter(
                Wallet.id == wallet.id
            ).update({
                Wallet.balance: Wallet.balance + match.potential_winnings,
                Wallet.updated_at: datetime.utcnow()
            })
            
            if result == 0:
                logger.error(f"Failed to update wallet balance for wallet: {wallet.id}")
                return
            
            # Create transaction record for winnings
            transaction = Transaction(
                wallet_id=wallet.id,
                amount=match.potential_winnings,
                transaction_type="win",
                status="completed",
                reference=f"win_{match.id}",
                description=f"Winnings from {match.game_type} {match.match_type} match"
            )
            db.add(transaction)
            
            logger.info(
                f"Match winnings processed: {match.id}",
                extra={
                    "match_id": match.id,
                    "user_id": match.user_id,
                    "winnings": match.potential_winnings
                }
            )
            
        elif match.result == "draw":
            # CRITICAL: Use atomic update for refund
            result = db.query(Wallet).filter(
                Wallet.id == wallet.id
            ).update({
                Wallet.balance: Wallet.balance + match.bet_amount,
                Wallet.updated_at: datetime.utcnow()
            })
            
            if result == 0:
                logger.error(f"Failed to update wallet balance for refund: {wallet.id}")
                return
            
            # Create transaction record for refund
            transaction = Transaction(
                wallet_id=wallet.id,
                amount=match.bet_amount,
                transaction_type="refund",
                status="completed",
                reference=f"refund_{match.id}",
                description=f"Refund from {match.game_type} {match.match_type} match (draw)"
            )
            db.add(transaction)
            
            logger.info(
                f"Match refund processed: {match.id}",
                extra={
                    "match_id": match.id,
                    "user_id": match.user_id,
                    "refund_amount": match.bet_amount
                }
            )
        
        # Loss case: bet amount is already deducted, no additional action needed
        
    except Exception as e:
        logger.error(f"Match result processing failed: {str(e)}", exc_info=True)
        raise e

@app.get("/games")
async def get_supported_games():
    """Get list of supported games"""
    return {
        "games": [
            {
                "id": "clash_royale",
                "name": "Clash Royale",
                "description": "Real-time multiplayer battle game",
                "supported_match_types": ["casual", "ranked", "tournament"],
                "min_bet": 100,
                "max_bet": 10000
            },
            {
                "id": "clash_of_clans",
                "name": "Clash of Clans",
                "description": "Strategy game with base building and battles",
                "supported_match_types": ["casual", "ranked", "tournament"],
                "min_bet": 200,
                "max_bet": 20000
            },
            {
                "id": "brawl_stars",
                "name": "Brawl Stars",
                "description": "Fast-paced multiplayer battle game",
                "supported_match_types": ["casual", "ranked", "tournament"],
                "min_bet": 150,
                "max_bet": 15000
            }
        ]
    }

@app.get("/leaderboard")
async def get_leaderboard(
    game_type: Optional[str] = None,
    match_type: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get leaderboard for matches"""
    try:
        query = db.query(Match).filter(Match.status == "completed")
        
        if game_type:
            query = query.filter(Match.game_type == game_type)
        if match_type:
            query = query.filter(Match.match_type == match_type)
        
        # Get winning matches
        winning_matches = query.filter(Match.result == "win").all()
        
        # Calculate user statistics
        user_stats = {}
        for match in winning_matches:
            user_id = match.user_id
            if user_id not in user_stats:
                user_stats[user_id] = {
                    "user_id": user_id,
                    "total_winnings": 0,
                    "matches_won": 0,
                    "total_bet": 0
                }
            
            user_stats[user_id]["total_winnings"] += match.potential_winnings
            user_stats[user_id]["matches_won"] += 1
            user_stats[user_id]["total_bet"] += match.bet_amount
        
        # Sort by total winnings
        leaderboard = sorted(user_stats.values(), key=lambda x: x["total_winnings"], reverse=True)[:limit]
        
        return {
            "leaderboard": leaderboard,
            "game_type": game_type,
            "match_type": match_type
        }
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
