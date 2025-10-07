#!/usr/bin/env python3
"""
Test Admin API Script
Test the admin dashboard stats endpoint
"""

import requests
import json

def test_admin_dashboard():
    """Test admin dashboard stats endpoint"""
    
    # First login to get a token
    login_url = "http://localhost:8001/api/v1/auth/login-direct"
    login_data = {
        "email": "testadmin@clasharena.com",
        "password": "sammyokay"
    }
    
    try:
        print("🔍 Testing admin dashboard endpoint...")
        
        # Login first
        print("1. Logging in...")
        login_response = requests.post(login_url, json=login_data)
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return
        
        login_data = login_response.json()
        token = login_data["access_token"]
        user = login_data["user"]
        
        print(f"✅ Login successful!")
        print(f"   User: {user['username']}")
        print(f"   Is Admin: {user['is_admin']}")
        print(f"   Token: {token[:20]}...")
        
        # Test admin dashboard
        print("\n2. Testing admin dashboard stats...")
        dashboard_url = "http://localhost:8001/api/v1/admin/dashboard/stats"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        dashboard_response = requests.get(dashboard_url, headers=headers)
        
        print(f"Status Code: {dashboard_response.status_code}")
        print(f"Response: {dashboard_response.text}")
        
        if dashboard_response.status_code == 200:
            data = dashboard_response.json()
            print("\n✅ Dashboard stats retrieved successfully!")
            print(f"   Total Users: {data.get('users', {}).get('total', 'N/A')}")
            print(f"   Total Matches: {data.get('matches', {}).get('total', 'N/A')}")
            print(f"   Net Revenue: ₦{data.get('revenue', {}).get('net_revenue', 'N/A')}")
        else:
            print(f"\n❌ Dashboard stats failed: {dashboard_response.status_code}")
            if dashboard_response.status_code == 403:
                print("   This means the user is not recognized as admin!")
            elif dashboard_response.status_code == 401:
                print("   This means the token is invalid!")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is the backend server running?")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 ClashArena Admin API Test")
    print("=" * 35)
    
    test_admin_dashboard()
