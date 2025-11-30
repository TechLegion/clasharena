#!/usr/bin/env python3
"""
Script to verify the specific transaction for sammyokorie0@gmail.com
"""
import requests
import json

# Transaction details from your receipt
TRANSACTION_REFERENCE = "dep_989127c9-dcce-4042-8552-460d2d15be6a"
BACKEND_URL = "https://clash-arena-production.up.railway.app"

def login_and_verify():
    """Login and verify the transaction"""
    
    # First, let's login to get a token
    login_data = {
        "email": "sammyokorie0@gmail.com",
        "password": "your_password_here"  # You'll need to replace this
    }
    
    print("Step 1: Logging in...")
    try:
        login_response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login-direct",
            json=login_data
        )
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            token = login_result.get("access_token")
            
            if not token:
                print("❌ No access token received from login")
                return
            
            print("✅ Login successful!")
            
            # Now verify the transaction
            print("Step 2: Verifying transaction...")
            verify_transaction(token)
            
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            
    except Exception as e:
        print(f"❌ Login error: {str(e)}")

def verify_transaction(token):
    """Verify the transaction with the token"""
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "reference": TRANSACTION_REFERENCE
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/payments/deposit/verify",
            headers=headers,
            json=data
        )
        
        print(f"Verification Status Code: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200:
            if result.get("status") == "success":
                print("✅ Transaction verified successfully!")
                print(f"Amount credited: ₦{result.get('amount', 0):,.2f}")
                print(f"New balance: ₦{result.get('balance', 0):,.2f}")
            elif result.get("status") == "already_credited":
                print("ℹ️ Transaction was already processed")
            else:
                print("❌ Transaction verification failed")
        else:
            print(f"❌ Verification error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Verification error: {str(e)}")

if __name__ == "__main__":
    print("=== ClashArena Transaction Verification ===")
    print(f"Transaction Reference: {TRANSACTION_REFERENCE}")
    print(f"Amount: ₦100.00")
    print()
    
    # You need to update the password in the login_data above
    print("⚠️  IMPORTANT: Update the password in this script before running!")
    print("Edit line 13: 'password': 'your_actual_password'")
    print()
    
    # Uncomment the line below after updating the password
    # login_and_verify()
    
    print("After updating the password, uncomment the last line and run again.")
