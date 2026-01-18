import os
from typing import Optional

class Settings:
    """Application configuration settings"""
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "ClashArena"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Gaming platform for ClashArena players"
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Database - PostgreSQL configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:sammyokay@localhost:5432/clasharena")
    SQLALCHEMY_ECHO: bool = os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true"
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")
    
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
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "https://clasharena.online")
    
    # CORS
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8000",
        "https://clasharenafrontend.vercel.app",  # Main Vercel frontend URL
        "https://clasharenafrontend-32sn8g2y5-techlegions-projects.vercel.app",  # Backup URL
        "https://clasharena-frontend.vercel.app",  # For future deployments
        "https://clasharena.online",  # Custom domain
        "https://www.clasharena.online",  # WWW subdomain
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

# Debug: Print which Paystack keys are loaded (without exposing full keys)
if settings.PAYSTACK_SECRET_KEY:
    secret_preview = settings.PAYSTACK_SECRET_KEY[:7] + "..." + settings.PAYSTACK_SECRET_KEY[-4:]
    key_type = "TEST" if "test" in settings.PAYSTACK_SECRET_KEY.lower() else ("LIVE" if "live" in settings.PAYSTACK_SECRET_KEY.lower() else "UNKNOWN")
    print(f"🔑 Paystack Secret Key loaded: {secret_preview} ({key_type})")
else:
    print("⚠️ WARNING: PAYSTACK_SECRET_KEY is not set!")