"""
Wallet tests for ClashArena
"""

import pytest
from fastapi.testclient import TestClient

class TestWallet:
    """Test wallet endpoints"""
    
    def test_get_wallet_balance(self, client, auth_headers):
        """Test getting wallet balance"""
        response = client.get("/wallet/balance", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
        assert "currency" in data
    
    def test_get_wallet_balance_unauthorized(self, client):
        """Test getting wallet balance without authentication"""
        response = client.get("/wallet/balance")
        
        assert response.status_code == 401
    
    def test_deposit_funds(self, client, auth_headers):
        """Test depositing funds"""
        deposit_data = {
            "amount": 1000.0,
            "payment_method": "test"
        }
        
        response = client.post("/wallet/deposit", json=deposit_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "transaction_id" in data
        assert "amount" in data
    
    def test_deposit_invalid_amount(self, client, auth_headers):
        """Test deposit with invalid amount"""
        deposit_data = {
            "amount": -100.0,
            "payment_method": "test"
        }
        
        response = client.post("/wallet/deposit", json=deposit_data, headers=auth_headers)
        
        assert response.status_code == 400
    
    def test_withdraw_funds(self, client, auth_headers):
        """Test withdrawing funds"""
        withdraw_data = {
            "amount": 500.0,
            "payment_method": "test"
        }
        
        response = client.post("/wallet/withdraw", json=withdraw_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "transaction_id" in data
        assert "amount" in data
    
    def test_withdraw_insufficient_funds(self, client, auth_headers):
        """Test withdrawal with insufficient funds"""
        withdraw_data = {
            "amount": 10000.0,
            "payment_method": "test"
        }
        
        response = client.post("/wallet/withdraw", json=withdraw_data, headers=auth_headers)
        
        assert response.status_code == 400
        assert "insufficient funds" in response.json()["detail"].lower()
    
    def test_get_transaction_history(self, client, auth_headers):
        """Test getting transaction history"""
        response = client.get("/wallet/transactions", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_transaction_history_with_pagination(self, client, auth_headers):
        """Test getting transaction history with pagination"""
        response = client.get("/wallet/transactions?page=1&size=10", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
