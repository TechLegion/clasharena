import os
from typing import Optional

class Settings:
    """Application configuration settings"""
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "ClashArena"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Gaming platform for ClashArena players"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Database - PostgreSQL configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:sammyokay@localhost:5432/clasharena")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Payment Gateways - Paystack 2025
    PAYSTACK_SECRET_KEY: str = os.getenv("PAYSTACK_SECRET_KEY", "")
    PAYSTACK_PUBLIC_KEY: str = os.getenv("PAYSTACK_PUBLIC_KEY", "")
    # Note: PAYSTACK_WEBHOOK_SECRET not needed in 2025 - uses PAYSTACK_SECRET_KEY for signature verification
    FLUTTERWAVE_SECRET_KEY: str = os.getenv("FLUTTERWAVE_SECRET_KEY", "")
    
    # Email Configuration
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
    MAILGUN_API_KEY: str = os.getenv("MAILGUN_API_KEY", "")
    MAILGUN_DOMAIN: str = os.getenv("MAILGUN_DOMAIN", "")
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "noreply@clasharena.com")
    FROM_NAME: str = os.getenv("FROM_NAME", "ClashArena Team")
    
    # Frontend URL
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # CORS
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8000",
    ]
    
    # Social Auth
    GOOGLE_CLIENT_ID: Optional[str] = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: Optional[str] = os.getenv("GOOGLE_CLIENT_SECRET")
    FACEBOOK_APP_ID: Optional[str] = os.getenv("FACEBOOK_APP_ID")
    FACEBOOK_APP_SECRET: Optional[str] = os.getenv("FACEBOOK_APP_SECRET")
    
    # SMS Configuration - Twilio
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")

settings = Settings()