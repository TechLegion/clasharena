"""
Match tests for ClashArena
"""

import pytest
from fastapi.testclient import TestClient

class TestMatches:
    """Test match endpoints"""
    
    def test_get_supported_games(self, client):
        """Test getting supported games"""
        response = client.get("/games")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_match(self, client, auth_headers):
        """Test creating a match"""
        match_data = {
            "game_type": "clash_royale",
            "match_type": "casual",
            "bet_amount": 100.0
        }
        
        response = client.post("/matches", json=match_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "match_id" in data
        assert "status" in data
    
    def test_create_match_invalid_game_type(self, client, auth_headers):
        """Test creating a match with invalid game type"""
        match_data = {
            "game_type": "invalid_game",
            "match_type": "casual",
            "bet_amount": 100.0
        }
        
        response = client.post("/matches", json=match_data, headers=auth_headers)
        
        assert response.status_code == 400
    
    def test_create_match_insufficient_funds(self, client, auth_headers):
        """Test creating a match with insufficient funds"""
        match_data = {
            "game_type": "clash_royale",
            "match_type": "casual",
            "bet_amount": 10000.0
        }
        
        response = client.post("/matches", json=match_data, headers=auth_headers)
        
        assert response.status_code == 400
        assert "insufficient funds" in response.json()["detail"].lower()
    
    def test_get_user_matches(self, client, auth_headers):
        """Test getting user matches"""
        response = client.get("/matches", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_user_matches_with_pagination(self, client, auth_headers):
        """Test getting user matches with pagination"""
        response = client.get("/matches?page=1&size=10", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_match_details(self, client, auth_headers):
        """Test getting match details"""
        # First create a match
        match_data = {
            "game_type": "clash_royale",
            "match_type": "casual",
            "bet_amount": 100.0
        }
        
        create_response = client.post("/matches", json=match_data, headers=auth_headers)
        match_id = create_response.json()["match_id"]
        
        # Then get match details
        response = client.get(f"/matches/{match_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "match_id" in data
        assert "status" in data
    
    def test_get_match_details_unauthorized(self, client):
        """Test getting match details without authentication"""
        response = client.get("/matches/123")
        
        assert response.status_code == 401
    
    def test_join_match(self, client, auth_headers):
        """Test joining a match"""
        # First create a match
        match_data = {
            "game_type": "clash_royale",
            "match_type": "casual",
            "bet_amount": 100.0
        }
        
        create_response = client.post("/matches", json=match_data, headers=auth_headers)
        match_id = create_response.json()["match_id"]
        
        # Then join the match
        response = client.post(f"/matches/{match_id}/join", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_join_match_not_found(self, client, auth_headers):
        """Test joining a non-existent match"""
        response = client.post("/matches/999999/join", headers=auth_headers)
        
        assert response.status_code == 404
