#!/usr/bin/env python3
"""
Webhook Tunnel Setup Script
This script helps set up ngrok to expose your local backend for Paystack webhooks.
"""

import subprocess
import sys
import time
import requests
import json

def check_ngrok_installed():
    """Check if ngrok is installed"""
    try:
        result = subprocess.run(['ngrok', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ ngrok is installed")
            return True
        else:
            print("❌ ngrok not found")
            return False
    except FileNotFoundError:
        print("❌ ngrok not found")
        return False

def install_ngrok_instructions():
    """Show instructions to install ngrok"""
    print("\n📋 To install ngrok:")
    print("1. Go to: https://ngrok.com/download")
    print("2. Download for your OS")
    print("3. Extract and add to PATH")
    print("4. Sign up for free account at https://ngrok.com")
    print("5. Get your auth token from dashboard")
    print("6. Run: ngrok config add-authtoken YOUR_TOKEN")

def start_ngrok_tunnel(port=8001):
    """Start ngrok tunnel"""
    try:
        print(f"🚀 Starting ngrok tunnel for port {port}...")
        
        # Start ngrok in background
        process = subprocess.Popen(
            ['ngrok', 'http', str(port), '--log=stdout'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment for ngrok to start
        time.sleep(3)
        
        # Get the public URL
        try:
            response = requests.get('http://localhost:4040/api/tunnels')
            if response.status_code == 200:
                tunnels = response.json()
                if tunnels['tunnels']:
                    public_url = tunnels['tunnels'][0]['public_url']
                    webhook_url = f"{public_url}/api/v1/payments/webhook/paystack"
                    
                    print(f"✅ ngrok tunnel started!")
                    print(f"🌐 Public URL: {public_url}")
                    print(f"🔗 Webhook URL: {webhook_url}")
                    print("\n📋 Next steps:")
                    print(f"1. Update Paystack webhook URL to: {webhook_url}")
                    print("2. Keep this script running")
                    print("3. Test a payment - it should auto-credit now!")
                    
                    return webhook_url, process
                else:
                    print("❌ No tunnels found")
                    return None, process
            else:
                print("❌ Could not get tunnel info")
                return None, process
        except Exception as e:
            print(f"❌ Error getting tunnel info: {e}")
            return None, process
            
    except Exception as e:
        print(f"❌ Error starting ngrok: {e}")
        return None, None

def main():
    print("🔧 ClashArena Webhook Tunnel Setup")
    print("=" * 40)
    
    if not check_ngrok_installed():
        install_ngrok_instructions()
        return
    
    # Start tunnel
    webhook_url, ngrok_process = start_ngrok_tunnel()
    
    if webhook_url:
        print(f"\n⏳ Keeping tunnel alive... Press Ctrl+C to stop")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping ngrok tunnel...")
            if ngrok_process:
                ngrok_process.terminate()
            print("✅ Tunnel stopped")
    else:
        print("❌ Failed to start tunnel")

if __name__ == "__main__":
    main()
