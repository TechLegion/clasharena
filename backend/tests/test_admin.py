"""
Admin tests for ClashArena
"""

import pytest
from fastapi.testclient import TestClient

class TestAdmin:
    """Test admin endpoints"""
    
    def test_get_all_users_admin(self, client, admin_headers):
        """Test getting all users as admin"""
        response = client.get("/admin/users", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_all_users_non_admin(self, client, auth_headers):
        """Test getting all users as non-admin"""
        response = client.get("/admin/users", headers=auth_headers)
        
        assert response.status_code == 403
    
    def test_get_all_users_unauthorized(self, client):
        """Test getting all users without authentication"""
        response = client.get("/admin/users")
        
        assert response.status_code == 401
    
    def test_get_user_by_id_admin(self, client, admin_headers, test_user):
        """Test getting user by ID as admin"""
        response = client.get(f"/admin/users/{test_user.id}", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
    
    def test_get_user_by_id_non_admin(self, client, auth_headers, test_user):
        """Test getting user by ID as non-admin"""
        response = client.get(f"/admin/users/{test_user.id}", headers=auth_headers)
        
        assert response.status_code == 403
    
    def test_update_user_admin(self, client, admin_headers, test_user):
        """Test updating user as admin"""
        update_data = {
            "full_name": "Updated Name",
            "is_active": True
        }
        
        response = client.put(f"/admin/users/{test_user.id}", json=update_data, headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
    
    def test_update_user_non_admin(self, client, auth_headers, test_user):
        """Test updating user as non-admin"""
        update_data = {
            "full_name": "Updated Name"
        }
        
        response = client.put(f"/admin/users/{test_user.id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 403
    
    def test_delete_user_admin(self, client, admin_headers, test_user):
        """Test deleting user as admin"""
        response = client.delete(f"/admin/users/{test_user.id}", headers=admin_headers)
        
        assert response.status_code == 200
        assert response.json()["message"] == "User deleted successfully"
    
    def test_delete_user_non_admin(self, client, auth_headers, test_user):
        """Test deleting user as non-admin"""
        response = client.delete(f"/admin/users/{test_user.id}", headers=auth_headers)
        
        assert response.status_code == 403
    
    def test_get_system_stats_admin(self, client, admin_headers):
        """Test getting system statistics as admin"""
        response = client.get("/admin/stats", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "total_matches" in data
        assert "total_transactions" in data
    
    def test_get_system_stats_non_admin(self, client, auth_headers):
        """Test getting system statistics as non-admin"""
        response = client.get("/admin/stats", headers=auth_headers)
        
        assert response.status_code == 403
    
    def test_get_all_transactions_admin(self, client, admin_headers):
        """Test getting all transactions as admin"""
        response = client.get("/admin/transactions", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_all_transactions_non_admin(self, client, auth_headers):
        """Test getting all transactions as non-admin"""
        response = client.get("/admin/transactions", headers=auth_headers)
        
        assert response.status_code == 403
    
    def test_get_all_matches_admin(self, client, admin_headers):
        """Test getting all matches as admin"""
        response = client.get("/admin/matches", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_all_matches_non_admin(self, client, auth_headers):
        """Test getting all matches as non-admin"""
        response = client.get("/admin/matches", headers=auth_headers)
        
        assert response.status_code == 403
