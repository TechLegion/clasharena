"""
Match validation service for verifying match results and detecting cheating
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from PIL import Image
import hashlib
import requests
from io import BytesIO

logger = logging.getLogger(__name__)

class MatchValidator:
    """Validates match results and detects cheating"""
    
    def __init__(self):
        self.suspicious_patterns = []
        self.validation_rules = self._load_validation_rules()
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules for different games"""
        return {
            "pubg_mobile": {
                "max_kills": 30,
                "max_damage": 5000,
                "min_survival_time": 30,
                "max_survival_time": 1800,
                "max_accuracy": 95
            },
            "free_fire": {
                "max_kills": 25,
                "max_damage": 3000,
                "min_survival_time": 60,
                "max_survival_time": 1200,
                "max_accuracy": 90
            },
            "call_of_duty": {
                "max_kills": 40,
                "max_damage": 6000,
                "min_survival_time": 120,
                "max_survival_time": 2400,
                "max_accuracy": 98
            }
        }
    
    def validate_match_result(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive match result validation"""
        try:
            validation_result = {
                "is_valid": True,
                "confidence_score": 1.0,
                "warnings": [],
                "errors": [],
                "suspicious_indicators": []
            }
            
            game_type = match_data.get("game_type")
            if not game_type:
                validation_result["errors"].append("Missing game type")
                validation_result["is_valid"] = False
                return validation_result
            
            # Validate basic match data
            self._validate_basic_data(match_data, validation_result)
            
            # Validate game-specific data
            self._validate_game_specific_data(match_data, validation_result)
            
            # Validate screenshots
            if match_data.get("screenshots"):
                self._validate_screenshots(match_data["screenshots"], validation_result)
            
            # Validate replay data
            if match_data.get("replay_data"):
                self._validate_replay_data(match_data["replay_data"], validation_result)
            
            # Check for suspicious patterns
            self._check_suspicious_patterns(match_data, validation_result)
            
            # Calculate final confidence score
            validation_result["confidence_score"] = self._calculate_confidence_score(validation_result)
            
            # Determine if match is valid
            if validation_result["confidence_score"] < 0.7:
                validation_result["is_valid"] = False
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating match result: {str(e)}")
            return {
                "is_valid": False,
                "confidence_score": 0.0,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": [],
                "suspicious_indicators": []
            }
    
    def _validate_basic_data(self, match_data: Dict[str, Any], validation_result: Dict[str, Any]):
        """Validate basic match data"""
        required_fields = ["match_id", "player_id", "placement", "kills"]
        
        for field in required_fields:
            if field not in match_data:
                validation_result["errors"].append(f"Missing required field: {field}")
                validation_result["is_valid"] = False
        
        # Validate placement
        placement = match_data.get("placement")
        if placement is not None:
            if placement < 1 or placement > 100:
                validation_result["errors"].append("Invalid placement value")
                validation_result["is_valid"] = False
        
        # Validate kills
        kills = match_data.get("kills")
        if kills is not None:
            if kills < 0 or kills > 100:
                validation_result["errors"].append("Invalid kill count")
                validation_result["is_valid"] = False
    
    def _validate_game_specific_data(self, match_data: Dict[str, Any], validation_result: Dict[str, Any]):
        """Validate game-specific data"""
        game_type = match_data.get("game_type")
        rules = self.validation_rules.get(game_type, {})
        
        if not rules:
            validation_result["warnings"].append(f"No validation rules for game type: {game_type}")
            return
        
        # Check kills against game limits
        kills = match_data.get("kills", 0)
        max_kills = rules.get("max_kills", 50)
        if kills > max_kills:
            validation_result["suspicious_indicators"].append(f"Kill count ({kills}) exceeds normal limit ({max_kills})")
            validation_result["confidence_score"] -= 0.2
        
        # Check damage against game limits
        damage = match_data.get("damage", 0)
        max_damage = rules.get("max_damage", 10000)
        if damage > max_damage:
            validation_result["suspicious_indicators"].append(f"Damage ({damage}) exceeds normal limit ({max_damage})")
            validation_result["confidence_score"] -= 0.2
        
        # Check survival time
        survival_time = match_data.get("survival_time", 0)
        min_survival = rules.get("min_survival_time", 30)
        max_survival = rules.get("max_survival_time", 1800)
        
        if survival_time < min_survival:
            validation_result["warnings"].append(f"Survival time ({survival_time}s) is unusually short")
        
        if survival_time > max_survival:
            validation_result["suspicious_indicators"].append(f"Survival time ({survival_time}s) exceeds normal limit ({max_survival}s)")
            validation_result["confidence_score"] -= 0.1
        
        # Check accuracy
        accuracy = match_data.get("accuracy", 0)
        max_accuracy = rules.get("max_accuracy", 95)
        if accuracy > max_accuracy:
            validation_result["suspicious_indicators"].append(f"Accuracy ({accuracy}%) exceeds normal limit ({max_accuracy}%)")
            validation_result["confidence_score"] -= 0.3
    
    def _validate_screenshots(self, screenshots: List[Dict[str, Any]], validation_result: Dict[str, Any]):
        """Validate screenshot authenticity"""
        try:
            for i, screenshot in enumerate(screenshots):
                screenshot_url = screenshot.get("url")
                if not screenshot_url:
                    validation_result["warnings"].append(f"Screenshot {i+1} missing URL")
                    continue
                
                # Check if screenshot is accessible
                try:
                    response = requests.get(screenshot_url, timeout=10)
                    if response.status_code != 200:
                        validation_result["warnings"].append(f"Screenshot {i+1} not accessible")
                        continue
                    
                    # Check image metadata
                    image = Image.open(BytesIO(response.content))
                    metadata = image.info
                    
                    # Check if image has been modified
                    if "exif" in metadata:
                        exif_data = metadata["exif"]
                        # Add EXIF validation logic here
                    
                    # Check image dimensions
                    width, height = image.size
                    if width < 100 or height < 100:
                        validation_result["warnings"].append(f"Screenshot {i+1} has suspicious dimensions")
                    
                    # Check image file size
                    if len(response.content) < 1000:  # Less than 1KB
                        validation_result["warnings"].append(f"Screenshot {i+1} is unusually small")
                    
                except Exception as e:
                    validation_result["warnings"].append(f"Error validating screenshot {i+1}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error validating screenshots: {str(e)}")
            validation_result["warnings"].append("Error validating screenshots")
    
    def _validate_replay_data(self, replay_data: Dict[str, Any], validation_result: Dict[str, Any]):
        """Validate replay data integrity"""
        try:
            # Check if replay has required fields
            required_fields = ["duration", "events", "player_actions"]
            for field in required_fields:
                if field not in replay_data:
                    validation_result["warnings"].append(f"Replay data missing field: {field}")
            
            # Check replay duration
            duration = replay_data.get("duration", 0)
            if duration < 60:  # Less than 1 minute
                validation_result["suspicious_indicators"].append("Replay duration is unusually short")
                validation_result["confidence_score"] -= 0.2
            
            if duration > 3600:  # More than 1 hour
                validation_result["warnings"].append("Replay duration is unusually long")
            
            # Check events consistency
            events = replay_data.get("events", [])
            if len(events) < 10:
                validation_result["suspicious_indicators"].append("Replay has too few events")
                validation_result["confidence_score"] -= 0.3
            
            # Check for impossible actions
            kill_events = [e for e in events if e.get("type") == "kill"]
            if len(kill_events) > 50:
                validation_result["suspicious_indicators"].append("Replay has suspiciously high kill count")
                validation_result["confidence_score"] -= 0.4
            
            # Check for rapid actions
            if len(events) > 0:
                timestamps = [e.get("timestamp", 0) for e in events if "timestamp" in e]
                if len(timestamps) > 1:
                    time_diffs = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
                    rapid_actions = [diff for diff in time_diffs if diff < 0.1]  # Less than 100ms
                    if len(rapid_actions) > 10:
                        validation_result["suspicious_indicators"].append("Replay has suspiciously rapid actions")
                        validation_result["confidence_score"] -= 0.3
        
        except Exception as e:
            logger.error(f"Error validating replay data: {str(e)}")
            validation_result["warnings"].append("Error validating replay data")
    
    def _check_suspicious_patterns(self, match_data: Dict[str, Any], validation_result: Dict[str, Any]):
        """Check for suspicious patterns in match data"""
        try:
            # Check for impossible combinations
            placement = match_data.get("placement", 0)
            kills = match_data.get("kills", 0)
            survival_time = match_data.get("survival_time", 0)
            
            # High placement with high kills (suspicious)
            if placement > 50 and kills > 20:
                validation_result["suspicious_indicators"].append("High placement with high kill count")
                validation_result["confidence_score"] -= 0.2
            
            # Low placement with high survival time (suspicious)
            if placement < 10 and survival_time > 1200:
                validation_result["suspicious_indicators"].append("Low placement with high survival time")
                validation_result["confidence_score"] -= 0.1
            
            # Check for perfect scores
            accuracy = match_data.get("accuracy", 0)
            if accuracy == 100:
                validation_result["suspicious_indicators"].append("Perfect accuracy score")
                validation_result["confidence_score"] -= 0.4
            
            # Check for round numbers (suspicious)
            if kills % 10 == 0 and kills > 10:
                validation_result["warnings"].append("Kill count is a round number")
            
            # Check for impossible damage-to-kill ratio
            damage = match_data.get("damage", 0)
            if kills > 0 and damage > 0:
                damage_per_kill = damage / kills
                if damage_per_kill > 500:  # More than 500 damage per kill
                    validation_result["suspicious_indicators"].append("Unrealistic damage-to-kill ratio")
                    validation_result["confidence_score"] -= 0.2
        
        except Exception as e:
            logger.error(f"Error checking suspicious patterns: {str(e)}")
            validation_result["warnings"].append("Error checking suspicious patterns")
    
    def _calculate_confidence_score(self, validation_result: Dict[str, Any]) -> float:
        """Calculate final confidence score"""
        base_score = 1.0
        
        # Deduct for errors
        base_score -= len(validation_result["errors"]) * 0.3
        
        # Deduct for suspicious indicators
        base_score -= len(validation_result["suspicious_indicators"]) * 0.1
        
        # Deduct for warnings
        base_score -= len(validation_result["warnings"]) * 0.05
        
        return max(0.0, min(1.0, base_score))
    
    def generate_validation_report(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        validation_result = self.validate_match_result(match_data)
        
        report = {
            "match_id": match_data.get("match_id"),
            "validation_timestamp": datetime.utcnow().isoformat(),
            "validation_result": validation_result,
            "recommendations": self._generate_recommendations(validation_result),
            "risk_assessment": self._assess_risk(validation_result)
        }
        
        return report
    
    def _generate_recommendations(self, validation_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        if validation_result["confidence_score"] < 0.7:
            recommendations.append("Manual review recommended due to low confidence score")
        
        if validation_result["suspicious_indicators"]:
            recommendations.append("Additional verification required for suspicious indicators")
        
        if validation_result["errors"]:
            recommendations.append("Match data needs correction before processing")
        
        if not recommendations:
            recommendations.append("Match data appears valid and can be processed")
        
        return recommendations
    
    def _assess_risk(self, validation_result: Dict[str, Any]) -> str:
        """Assess risk level based on validation results"""
        confidence_score = validation_result["confidence_score"]
        
        if confidence_score >= 0.9:
            return "LOW"
        elif confidence_score >= 0.7:
            return "MEDIUM"
        elif confidence_score >= 0.5:
            return "HIGH"
        else:
            return "CRITICAL"
