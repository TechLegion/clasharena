#!/usr/bin/env python3
"""
Deposit Verification Script
Run this script to manually verify a Paystack deposit and credit your wallet.
"""

import httpx
import asyncio
import sys

# Configuration
PAYSTACK_SECRET_KEY = "sk_live_2ab66b1fe6bf3073420cf0d8513cd965de1dd021"
API_BASE_URL = "http://localhost:8001"
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTk3NTg5MDUsInN1YiI6IjNlYzZhMmE0LWQ5MzctNDQ1NC1hODlhLWI0ZTcxNjRmOTgyMiJ9.cLGmIC7UdvV13NRaEX5hydrYRqjVgV4ek3KFUEQYicw"

async def verify_payment_with_paystack(reference):
    """Verify payment with Paystack API"""
    print(f"🔍 Verifying payment with Paystack...")
    print(f"Reference: {reference}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"https://api.paystack.co/transaction/verify/{reference}",
                headers={
                    "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                data = result["data"]
                
                print(f"✅ Paystack Response:")
                print(f"   Status: {data['status']}")
                print(f"   Amount: ₦{data['amount'] / 100:,.2f}")
                print(f"   Email: {data['customer']['email']}")
                print(f"   Reference: {data['reference']}")
                print(f"   Date: {data['created_at']}")
                
                if data['status'] == 'success':
                    print(f"✅ Payment successful on Paystack!")
                    return True, data
                else:
                    print(f"❌ Payment not successful on Paystack")
                    return False, data
            else:
                print(f"❌ Paystack API error: {response.status_code}")
                print(f"Response: {response.text}")
                return False, None
                
        except Exception as e:
            print(f"❌ Error calling Paystack: {e}")
            return False, None

async def credit_wallet_via_api(reference):
    """Credit wallet via our API"""
    print(f"💰 Crediting wallet via API...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/api/v1/payments/deposit/verify",
                headers={
                    "Authorization": f"Bearer {JWT_TOKEN}",
                    "Content-Type": "application/json"
                },
                json={"reference": reference}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Wallet credited successfully!")
                print(f"   Amount: ₦{result.get('amount', 0):,.2f}")
                print(f"   New Balance: ₦{result.get('balance', 0):,.2f}")
                print(f"   Message: {result.get('message', '')}")
                return True, result
            else:
                print(f"❌ API error: {response.status_code}")
                print(f"Response: {response.text}")
                return False, None
                
        except Exception as e:
            print(f"❌ Error calling API: {e}")
            return False, None

async def main():
    print("🚀 ClashArena Deposit Verification Script")
    print("=" * 50)
    
    # Get reference from user input or command line
    if len(sys.argv) > 1:
        reference = sys.argv[1]
    else:
        reference = input("Enter your transaction reference: ").strip()
    
    if not reference:
        print("❌ No reference provided!")
        return
    
    print(f"📋 Processing reference: {reference}")
    print()
    
    # Step 1: Verify with Paystack
    paystack_success, paystack_data = await verify_payment_with_paystack(reference)
    
    if not paystack_success:
        print("❌ Cannot proceed - payment not successful on Paystack")
        return
    
    print()
    
    # Step 2: Credit wallet via our API
    api_success, api_result = await credit_wallet_via_api(reference)
    
    if api_success:
        print()
        print("🎉 DEPOSIT VERIFICATION COMPLETE!")
        print(f"💰 Your wallet has been credited with ₦{api_result.get('amount', 0):,.2f}")
        print(f"💳 New balance: ₦{api_result.get('balance', 0):,.2f}")
    else:
        print()
        print("❌ DEPOSIT VERIFICATION FAILED!")
        print("Please check the error messages above and try again.")

if __name__ == "__main__":
    # JWT token is already set
    print("✅ JWT token configured")
    
    # Run the verification
    asyncio.run(main())
