from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
# Explicitly load from backend/.env first, fallback to root .env
backend_dir = Path(__file__).parent.parent  # backend/app -> backend
backend_env = backend_dir / ".env"
root_env = backend_dir.parent / ".env"  # backend -> root

# Try backend/.env first, then root/.env
if backend_env.exists():
    load_dotenv(backend_env)
    print(f"✅ Loaded .env from: {backend_env}")
elif root_env.exists():
    load_dotenv(root_env)
    print(f"✅ Loaded .env from: {root_env}")
else:
    # Fallback to default behavior
    load_dotenv()
    print("⚠️ Using default load_dotenv() behavior")

from app.core.config import settings
from app.core.database import init_db
from app.core.rate_limiting import limiter, rate_limit_exceeded_handler
from app.api.v1 import auth, wallet, matches, referrals, admin, tasks, payments, otp

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
init_db()

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["authentication"])
app.include_router(wallet.router, prefix=f"{settings.API_V1_STR}/wallet", tags=["wallet"])
app.include_router(payments.router, prefix=f"{settings.API_V1_STR}/payments", tags=["payments"])
app.include_router(otp.router, prefix=f"{settings.API_V1_STR}/otp", tags=["otp"])
app.include_router(matches.router, prefix=f"{settings.API_V1_STR}", tags=["matches"])
app.include_router(referrals.router, prefix=f"{settings.API_V1_STR}", tags=["referrals"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["admin"])
app.include_router(tasks.router, prefix=f"{settings.API_V1_STR}/tasks", tags=["tasks"])

@app.get("/")
async def root():
    return {
        "message": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_STR}/docs"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME.lower(),
        "version": settings.VERSION
    }
