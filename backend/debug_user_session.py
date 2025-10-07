#!/usr/bin/env python3
"""
Debug User Session Script
Check what user data is returned by login
"""

import requests
import json

def debug_user_session():
    """Debug user session data"""
    
    login_url = "http://localhost:8001/api/v1/auth/login-direct"
    login_data = {
        "email": "testadmin@clasharena.com",
        "password": "sammyokay"
    }
    
    try:
        print("🔍 Debugging user session...")
        
        # Login
        print("1. Logging in...")
        login_response = requests.post(login_url, json=login_data)
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            return
        
        login_data = login_response.json()
        user = login_data["user"]
        
        print("\n📋 User Data from Login Response:")
        print(f"   ID: {user.get('id')}")
        print(f"   Email: {user.get('email')}")
        print(f"   Username: {user.get('username')}")
        print(f"   Full Name: {user.get('full_name')}")
        print(f"   Is Active: {user.get('is_active')}")
        print(f"   Is Admin: {user.get('is_admin')}")
        print(f"   Is Admin Type: {type(user.get('is_admin'))}")
        
        # Test token with a simple API call
        print("\n2. Testing token with API call...")
        token = login_data["access_token"]
        
        # Try to get user info using the token
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Test with a simple endpoint first
        test_response = requests.get("http://localhost:8001/api/v1/wallet/balance", headers=headers)
        print(f"   Wallet API Status: {test_response.status_code}")
        
        if test_response.status_code == 200:
            print("   ✅ Token is working for regular endpoints")
        else:
            print("   ❌ Token not working for regular endpoints")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 User Session Debug")
    print("=" * 25)
    
    debug_user_session()
