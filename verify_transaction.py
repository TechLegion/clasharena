#!/usr/bin/env python3
"""
Script to manually verify a Paystack transaction
"""
import requests
import json
import sys

# Your Railway backend URL
BACKEND_URL = "https://clash-arena-production.up.railway.app"

def verify_transaction(reference, user_token):
    """Verify a transaction manually"""
    
    # You'll need to get this from your login response
    headers = {
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "reference": reference
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/payments/deposit/verify",
            headers=headers,
            json=data
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                print("✅ Transaction verified successfully!")
                print(f"Amount credited: ₦{result.get('amount', 0):,.2f}")
                print(f"New balance: ₦{result.get('balance', 0):,.2f}")
            else:
                print("❌ Transaction verification failed")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python verify_transaction.py <transaction_reference> <user_token>")
        print("Example: python verify_transaction.py dep_abc123 your_jwt_token")
        sys.exit(1)
    
    reference = sys.argv[1]
    user_token = sys.argv[2]
    
    print(f"Verifying transaction: {reference}")
    verify_transaction(reference, user_token)
