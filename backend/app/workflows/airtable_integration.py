"""
Airtable integration for CODM match workflow automation
Handles automated match processing using Airtable and Zapier
"""

import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import asyncio

logger = logging.getLogger(__name__)

class AirtableCODMWorkflow:
    """Airtable workflow automation for CODM matches"""
    
    def __init__(self, api_key: str, base_id: str):
        self.api_key = api_key
        self.base_id = base_id
        self.base_url = "https://api.airtable.com/v0"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_match_record(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new CODM match record in Airtable"""
        try:
            data = {
                "fields": {
                    "Match ID": match_data["match_id"],
                    "Player ID": match_data["player_id"],
                    "Player Name": match_data.get("player_name", ""),
                    "Game Mode": match_data.get("game_mode", ""),
                    "Kills": match_data.get("kills", 0),
                    "Deaths": match_data.get("deaths", 0),
                    "Assists": match_data.get("assists", 0),
                    "Score": match_data.get("score", 0),
                    "Placement": match_data.get("placement", 0),
                    "Status": "Pending",
                    "Created At": datetime.utcnow().isoformat(),
                    "Screenshots": match_data.get("screenshots", []),
                    "Admin Notes": "",
                    "Confidence Score": match_data.get("confidence_score", 0.0),
                    "Requires Review": match_data.get("requires_review", False)
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/{self.base_id}/CODM_Matches",
                    headers=self.headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Created Airtable record for match {match_data['match_id']}")
                        return {
                            "status": "success",
                            "airtable_record_id": result["id"],
                            "message": "Match record created in Airtable"
                        }
                    else:
                        error_data = await response.json()
                        logger.error(f"Failed to create Airtable record: {error_data}")
                        return {
                            "status": "error",
                            "message": f"Failed to create Airtable record: {response.status}"
                        }
        
        except Exception as e:
            logger.error(f"Error creating Airtable record: {str(e)}")
            return {
                "status": "error",
                "message": f"Airtable error: {str(e)}"
            }
    
    async def update_match_status(self, match_id: str, status: str, admin_notes: str = "") -> Dict[str, Any]:
        """Update match status in Airtable"""
        try:
            # First, get the record ID for the match
            record_id = await self._get_record_id_by_match_id(match_id)
            if not record_id:
                return {
                    "status": "error",
                    "message": f"Match {match_id} not found in Airtable"
                }
            
            data = {
                "fields": {
                    "Status": status,
                    "Admin Notes": admin_notes,
                    "Updated At": datetime.utcnow().isoformat()
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    f"{self.base_url}/{self.base_id}/CODM_Matches/{record_id}",
                    headers=self.headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        logger.info(f"Updated Airtable record for match {match_id}")
                        return {
                            "status": "success",
                            "message": f"Match {match_id} status updated to {status}"
                        }
                    else:
                        error_data = await response.json()
                        logger.error(f"Failed to update Airtable record: {error_data}")
                        return {
                            "status": "error",
                            "message": f"Failed to update Airtable record: {response.status}"
                        }
        
        except Exception as e:
            logger.error(f"Error updating Airtable record: {str(e)}")
            return {
                "status": "error",
                "message": f"Airtable update error: {str(e)}"
            }
    
    async def get_pending_matches(self) -> List[Dict[str, Any]]:
        """Get all pending matches from Airtable"""
        try:
            params = {
                "filterByFormula": "{Status} = 'Pending'",
                "sort[0][field]": "Created At",
                "sort[0][direction]": "desc"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/{self.base_id}/CODM_Matches",
                    headers=self.headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        records = data.get("records", [])
                        
                        pending_matches = []
                        for record in records:
                            fields = record.get("fields", {})
                            pending_matches.append({
                                "record_id": record["id"],
                                "match_id": fields.get("Match ID", ""),
                                "player_id": fields.get("Player ID", ""),
                                "player_name": fields.get("Player Name", ""),
                                "game_mode": fields.get("Game Mode", ""),
                                "kills": fields.get("Kills", 0),
                                "deaths": fields.get("Deaths", 0),
                                "score": fields.get("Score", 0),
                                "created_at": fields.get("Created At", ""),
                                "confidence_score": fields.get("Confidence Score", 0.0),
                                "requires_review": fields.get("Requires Review", False)
                            })
                        
                        return pending_matches
                    else:
                        logger.error(f"Failed to get pending matches: {response.status}")
                        return []
        
        except Exception as e:
            logger.error(f"Error getting pending matches: {str(e)}")
            return []
    
    async def get_match_by_id(self, match_id: str) -> Optional[Dict[str, Any]]:
        """Get specific match by ID from Airtable"""
        try:
            params = {
                "filterByFormula": f"{{Match ID}} = '{match_id}'"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/{self.base_id}/CODM_Matches",
                    headers=self.headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        records = data.get("records", [])
                        
                        if records:
                            record = records[0]
                            fields = record.get("fields", {})
                            return {
                                "record_id": record["id"],
                                "match_id": fields.get("Match ID", ""),
                                "player_id": fields.get("Player ID", ""),
                                "player_name": fields.get("Player Name", ""),
                                "game_mode": fields.get("Game Mode", ""),
                                "kills": fields.get("Kills", 0),
                                "deaths": fields.get("Deaths", 0),
                                "score": fields.get("Score", 0),
                                "status": fields.get("Status", ""),
                                "created_at": fields.get("Created At", ""),
                                "admin_notes": fields.get("Admin Notes", ""),
                                "confidence_score": fields.get("Confidence Score", 0.0)
                            }
                    
                    return None
        
        except Exception as e:
            logger.error(f"Error getting match by ID: {str(e)}")
            return None
    
    async def _get_record_id_by_match_id(self, match_id: str) -> Optional[str]:
        """Get Airtable record ID by match ID"""
        try:
            params = {
                "filterByFormula": f"{{Match ID}} = '{match_id}'"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/{self.base_id}/CODM_Matches",
                    headers=self.headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        records = data.get("records", [])
                        
                        if records:
                            return records[0]["id"]
                    
                    return None
        
        except Exception as e:
            logger.error(f"Error getting record ID: {str(e)}")
            return None
    
    async def create_admin_notification(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create admin notification record in Airtable"""
        try:
            data = {
                "fields": {
                    "Match ID": match_data["match_id"],
                    "Player ID": match_data["player_id"],
                    "Player Name": match_data.get("player_name", ""),
                    "Notification Type": "New Submission",
                    "Priority": "High" if match_data.get("requires_review", False) else "Medium",
                    "Message": f"New CODM submission from {match_data.get('player_name', 'Unknown')}",
                    "Status": "Unread",
                    "Created At": datetime.utcnow().isoformat(),
                    "Action Required": "Review and Approve/Reject"
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/{self.base_id}/Admin_Notifications",
                    headers=self.headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Created admin notification for match {match_data['match_id']}")
                        return {
                            "status": "success",
                            "notification_id": result["id"],
                            "message": "Admin notification created"
                        }
                    else:
                        error_data = await response.json()
                        logger.error(f"Failed to create admin notification: {error_data}")
                        return {
                            "status": "error",
                            "message": f"Failed to create admin notification: {response.status}"
                        }
        
        except Exception as e:
            logger.error(f"Error creating admin notification: {str(e)}")
            return {
                "status": "error",
                "message": f"Admin notification error: {str(e)}"
            }
    
    async def create_player_notification(self, match_id: str, player_id: str, notification_type: str, message: str) -> Dict[str, Any]:
        """Create player notification record in Airtable"""
        try:
            data = {
                "fields": {
                    "Match ID": match_id,
                    "Player ID": player_id,
                    "Notification Type": notification_type,
                    "Message": message,
                    "Status": "Unread",
                    "Created At": datetime.utcnow().isoformat()
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/{self.base_id}/Player_Notifications",
                    headers=self.headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Created player notification for match {match_id}")
                        return {
                            "status": "success",
                            "notification_id": result["id"],
                            "message": "Player notification created"
                        }
                    else:
                        error_data = await response.json()
                        logger.error(f"Failed to create player notification: {error_data}")
                        return {
                            "status": "error",
                            "message": f"Failed to create player notification: {response.status}"
                        }
        
        except Exception as e:
            logger.error(f"Error creating player notification: {str(e)}")
            return {
                "status": "error",
                "message": f"Player notification error: {str(e)}"
            }
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get CODM match statistics from Airtable"""
        try:
            # Get total matches
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/{self.base_id}/CODM_Matches",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        records = data.get("records", [])
                        
                        total_matches = len(records)
                        pending_matches = len([r for r in records if r.get("fields", {}).get("Status") == "Pending"])
                        approved_matches = len([r for r in records if r.get("fields", {}).get("Status") == "Approved"])
                        rejected_matches = len([r for r in records if r.get("fields", {}).get("Status") == "Rejected"])
                        
                        return {
                            "total_matches": total_matches,
                            "pending_matches": pending_matches,
                            "approved_matches": approved_matches,
                            "rejected_matches": rejected_matches,
                            "approval_rate": (approved_matches / total_matches * 100) if total_matches > 0 else 0
                        }
                    else:
                        return {
                            "total_matches": 0,
                            "pending_matches": 0,
                            "approved_matches": 0,
                            "rejected_matches": 0,
                            "approval_rate": 0
                        }
        
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}")
            return {
                "total_matches": 0,
                "pending_matches": 0,
                "approved_matches": 0,
                "rejected_matches": 0,
                "approval_rate": 0
            }

class ZapierIntegration:
    """Zapier integration for automated workflows"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    async def trigger_match_created_webhook(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger Zapier webhook when match is created"""
        try:
            webhook_data = {
                "event": "match_created",
                "match_id": match_data["match_id"],
                "player_id": match_data["player_id"],
                "game_mode": match_data.get("game_mode", ""),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=webhook_data
                ) as response:
                    if response.status == 200:
                        logger.info(f"Triggered Zapier webhook for match {match_data['match_id']}")
                        return {
                            "status": "success",
                            "message": "Zapier webhook triggered"
                        }
                    else:
                        logger.error(f"Failed to trigger Zapier webhook: {response.status}")
                        return {
                            "status": "error",
                            "message": f"Failed to trigger Zapier webhook: {response.status}"
                        }
        
        except Exception as e:
            logger.error(f"Error triggering Zapier webhook: {str(e)}")
            return {
                "status": "error",
                "message": f"Zapier webhook error: {str(e)}"
            }
    
    async def trigger_match_approved_webhook(self, match_id: str, player_id: str) -> Dict[str, Any]:
        """Trigger Zapier webhook when match is approved"""
        try:
            webhook_data = {
                "event": "match_approved",
                "match_id": match_id,
                "player_id": player_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=webhook_data
                ) as response:
                    if response.status == 200:
                        logger.info(f"Triggered Zapier webhook for approved match {match_id}")
                        return {
                            "status": "success",
                            "message": "Zapier webhook triggered"
                        }
                    else:
                        logger.error(f"Failed to trigger Zapier webhook: {response.status}")
                        return {
                            "status": "error",
                            "message": f"Failed to trigger Zapier webhook: {response.status}"
                        }
        
        except Exception as e:
            logger.error(f"Error triggering Zapier webhook: {str(e)}")
            return {
                "status": "error",
                "message": f"Zapier webhook error: {str(e)}"
            }
