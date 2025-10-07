from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import os
from typing import Optional

app = FastAPI(title="ClashArena API Gateway", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
SERVICE_URLS = {
    "auth": os.getenv("AUTH_SERVICE_URL", "http://localhost:8001"),
    "wallet": os.getenv("WALLET_SERVICE_URL", "http://localhost:8002"),
    "match": os.getenv("MATCH_SERVICE_URL", "http://localhost:8003"),
    "referral": os.getenv("REFERRAL_SERVICE_URL", "http://localhost:8004"),
    "admin": os.getenv("ADMIN_SERVICE_URL", "http://localhost:8005"),
}

@app.get("/")
async def root():
    return {"message": "ClashArena API Gateway", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    services_status = {}
    
    async with httpx.AsyncClient() as client:
        for service_name, url in SERVICE_URLS.items():
            try:
                response = await client.get(f"{url}/health", timeout=5.0)
                services_status[service_name] = "healthy" if response.status_code == 200 else "unhealthy"
            except Exception as e:
                services_status[service_name] = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy",
        "services": services_status
    }

# Auth Service Routes
@app.post("/auth/register")
async def register_user(user_data: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{SERVICE_URLS['auth']}/register", json=user_data)
        return response.json()

@app.post("/auth/login")
async def login_user(credentials: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{SERVICE_URLS['auth']}/login", json=credentials)
        return response.json()

@app.post("/auth/refresh")
async def refresh_token(token_data: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{SERVICE_URLS['auth']}/refresh", json=token_data)
        return response.json()

# Wallet Service Routes
@app.get("/wallet/balance")
async def get_wallet_balance(user_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SERVICE_URLS['wallet']}/balance", params={"user_id": user_id})
        return response.json()

@app.post("/wallet/deposit")
async def deposit_funds(deposit_data: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{SERVICE_URLS['wallet']}/deposit", json=deposit_data)
        return response.json()

@app.post("/wallet/withdraw")
async def withdraw_funds(withdraw_data: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{SERVICE_URLS['wallet']}/withdraw", json=withdraw_data)
        return response.json()

# Match Service Routes
@app.get("/matches")
async def get_matches(user_id: Optional[str] = None, status: Optional[str] = None):
    params = {}
    if user_id:
        params["user_id"] = user_id
    if status:
        params["status"] = status
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SERVICE_URLS['match']}/matches", params=params)
        return response.json()

@app.post("/matches")
async def create_match(match_data: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{SERVICE_URLS['match']}/matches", json=match_data)
        return response.json()

@app.put("/matches/{match_id}")
async def update_match(match_id: str, match_data: dict):
    async with httpx.AsyncClient() as client:
        response = await client.put(f"{SERVICE_URLS['match']}/matches/{match_id}", json=match_data)
        return response.json()

# Referral Service Routes
@app.get("/referrals")
async def get_referrals(user_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SERVICE_URLS['referral']}/referrals", params={"user_id": user_id})
        return response.json()

@app.post("/referrals")
async def create_referral(referral_data: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{SERVICE_URLS['referral']}/referrals", json=referral_data)
        return response.json()

# Admin Service Routes
@app.get("/admin/users")
async def get_all_users(page: int = 1, limit: int = 20):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SERVICE_URLS['admin']}/users", params={"page": page, "limit": limit})
        return response.json()

@app.get("/admin/matches")
async def get_all_matches(page: int = 1, limit: int = 20):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SERVICE_URLS['admin']}/matches", params={"page": page, "limit": limit})
        return response.json()

@app.get("/admin/transactions")
async def get_all_transactions(page: int = 1, limit: int = 20):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SERVICE_URLS['admin']}/transactions", params={"page": page, "limit": limit})
        return response.json()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
