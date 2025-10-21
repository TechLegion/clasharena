"""
Authentication tests for ClashArena
"""

import pytest
from fastapi.testclient import TestClient

class TestAuth:
    """Test authentication endpoints"""
    
    def test_register_user(self, client):
        """Test user registration"""
        user_data = {
            "email": "newuser@clasharena.com",
            "username": "newuser",
            "full_name": "New User",
            "password": "newpassword123"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email"""
        user_data = {
            "email": test_user.email,
            "username": "differentuser",
            "full_name": "Different User",
            "password": "password123"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "email already registered" in response.json()["detail"].lower()
    
    def test_login_user(self, client, test_user):
        """Test user login"""
        login_data = {
            "username": test_user.email,
            "password": "testpassword123"
        }
        
        response = client.post("/auth/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        login_data = {
            "username": "nonexistent@clasharena.com",
            "password": "wrongpassword"
        }
        
        response = client.post("/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "incorrect email or password" in response.json()["detail"].lower()
    
    def test_get_current_user(self, client, auth_headers):
        """Test getting current user information"""
        response = client.get("/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "username" in data
        assert "full_name" in data
    
    def test_get_current_user_unauthorized(self, client):
        """Test getting current user without authentication"""
        response = client.get("/auth/me")
        
        assert response.status_code == 401
    
    def test_refresh_token(self, client, test_user):
        """Test token refresh"""
        # First login to get initial token
        login_data = {
            "username": test_user.email,
            "password": "testpassword123"
        }
        
        login_response = client.post("/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        
        # Test token refresh
        response = client.post("/auth/refresh", headers={"Authorization": f"Bearer {token}"})
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_logout(self, client, auth_headers):
        """Test user logout"""
        response = client.post("/auth/logout", headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"
