#!/usr/bin/env python3
"""
Test script to verify environment variables are loaded correctly
"""

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

print("🔍 Environment Variables Test")
print("=" * 50)

# Test critical variables
variables_to_test = [
    "SECRET_KEY",
    "DATABASE_URL", 
    "REDIS_URL",
    "PAYSTACK_SECRET_KEY",
    "PAYSTACK_PUBLIC_KEY",
    "TWILIO_ACCOUNT_SID",
    "TWILIO_AUTH_TOKEN",
    "TWILIO_PHONE_NUMBER",
    "SENDGRID_API_KEY"
]

for var in variables_to_test:
    value = os.getenv(var)
    if value:
        # Hide sensitive values but show they exist
        if "SECRET" in var or "KEY" in var or "TOKEN" in var:
            display_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
        else:
            display_value = value
        print(f"✅ {var}: {display_value}")
    else:
        print(f"❌ {var}: NOT SET")

print("\n" + "=" * 50)
print("🎯 Configuration Test Complete")

# Test the settings import
try:
    from app.core.config import settings
    print(f"✅ Settings loaded successfully")
    print(f"📊 Database URL configured: {'Yes' if settings.DATABASE_URL else 'No'}")
    print(f"📊 Redis URL configured: {'Yes' if settings.REDIS_URL else 'No'}")
    print(f"📊 Paystack configured: {'Yes' if settings.PAYSTACK_SECRET_KEY else 'No'}")
    print(f"📊 Twilio configured: {'Yes' if settings.TWILIO_ACCOUNT_SID else 'No'}")
except Exception as e:
    print(f"❌ Failed to load settings: {e}")
