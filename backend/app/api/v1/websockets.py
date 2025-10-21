"""
WebSocket endpoints for real-time match updates
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import List, Dict, Any
import json
import logging
from datetime import datetime
import asyncio
from app.core.database import get_db
from shared.models import Match, User

router = APIRouter()
logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        # Active connections by user ID
        self.active_connections: Dict[str, WebSocket] = {}
        # Match-specific connections
        self.match_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept WebSocket connection"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"User {user_id} connected via WebSocket")
    
    def disconnect(self, user_id: str):
        """Remove WebSocket connection"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        logger.info(f"User {user_id} disconnected from WebSocket")
    
    async def send_personal_message(self, message: str, user_id: str):
        """Send message to specific user"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {str(e)}")
                self.disconnect(user_id)
    
    async def send_match_update(self, match_id: str, update_data: Dict[str, Any]):
        """Send match update to all connected users for that match"""
        message = json.dumps({
            "type": "match_update",
            "match_id": match_id,
            "data": update_data,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Send to match-specific connections
        if match_id in self.match_connections:
            for websocket in self.match_connections[match_id]:
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    logger.error(f"Error sending match update: {str(e)}")
        
        # Send to user who owns the match
        db = next(get_db())
        match = db.query(Match).filter(Match.id == match_id).first()
        if match and match.user_id in self.active_connections:
            try:
                await self.active_connections[match.user_id].send_text(message)
            except Exception as e:
                logger.error(f"Error sending match update to owner: {str(e)}")
    
    async def broadcast(self, message: str):
        """Broadcast message to all connected users"""
        for user_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to user {user_id}: {str(e)}")
                self.disconnect(user_id)

# Global connection manager
manager = ConnectionManager()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "subscribe_match":
                match_id = message.get("match_id")
                if match_id:
                    # Add connection to match-specific list
                    if match_id not in manager.match_connections:
                        manager.match_connections[match_id] = []
                    manager.match_connections[match_id].append(websocket)
                    
                    # Send confirmation
                    await websocket.send_text(json.dumps({
                        "type": "subscribed",
                        "match_id": match_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }))
            
            elif message.get("type") == "unsubscribe_match":
                match_id = message.get("match_id")
                if match_id and match_id in manager.match_connections:
                    manager.match_connections[match_id].remove(websocket)
                    
                    # Send confirmation
                    await websocket.send_text(json.dumps({
                        "type": "unsubscribed",
                        "match_id": match_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }))
            
            elif message.get("type") == "ping":
                # Respond to ping with pong
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }))
    
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        logger.info(f"User {user_id} disconnected from WebSocket")

@router.websocket("/ws/match/{match_id}")
async def match_websocket_endpoint(websocket: WebSocket, match_id: str):
    """WebSocket endpoint for match-specific updates"""
    await websocket.accept()
    
    # Add to match connections
    if match_id not in manager.match_connections:
        manager.match_connections[match_id] = []
    manager.match_connections[match_id].append(websocket)
    
    try:
        # Send initial match status
        db = next(get_db())
        match = db.query(Match).filter(Match.id == match_id).first()
        
        if match:
            initial_data = {
                "type": "match_status",
                "match_id": match_id,
                "status": match.status,
                "result": match.result,
                "game_type": match.game_type,
                "match_type": match.match_type,
                "entry_fee": float(match.entry_fee),
                "prize_pool": float(match.prize_pool),
                "created_at": match.created_at.isoformat(),
                "updated_at": match.updated_at.isoformat()
            }
            
            await websocket.send_text(json.dumps(initial_data))
        
        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }))
    
    except WebSocketDisconnect:
        # Remove from match connections
        if match_id in manager.match_connections:
            manager.match_connections[match_id].remove(websocket)
        logger.info(f"Disconnected from match {match_id} WebSocket")

# Utility functions for sending updates
async def send_match_update(match_id: str, update_type: str, data: Dict[str, Any]):
    """Send match update to all connected clients"""
    update_data = {
        "update_type": update_type,
        "data": data
    }
    await manager.send_match_update(match_id, update_data)

async def send_user_notification(user_id: str, notification_type: str, data: Dict[str, Any]):
    """Send notification to specific user"""
    message = json.dumps({
        "type": "notification",
        "notification_type": notification_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    })
    await manager.send_personal_message(message, user_id)

async def broadcast_system_message(message: str):
    """Broadcast system message to all connected users"""
    system_message = json.dumps({
        "type": "system_message",
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    })
    await manager.broadcast(system_message)
