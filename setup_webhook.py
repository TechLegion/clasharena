#!/usr/bin/env python3
"""
Script to automatically configure Paystack webhook
"""
import requests
import json

# Your Paystack credentials
PAYSTACK_SECRET_KEY = "sk_live_2ab66b1fe6bf3073420cf0d8513cd965de1dd021"
WEBHOOK_URL = "https://clash-arena-production.up.railway.app/api/v1/payments/webhook/paystack"

def setup_paystack_webhook():
    """Set up Paystack webhook automatically"""
    
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    webhook_data = {
        "url": WEBHOOK_URL,
        "events": [
            "charge.success",
            "transfer.success", 
            "transfer.failed"
        ]
    }
    
    try:
        print("Setting up Paystack webhook...")
        print(f"Webhook URL: {WEBHOOK_URL}")
        
        response = requests.post(
            "https://api.paystack.co/webhook",
            headers=headers,
            json=webhook_data
        )
        
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200 and result.get('status'):
            print("✅ Webhook configured successfully!")
            print(f"Webhook ID: {result.get('data', {}).get('id')}")
        else:
            print("❌ Failed to configure webhook")
            if 'message' in result:
                print(f"Error: {result['message']}")
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_webhook_connectivity():
    """Test if the webhook URL is accessible"""
    
    try:
        print("\nTesting webhook connectivity...")
        
        response = requests.post(
            WEBHOOK_URL,
            json={"test": "connectivity"},
            timeout=10
        )
        
        print(f"Connectivity test status: {response.status_code}")
        
        if response.status_code in [200, 401, 422]:  # 401/422 are expected for test requests
            print("✅ Webhook URL is accessible")
        else:
            print("⚠️ Webhook URL may not be accessible")
            
    except Exception as e:
        print(f"❌ Webhook connectivity test failed: {str(e)}")

def list_existing_webhooks():
    """List existing webhooks"""
    
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        print("\nChecking existing webhooks...")
        
        response = requests.get(
            "https://api.paystack.co/webhook",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            webhooks = result.get('data', [])
            
            if webhooks:
                print(f"Found {len(webhooks)} existing webhook(s):")
                for webhook in webhooks:
                    print(f"- URL: {webhook.get('url')}")
                    print(f"  Status: {webhook.get('status')}")
                    print(f"  Events: {webhook.get('events', [])}")
                    print()
            else:
                print("No existing webhooks found")
        else:
            print(f"Failed to fetch webhooks: {response.status_code}")
            
    except Exception as e:
        print(f"Error fetching webhooks: {str(e)}")

if __name__ == "__main__":
    print("=== Paystack Webhook Setup ===")
    print(f"Webhook URL: {WEBHOOK_URL}")
    print()
    
    # Test connectivity first
    test_webhook_connectivity()
    
    # List existing webhooks
    list_existing_webhooks()
    
    # Set up new webhook
    setup_paystack_webhook()
    
    print("\n=== Setup Complete ===")
    print("After running this script:")
    print("1. Go to your Paystack dashboard to verify the webhook")
    print("2. Make a test payment to verify automatic crediting")
    print("3. Check Railway logs for webhook activity")
