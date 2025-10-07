#!/usr/bin/env python3
"""
Test Authentication Flow Script
Test the login endpoint to verify it's working
"""

import requests
import json

def test_login():
    """Test login endpoint"""
    url = "http://localhost:8001/api/v1/auth/login-direct"
    
    # Test with the admin user
    login_data = {
        "email": "testadmin@clasharena.com",
        "password": "sammyokay"
    }
    
    try:
        print("🔍 Testing login endpoint...")
        print(f"URL: {url}")
        print(f"Data: {login_data}")
        
        response = requests.post(url, json=login_data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ Login successful!")
            print(f"Access Token: {data.get('access_token', 'N/A')[:20]}...")
            print(f"User: {data.get('user', {})}")
            print(f"Is Admin: {data.get('user', {}).get('is_admin', 'N/A')}")
        else:
            print(f"\n❌ Login failed: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is the backend server running?")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_register():
    """Test register endpoint"""
    url = "http://localhost:8001/api/v1/auth/register"
    
    register_data = {
        "email": "testuser@example.com",
        "password": "testpassword123",
        "username": "testuser",
        "full_name": "Test User"
    }
    
    try:
        print("\n🔍 Testing register endpoint...")
        print(f"URL: {url}")
        print(f"Data: {register_data}")
        
        response = requests.post(url, json=register_data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ Registration successful!")
            print(f"User: {data.get('user', {})}")
            print(f"Is Admin: {data.get('user', {}).get('is_admin', 'N/A')}")
        else:
            print(f"\n❌ Registration failed: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is the backend server running?")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 ClashArena Authentication Test")
    print("=" * 40)
    
    test_login()
    test_register()
