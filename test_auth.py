import requests
import json

BASE_URL = "http://localhost:8001/api/v1"

def test_registration():
    """Test user registration"""
    url = f"{BASE_URL}/auth/register"
    data = {
        "email": "test@clasharena.com",
        "username": "testuser",
        "full_name": "Test User",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Registration Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Registration Error: {e}")
        return None

def test_login():
    """Test user login"""
    url = f"{BASE_URL}/auth/login"
    data = {
        "email_or_username": "testuser",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Login Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Login Error: {e}")
        return None

def test_me(token):
    """Test get current user"""
    url = f"{BASE_URL}/auth/me"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Me Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Me Error: {e}")
        return None

if __name__ == "__main__":
    print("Testing ClashArena API Authentication...")
    print("=" * 50)
    
    # Test registration
    print("\n1. Testing Registration:")
    reg_result = test_registration()
    
    # Test login
    print("\n2. Testing Login:")
    login_result = test_login()
    
    if login_result and 'access_token' in login_result:
        token = login_result['access_token']
        
        # Test get current user
        print("\n3. Testing Get Current User:")
        me_result = test_me(token)
        
        print("\n" + "=" * 50)
        print("✅ All tests completed!")
    else:
        print("\n❌ Login failed, skipping user info test")
