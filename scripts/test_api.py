#!/usr/bin/env python3
"""
Test script for ClashArena API endpoints
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8001"

def test_endpoint(method, endpoint, data=None, headers=None):
    """Test an API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=headers)
        
        print(f"{method} {endpoint} - Status: {response.status_code}")
        
        if response.status_code < 400:
            try:
                result = response.json()
                print(f"Response: {json.dumps(result, indent=2)}")
            except:
                print(f"Response: {response.text}")
        else:
            print(f"Error: {response.text}")
        
        return response
        
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def main():
    """Main test function"""
    print("ClashArena API Test Suite")
    print("========================")
    
    # Test health check
    print("\n1. Testing Health Check...")
    test_endpoint("GET", "/health")
    
    # Test root endpoint
    print("\n2. Testing Root Endpoint...")
    test_endpoint("GET", "/")
    
    # Test user registration
    print("\n3. Testing User Registration...")
    user_data = {
        "email": "test@clasharena.com",
        "username": "testuser",
        "full_name": "Test User",
        "password": "testpassword123"
    }
    register_response = test_endpoint("POST", "/auth/register", user_data)
    
    if register_response and register_response.status_code == 200:
        auth_data = register_response.json()
        token = auth_data.get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test user info
        print("\n4. Testing Get Current User...")
        test_endpoint("GET", "/auth/me", headers=headers)
        
        # Test wallet balance
        print("\n5. Testing Wallet Balance...")
        test_endpoint("GET", "/wallet/balance", headers=headers)
        
        # Test deposit
        print("\n6. Testing Wallet Deposit...")
        deposit_data = {
            "amount": 1000.0,
            "payment_method": "test"
        }
        test_endpoint("POST", "/wallet/deposit", deposit_data, headers=headers)
        
        # Test wallet balance again
        print("\n7. Testing Wallet Balance After Deposit...")
        test_endpoint("GET", "/wallet/balance", headers=headers)
        
        # Test get games
        print("\n8. Testing Get Supported Games...")
        test_endpoint("GET", "/games")
        
        # Test create match
        print("\n9. Testing Create Match...")
        match_data = {
            "game_type": "clash_royale",
            "match_type": "casual",
            "bet_amount": 100.0
        }
        test_endpoint("POST", "/matches", match_data, headers=headers)
        
        # Test get matches
        print("\n10. Testing Get Matches...")
        test_endpoint("GET", "/matches", headers=headers)
        
        # Test create referral
        print("\n11. Testing Create Referral...")
        test_endpoint("POST", "/referrals", headers=headers)
        
        # Test get referrals
        print("\n12. Testing Get Referrals...")
        test_endpoint("GET", "/referrals", headers=headers)
    
    print("\n" + "="*50)
    print("API Test Suite Completed!")
    print("Check the responses above for any errors.")

if __name__ == "__main__":
    main()
