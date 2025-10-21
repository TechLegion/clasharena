"""
Game integration services for handling different game APIs and data formats
"""

import requests
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class GameIntegrationService(ABC):
    """Abstract base class for game integration services"""
    
    @abstractmethod
    def get_player_stats(self, player_id: str) -> Dict[str, Any]:
        """Get player statistics from game API"""
        pass
    
    @abstractmethod
    def verify_match_result(self, match_data: Dict[str, Any]) -> bool:
        """Verify match result authenticity"""
        pass
    
    @abstractmethod
    def format_match_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format raw game data into standardized format"""
        pass

class PUBGMobileIntegration(GameIntegrationService):
    """PUBG Mobile integration service"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.pubg.com"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/vnd.api+json"
        }
    
    def get_player_stats(self, player_id: str) -> Dict[str, Any]:
        """Get PUBG Mobile player statistics"""
        try:
            # Get player info
            response = requests.get(
                f"{self.base_url}/shards/steam/players",
                headers=self.headers,
                params={"filter[playerNames]": player_id}
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get PUBG player stats: {response.status_code}")
                return {}
            
            data = response.json()
            player_data = data.get("data", [])
            
            if not player_data:
                return {}
            
            player = player_data[0]
            player_id = player["id"]
            
            # Get match history
            matches_response = requests.get(
                f"{self.base_url}/shards/steam/players/{player_id}/matches",
                headers=self.headers
            )
            
            if matches_response.status_code != 200:
                logger.error(f"Failed to get PUBG match history: {matches_response.status_code}")
                return {}
            
            matches_data = matches_response.json()
            
            return {
                "player_id": player_id,
                "platform": "steam",
                "matches": matches_data.get("data", []),
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting PUBG player stats: {str(e)}")
            return {}
    
    def verify_match_result(self, match_data: Dict[str, Any]) -> bool:
        """Verify PUBG Mobile match result"""
        try:
            match_id = match_data.get("match_id")
            if not match_id:
                return False
            
            # Get match details from PUBG API
            response = requests.get(
                f"{self.base_url}/shards/steam/matches/{match_id}",
                headers=self.headers
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to verify PUBG match: {response.status_code}")
                return False
            
            api_data = response.json()
            match_info = api_data.get("data", {}).get("attributes", {})
            
            # Verify match details
            if match_info.get("gameMode") != match_data.get("game_mode"):
                return False
            
            # Verify player stats
            participants = api_data.get("included", [])
            for participant in participants:
                if participant.get("type") == "participant":
                    participant_data = participant.get("attributes", {})
                    if participant_data.get("stats", {}).get("name") == match_data.get("player_name"):
                        # Verify stats match
                        stats = participant_data.get("stats", {})
                        if stats.get("winPlace") != match_data.get("placement"):
                            return False
                        if stats.get("kills") != match_data.get("kills"):
                            return False
                        break
            
            return True
            
        except Exception as e:
            logger.error(f"Error verifying PUBG match result: {str(e)}")
            return False
    
    def format_match_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format PUBG Mobile data into standardized format"""
        try:
            return {
                "game_type": "pubg_mobile",
                "match_id": raw_data.get("match_id"),
                "player_name": raw_data.get("player_name"),
                "placement": raw_data.get("placement"),
                "kills": raw_data.get("kills"),
                "damage": raw_data.get("damage"),
                "survival_time": raw_data.get("survival_time"),
                "game_mode": raw_data.get("game_mode"),
                "map": raw_data.get("map"),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error formatting PUBG data: {str(e)}")
            return {}

class FreeFireIntegration(GameIntegrationService):
    """Free Fire integration service"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.ff.garena.com"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def get_player_stats(self, player_id: str) -> Dict[str, Any]:
        """Get Free Fire player statistics"""
        try:
            response = requests.get(
                f"{self.base_url}/players/{player_id}",
                headers=self.headers
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get Free Fire player stats: {response.status_code}")
                return {}
            
            data = response.json()
            return {
                "player_id": player_id,
                "platform": "garena",
                "stats": data.get("stats", {}),
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting Free Fire player stats: {str(e)}")
            return {}
    
    def verify_match_result(self, match_data: Dict[str, Any]) -> bool:
        """Verify Free Fire match result"""
        try:
            # Free Fire verification logic
            match_id = match_data.get("match_id")
            if not match_id:
                return False
            
            # Implement Free Fire specific verification
            # This would depend on Free Fire's API structure
            
            return True
            
        except Exception as e:
            logger.error(f"Error verifying Free Fire match result: {str(e)}")
            return False
    
    def format_match_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format Free Fire data into standardized format"""
        try:
            return {
                "game_type": "free_fire",
                "match_id": raw_data.get("match_id"),
                "player_name": raw_data.get("player_name"),
                "placement": raw_data.get("placement"),
                "kills": raw_data.get("kills"),
                "damage": raw_data.get("damage"),
                "survival_time": raw_data.get("survival_time"),
                "game_mode": raw_data.get("game_mode"),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error formatting Free Fire data: {str(e)}")
            return {}

class CallOfDutyIntegration(GameIntegrationService):
    """Call of Duty Mobile integration service"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.callofduty.com"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def get_player_stats(self, player_id: str) -> Dict[str, Any]:
        """Get Call of Duty Mobile player statistics"""
        try:
            response = requests.get(
                f"{self.base_url}/cod/v1/stats/cod/{player_id}",
                headers=self.headers
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get COD player stats: {response.status_code}")
                return {}
            
            data = response.json()
            return {
                "player_id": player_id,
                "platform": "activision",
                "stats": data.get("data", {}),
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting COD player stats: {str(e)}")
            return {}
    
    def verify_match_result(self, match_data: Dict[str, Any]) -> bool:
        """Verify Call of Duty Mobile match result"""
        try:
            # COD verification logic
            match_id = match_data.get("match_id")
            if not match_id:
                return False
            
            # Implement COD specific verification
            
            return True
            
        except Exception as e:
            logger.error(f"Error verifying COD match result: {str(e)}")
            return False
    
    def format_match_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format Call of Duty data into standardized format"""
        try:
            return {
                "game_type": "call_of_duty",
                "match_id": raw_data.get("match_id"),
                "player_name": raw_data.get("player_name"),
                "placement": raw_data.get("placement"),
                "kills": raw_data.get("kills"),
                "deaths": raw_data.get("deaths"),
                "assists": raw_data.get("assists"),
                "score": raw_data.get("score"),
                "game_mode": raw_data.get("game_mode"),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error formatting COD data: {str(e)}")
            return {}

class GameIntegrationFactory:
    """Factory for creating game integration services"""
    
    @staticmethod
    def create_service(game_type: str, api_key: str) -> Optional[GameIntegrationService]:
        """Create appropriate game integration service"""
        services = {
            "pubg_mobile": PUBGMobileIntegration,
            "free_fire": FreeFireIntegration,
            "call_of_duty": CallOfDutyIntegration,
        }
        
        service_class = services.get(game_type)
        if not service_class:
            logger.error(f"Unsupported game type: {game_type}")
            return None
        
        try:
            return service_class(api_key)
        except Exception as e:
            logger.error(f"Error creating {game_type} service: {str(e)}")
            return None

class GameDataValidator:
    """Validates game data for authenticity and integrity"""
    
    @staticmethod
    def validate_screenshot(screenshot_data: Dict[str, Any]) -> bool:
        """Validate screenshot authenticity"""
        try:
            # Check if screenshot exists and has valid metadata
            if not screenshot_data.get("url"):
                return False
            
            # Check if screenshot is recent (within match duration)
            timestamp = screenshot_data.get("timestamp")
            if timestamp:
                screenshot_time = datetime.fromisoformat(timestamp)
                if screenshot_time < datetime.utcnow() - timedelta(hours=2):
                    return False
            
            # Add more validation logic (image analysis, metadata verification, etc.)
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating screenshot: {str(e)}")
            return False
    
    @staticmethod
    def validate_replay_data(replay_data: Dict[str, Any]) -> bool:
        """Validate replay data integrity"""
        try:
            # Check if replay data has required fields
            required_fields = ["duration", "events", "player_actions"]
            for field in required_fields:
                if field not in replay_data:
                    return False
            
            # Check for suspicious patterns in replay data
            events = replay_data.get("events", [])
            if len(events) < 10:  # Suspiciously short match
                return False
            
            # Check for impossible actions (e.g., too many kills in short time)
            kill_events = [e for e in events if e.get("type") == "kill"]
            if len(kill_events) > 50:  # Suspiciously high kill count
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating replay data: {str(e)}")
            return False
    
    @staticmethod
    def validate_match_timing(match_data: Dict[str, Any]) -> bool:
        """Validate match timing consistency"""
        try:
            start_time = match_data.get("start_time")
            end_time = match_data.get("end_time")
            
            if not start_time or not end_time:
                return False
            
            start = datetime.fromisoformat(start_time)
            end = datetime.fromisoformat(end_time)
            
            # Check if match duration is reasonable (5 minutes to 2 hours)
            duration = (end - start).total_seconds()
            if duration < 300 or duration > 7200:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating match timing: {str(e)}")
            return False

class AntiCheatService:
    """Anti-cheat detection service"""
    
    @staticmethod
    def detect_suspicious_patterns(match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect suspicious patterns in match data"""
        try:
            suspicious_indicators = []
            risk_score = 0.0
            
            # Check for unrealistic stats
            kills = match_data.get("kills", 0)
            if kills > 30:
                suspicious_indicators.append("Unrealistic kill count")
                risk_score += 0.3
            
            # Check for impossible accuracy
            accuracy = match_data.get("accuracy", 0)
            if accuracy > 95:
                suspicious_indicators.append("Impossible accuracy")
                risk_score += 0.2
            
            # Check for suspicious timing
            survival_time = match_data.get("survival_time", 0)
            if survival_time > 1800 and kills > 20:  # 30+ minutes with 20+ kills
                suspicious_indicators.append("Suspicious survival time")
                risk_score += 0.2
            
            # Check for rapid score changes
            score_history = match_data.get("score_history", [])
            if len(score_history) > 10:
                rapid_changes = 0
                for i in range(1, len(score_history)):
                    if score_history[i] - score_history[i-1] > 1000:
                        rapid_changes += 1
                
                if rapid_changes > 3:
                    suspicious_indicators.append("Rapid score changes")
                    risk_score += 0.3
            
            return {
                "risk_score": min(1.0, risk_score),
                "suspicious_indicators": suspicious_indicators,
                "requires_review": risk_score > 0.5
            }
            
        except Exception as e:
            logger.error(f"Error detecting suspicious patterns: {str(e)}")
            return {"risk_score": 1.0, "suspicious_indicators": ["Error in analysis"], "requires_review": True}
