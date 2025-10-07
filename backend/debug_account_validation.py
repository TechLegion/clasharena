#!/usr/bin/env python3
"""
Debug Account Validation Script
Test bank account validation with Paystack API
"""

import httpx
import asyncio

# Configuration
PAYSTACK_SECRET_KEY = "sk_live_2ab66b1fe6bf3073420cf0d8513cd965de1dd021"

async def test_account_validation(account_number, bank_code):
    """Test account validation with Paystack"""
    print(f"🔍 Testing account validation...")
    print(f"Account Number: {account_number}")
    print(f"Bank Code: {bank_code}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Test account resolution
            response = await client.get(
                "https://api.paystack.co/bank/resolve",
                headers={
                    "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
                    "Content-Type": "application/json"
                },
                params={
                    "account_number": account_number,
                    "bank_code": bank_code
                }
            )
            
            print(f"📡 API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success Response:")
                print(f"   Status: {result.get('status')}")
                print(f"   Account Name: {result.get('data', {}).get('account_name', 'N/A')}")
                print(f"   Account Number: {result.get('data', {}).get('account_number', 'N/A')}")
                print(f"   Bank Code: {result.get('data', {}).get('bank_code', 'N/A')}")
                return True, result
            else:
                print(f"❌ Error Response: {response.status_code}")
                print(f"Response: {response.text}")
                return False, response.text
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            return False, str(e)

async def get_banks():
    """Get list of banks from Paystack"""
    print(f"🏦 Getting list of banks...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                "https://api.paystack.co/bank",
                headers={
                    "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                banks = result.get('data', [])
                print(f"✅ Found {len(banks)} banks:")
                
                # Show first 10 banks as examples
                for i, bank in enumerate(banks[:10]):
                    print(f"   {i+1}. {bank.get('name')} - Code: {bank.get('code')}")
                
                if len(banks) > 10:
                    print(f"   ... and {len(banks) - 10} more banks")
                
                return banks
            else:
                print(f"❌ Failed to get banks: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error getting banks: {e}")
            return []

async def main():
    print("🔧 ClashArena Account Validation Debug")
    print("=" * 50)
    
    # First, get list of banks
    banks = await get_banks()
    
    print("\n" + "=" * 50)
    print("📋 To test account validation:")
    print("1. Pick a bank code from the list above")
    print("2. Enter your account details")
    print("3. The script will test the validation")
    
    # Get user input
    account_number = input("\nEnter account number: ").strip()
    bank_code = input("Enter bank code: ").strip()
    
    if account_number and bank_code:
        print(f"\n🧪 Testing validation...")
        success, result = await test_account_validation(account_number, bank_code)
        
        if success:
            print(f"\n✅ Account validation successful!")
        else:
            print(f"\n❌ Account validation failed!")
            print(f"Error: {result}")
    else:
        print("❌ Please provide both account number and bank code")

if __name__ == "__main__":
    asyncio.run(main())
