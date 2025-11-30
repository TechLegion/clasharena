from fastapi import FastAPI, HTTPException, Depends, status, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator
import os
import logging
import hashlib
import secrets
import json

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Add parent directory to path to import database module
backend_dir = Path(__file__).parent
root_dir = backend_dir.parent.resolve()  # Use resolve() to get absolute path
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Import database modules
try:
    from database.db import get_db, init_db
    from database.models import Entry, Payment, Payout, AdminUser, Notification
except ImportError as e:
    print(f"Error importing database modules: {e}")
    print(f"Python path: {sys.path}")
    print(f"Root directory: {root_dir}")
    print(f"Database path exists: {(root_dir / 'database').exists()}")
    raise

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Google Sheets integration (optional)
try:
    from google_sheets import save_entry_to_sheets, update_entry_in_sheets
except ImportError:
    logger.warning("Google Sheets integration not available. Install google-api-python-client and google-auth to enable.")
    def save_entry_to_sheets(entry_data): return False
    def update_entry_in_sheets(payment_reference, updates): return False

# Import exchange rate module
try:
    from exchange_rate import get_live_dollar_rate
except ImportError:
    logger.warning("Exchange rate module not available. Using default rate.")
    def get_live_dollar_rate(): return float(os.getenv("DOLLAR_RATE", "1500"))

app = FastAPI(title="ClashArena MVP", version="1.0.0")

# Add exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors and return user-friendly messages"""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error.get("loc", []))
        msg = error.get("msg", "Validation error")
        errors.append(f"{field}: {msg}")
    
    logger.error(f"Validation error: {errors}")
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Validation error",
            "errors": errors,
            "detail": str(exc)
        }
    )

# Initialize database (will create tables if they don't exist)
try:
    init_db()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Database initialization error: {e}")
    logger.error("Make sure PostgreSQL is running and the database exists.")
    logger.error("Run: python setup_database.py to create the database")
    # Don't raise - allow app to start but database operations will fail

# Mount static files and templates (paths relative to backend directory)
frontend_static = root_dir / "frontend" / "static"
frontend_templates = root_dir / "frontend" / "templates"

if frontend_static.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_static)), name="static")
else:
    logger.warning(f"Static directory not found: {frontend_static}")

if frontend_templates.exists():
    templates = Jinja2Templates(directory=str(frontend_templates))
else:
    logger.error(f"Templates directory not found: {frontend_templates}")
    raise FileNotFoundError(f"Templates directory not found: {frontend_templates}")

# Configuration
# Payment Gateway - using same Paystack keys as main app
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY", "sk_live_2ab66b1fe6bf3073420cf0d8513cd965de1dd021")
PAYSTACK_PUBLIC_KEY = os.getenv("PAYSTACK_PUBLIC_KEY", "pk_live_bcace690c5b14739346161a501307ad4f9688e30")
FLUTTERWAVE_SECRET_KEY = os.getenv("FLUTTERWAVE_SECRET_KEY", "")
PAYMENT_GATEWAY = os.getenv("PAYMENT_GATEWAY", "paystack")  # paystack or flutterwave
ENTRY_FEE_USD = float(os.getenv("ENTRY_FEE_USD", "1.0"))  # $1 USD entry fee
WHATSAPP_GROUP_LINK = os.getenv("WHATSAPP_GROUP_LINK", "https://chat.whatsapp.com/your-group-link")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

def get_entry_fee_ngn() -> float:
    """Calculate entry fee in NGN based on $1 USD and current exchange rate"""
    try:
        dollar_rate = get_live_dollar_rate()
        entry_fee_ngn = ENTRY_FEE_USD * dollar_rate
        logger.info(f"Entry fee calculated: ${ENTRY_FEE_USD} USD = ₦{entry_fee_ngn:.2f} NGN (rate: {dollar_rate})")
        return round(entry_fee_ngn, 2)
    except Exception as e:
        logger.error(f"Error calculating entry fee: {e}")
        # Fallback to default rate if exchange rate fails
        default_rate = float(os.getenv("DOLLAR_RATE", "1500"))
        return round(ENTRY_FEE_USD * default_rate, 2)

# Pydantic Models
class PaymentVerificationRequest(BaseModel):
    reference: str

class PlayerIntakeRequest(BaseModel):
    payment_reference: str
    codm_id: str = Field(..., min_length=1, description="Call of Duty Mobile ID")
    contact_phone: str = Field(..., min_length=1, description="Phone number")
    contact_email: EmailStr
    region: str = Field(..., min_length=1, description="Player region")
    bank_name: str = Field(..., min_length=1, description="Bank name")
    account_number: str = Field(..., min_length=1, description="Account number")
    account_name: str = Field(..., min_length=1, description="Account holder name")
    
    @validator('contact_phone', pre=True)
    def clean_phone(cls, v):
        """Clean phone number before validation"""
        if isinstance(v, str):
            v = v.strip()
        return v
    
    @validator('account_number', pre=True)
    def clean_account(cls, v):
        """Clean account number before validation"""
        if isinstance(v, str):
            v = v.strip()
        return v
    
    class Config:
        # Allow extra fields and be more lenient with validation
        extra = "forbid"

class MarkWinnerRequest(BaseModel):
    entry_id: str
    is_winner: bool

class TriggerPayoutRequest(BaseModel):
    entry_id: str

# Helper Functions
def hash_password(password: str) -> str:
    """Simple password hashing (use bcrypt in production)"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash

def verify_paystack_payment(reference: str) -> dict:
    """Verify payment with Paystack"""
    import requests
    try:
        headers = {
            "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        response = requests.get(
            f"https://api.paystack.co/transaction/verify/{reference}",
            headers=headers,
            timeout=10
        )
        logger.info(f"Paystack verification response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Paystack verification data: {json.dumps(data, indent=2)}")
            
            if data.get("status") and data.get("data"):
                transaction_data = data["data"]
                transaction_status = transaction_data.get("status")
                
                # Check if payment was successful
                if transaction_status == "success":
                    return {
                        "verified": True,
                        "amount": transaction_data.get("amount", 0) / 100,  # Convert from kobo to NGN
                        "gateway_reference": transaction_data.get("reference", reference),
                        "gateway_response": json.dumps(data)
                    }
                else:
                    logger.warning(f"Payment status is {transaction_status}, not success")
                    return {
                        "verified": False,
                        "status": transaction_status,
                        "gateway_response": json.dumps(data)
                    }
            else:
                logger.error(f"Invalid Paystack response structure: {data}")
                return {"verified": False, "gateway_response": json.dumps(data)}
        else:
            logger.error(f"Paystack API error: {response.status_code} - {response.text}")
            return {"verified": False, "error": f"API returned {response.status_code}", "gateway_response": response.text}
    except Exception as e:
        logger.error(f"Paystack verification error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"verified": False, "error": str(e)}

def verify_flutterwave_payment(reference: str) -> dict:
    """Verify payment with Flutterwave"""
    import requests
    try:
        headers = {
            "Authorization": f"Bearer {FLUTTERWAVE_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        response = requests.get(
            f"https://api.flutterwave.com/v3/transactions/{reference}/verify",
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success" and data.get("data", {}).get("status") == "successful":
                return {
                    "verified": True,
                    "amount": data["data"]["amount"],
                    "gateway_response": json.dumps(data)
                }
        return {"verified": False, "gateway_response": json.dumps(response.json())}
    except Exception as e:
        logger.error(f"Flutterwave verification error: {e}")
        return {"verified": False, "error": str(e)}

def send_notification(entry_id: str, notification_type: str, recipient: str, subject: str, message: str, db: Session):
    """Create notification record"""
    notification = Notification(
        entry_id=entry_id,
        notification_type=notification_type,
        recipient=recipient,
        subject=subject,
        message=message,
        status="pending"
    )
    db.add(notification)
    db.commit()
    # TODO: Integrate with actual email/WhatsApp/SMS services
    logger.info(f"Notification created: {notification_type} to {recipient}")

# Routes
@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Landing page with entry button"""
    entry_fee_ngn = get_entry_fee_ngn()
    return templates.TemplateResponse("landing.html", {
        "request": request,
        "entry_fee": int(entry_fee_ngn)  # Display as integer (no decimals)
    })

def initiate_paystack_payment(amount: float, email: str, reference: str) -> dict:
    """Initiate Paystack payment"""
    import requests
    try:
        headers = {
            "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "email": email,
            "amount": int(amount * 100),  # Convert to kobo
            "reference": reference,
            "callback_url": f"{os.getenv('BASE_URL', 'http://localhost:8000')}/intake/{reference}",
            "metadata": {
                "custom_fields": [
                    {
                        "display_name": "Tournament Entry",
                        "variable_name": "tournament_entry",
                        "value": "ClashArena"
                    }
                ]
            }
        }
        response = requests.post(
            "https://api.paystack.co/transaction/initialize",
            headers=headers,
            json=data
        )
        if response.status_code == 200:
            result = response.json()
            if result.get("status"):
                return {
                    "success": True,
                    "authorization_url": result["data"]["authorization_url"],
                    "access_code": result["data"]["access_code"]
                }
        return {"success": False, "error": response.text}
    except Exception as e:
        logger.error(f"Paystack initiation error: {e}")
        return {"success": False, "error": str(e)}

def initiate_flutterwave_payment(amount: float, email: str, reference: str) -> dict:
    """Initiate Flutterwave payment"""
    import requests
    try:
        headers = {
            "Authorization": f"Bearer {FLUTTERWAVE_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "tx_ref": reference,
            "amount": amount,
            "currency": "NGN",
            "redirect_url": f"{os.getenv('BASE_URL', 'http://localhost:8000')}/intake/{reference}",
            "customer": {
                "email": email
            },
            "customizations": {
                "title": "ClashArena Tournament Entry",
                "description": "Tournament Entry Fee"
            }
        }
        response = requests.post(
            "https://api.flutterwave.com/v3/payments",
            headers=headers,
            json=data
        )
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                return {
                    "success": True,
                    "link": result["data"]["link"]
                }
        return {"success": False, "error": response.text}
    except Exception as e:
        logger.error(f"Flutterwave initiation error: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/initiate-payment")
async def initiate_payment(
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    """Initiate payment and return checkout URL"""
    try:
        # Check if email already has a completed payment
        existing_entry = db.query(Entry).filter(
            Entry.contact_email == email,
            Entry.payment_status == "completed"
        ).first()
        
        if existing_entry:
            # If intake already submitted, redirect to thank you
            if existing_entry.codm_id:
                return {
                    "success": True,
                    "already_registered": True,
                    "message": "You have already registered for this tournament",
                    "redirect_url": f"/thank-you/{existing_entry.payment_reference}"
                }
            # If payment completed but intake not submitted, redirect to intake
            else:
                return {
                    "success": True,
                    "payment_completed": True,
                    "message": "Payment already completed. Please complete your registration",
                    "redirect_url": f"/intake/{existing_entry.payment_reference}"
                }
        
        # Calculate entry fee in NGN based on current exchange rate
        entry_fee_ngn = get_entry_fee_ngn()
        
        # Generate unique payment reference
        payment_ref = f"CLASH_{secrets.token_hex(8).upper()}"
        
        # Create entry record
        entry = Entry(
            payment_reference=payment_ref,
            payment_status="pending",
            entry_fee=entry_fee_ngn,
            contact_email=email
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)  # Refresh to get the ID
        
        # Create payment record
        payment = Payment(
            entry_id=entry.id,
            reference=payment_ref,
            gateway=PAYMENT_GATEWAY,
            amount=entry_fee_ngn,
            currency="NGN",
            status="pending"
        )
        db.add(payment)
        db.commit()
        
        # Initialize payment with gateway
        if PAYMENT_GATEWAY == "paystack":
            if not PAYSTACK_SECRET_KEY:
                raise HTTPException(status_code=500, detail="Paystack secret key not configured")
            payment_result = initiate_paystack_payment(entry_fee_ngn, email, payment_ref)
            if payment_result.get("success"):
                checkout_url = payment_result["authorization_url"]
            else:
                raise HTTPException(status_code=500, detail=f"Payment initiation failed: {payment_result.get('error')}")
        else:  # flutterwave
            if not FLUTTERWAVE_SECRET_KEY:
                raise HTTPException(status_code=500, detail="Flutterwave secret key not configured")
            payment_result = initiate_flutterwave_payment(entry_fee_ngn, email, payment_ref)
            if payment_result.get("success"):
                checkout_url = payment_result["link"]
            else:
                raise HTTPException(status_code=500, detail=f"Payment initiation failed: {payment_result.get('error')}")
        
        return {
            "success": True,
            "payment_reference": payment_ref,
            "checkout_url": checkout_url,
            "entry_id": entry.id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Payment initiation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/intake/{payment_reference}", response_class=HTMLResponse)
async def intake_page(request: Request, payment_reference: str, db: Session = Depends(get_db)):
    """Player intake form page (locked to payment reference)"""
    # Verify payment first
    entry = db.query(Entry).filter(Entry.payment_reference == payment_reference).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Payment reference not found")
    
    if entry.payment_status != "completed":
        # Verify payment
        logger.info(f"Verifying payment for reference: {payment_reference}")
        if PAYMENT_GATEWAY == "paystack":
            verification = verify_paystack_payment(payment_reference)
        else:
            verification = verify_flutterwave_payment(payment_reference)
        
        logger.info(f"Verification result: {verification}")
        
        if verification.get("verified"):
            entry.payment_status = "completed"
            payment = db.query(Payment).filter(Payment.reference == payment_reference).first()
            if payment:
                payment.status = "success"
                payment.gateway_response = verification.get("gateway_response", "")
            db.commit()
            db.refresh(entry)  # Refresh to get updated status
            logger.info(f"Payment verified and updated for reference: {payment_reference}")
        else:
            logger.warning(f"Payment verification failed for reference: {payment_reference}, reason: {verification.get('error', 'Unknown')}")
            return templates.TemplateResponse("payment_pending.html", {
                "request": request,
                "payment_reference": payment_reference,
                "error": verification.get("error", "Payment verification failed")
            })
    
    # Check if already submitted
    if entry.codm_id:
        return RedirectResponse(url=f"/thank-you/{payment_reference}", status_code=302)
    
    return templates.TemplateResponse("intake.html", {
        "request": request,
        "payment_reference": payment_reference
    })

@app.post("/api/submit-intake")
async def submit_intake(data: PlayerIntakeRequest, db: Session = Depends(get_db)):
    """Submit player intake form"""
    try:
        # Log received data for debugging
        logger.info(f"Received intake data: {data.dict()}")
        
        # Clean phone and account number (remove spaces, dashes, etc.)
        phone_cleaned = data.contact_phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace("+", "")
        account_cleaned = data.account_number.replace(" ", "").replace("-", "")
        
        # Validate cleaned values
        if len(phone_cleaned) < 10:
            raise HTTPException(status_code=422, detail=f"Phone number must be at least 10 digits (got {len(phone_cleaned)} after cleaning)")
        if len(account_cleaned) != 10:
            raise HTTPException(status_code=422, detail=f"Account number must be exactly 10 digits (got {len(account_cleaned)} after cleaning)")
        entry = db.query(Entry).filter(Entry.payment_reference == data.payment_reference).first()
        if not entry:
            raise HTTPException(status_code=404, detail="Payment reference not found")
        
        # Re-verify payment if status is not completed (safety check)
        if entry.payment_status != "completed":
            logger.info(f"Re-verifying payment for reference: {data.payment_reference}")
            if PAYMENT_GATEWAY == "paystack":
                verification = verify_paystack_payment(data.payment_reference)
            else:
                verification = verify_flutterwave_payment(data.payment_reference)
            
            if verification.get("verified"):
                entry.payment_status = "completed"
                payment = db.query(Payment).filter(Payment.reference == data.payment_reference).first()
                if payment:
                    payment.status = "success"
                    payment.gateway_response = verification.get("gateway_response", "")
                db.commit()
                logger.info(f"Payment verified during intake submission for reference: {data.payment_reference}")
            else:
                raise HTTPException(status_code=400, detail="Payment not completed. Please complete payment first.")
        
        if entry.codm_id:
            raise HTTPException(status_code=400, detail="Intake already submitted")
        
        # Update entry with player details (use cleaned values)
        entry.codm_id = data.codm_id
        entry.contact_phone = phone_cleaned
        entry.contact_email = data.contact_email
        entry.region = data.region
        entry.bank_name = data.bank_name
        entry.account_number = account_cleaned
        entry.account_name = data.account_name
        db.commit()
        db.refresh(entry)  # Refresh to get updated data
        
        # Save to Google Sheets
        try:
            # Get live exchange rate (cached for 1 hour)
            dollar_rate = get_live_dollar_rate()
            per_kill_value = float(os.getenv("PER_KILL_VALUE", "0.6"))
            
            logger.info(f"Using exchange rate: 1 USD = {dollar_rate} NGN")
            
            entry_data = {
                "payment_reference": entry.payment_reference,
                "contact_email": entry.contact_email,
                "codm_id": entry.codm_id,
                "contact_phone": entry.contact_phone,
                "region": entry.region,
                "bank_name": entry.bank_name,
                "account_number": entry.account_number,
                "account_name": entry.account_name,
                "entry_fee": float(entry.entry_fee) if entry.entry_fee else 0,
                "payment_status": entry.payment_status,
                "is_winner": entry.is_winner,
                "payout_status": entry.payout_status,
                "created_at": entry.created_at,
                "dollar_rate": dollar_rate,
                "per_kill_value": per_kill_value
            }
            save_entry_to_sheets(entry_data)
        except Exception as e:
            logger.warning(f"Failed to save to Google Sheets: {e}")
        
        # Send confirmation notifications
        send_notification(
            entry.id,
            "email",
            data.contact_email,
            "Welcome to ClashArena!",
            f"Thank you for registering! Your CODM ID: {data.codm_id}. Match details will be sent soon.",
            db
        )
        
        send_notification(
            entry.id,
            "whatsapp",
            data.contact_phone,
            "ClashArena Registration",
            f"Welcome! Join our WhatsApp group: {WHATSAPP_GROUP_LINK}",
            db
        )
        
        return {
            "success": True,
            "message": "Intake submitted successfully",
            "redirect_url": f"/thank-you/{data.payment_reference}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Intake submission error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/thank-you/{payment_reference}", response_class=HTMLResponse)
async def thank_you_page(request: Request, payment_reference: str, db: Session = Depends(get_db)):
    """Thank you page with WhatsApp link"""
    entry = db.query(Entry).filter(Entry.payment_reference == payment_reference).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    return templates.TemplateResponse("thank_you.html", {
        "request": request,
        "whatsapp_link": WHATSAPP_GROUP_LINK,
        "codm_id": entry.codm_id
    })

# Admin Routes
@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Admin login page"""
    return templates.TemplateResponse("admin_login.html", {"request": request})

@app.post("/admin/login")
async def admin_login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    """Admin login"""
    try:
        admin = db.query(AdminUser).filter(AdminUser.username == username).first()
        if not admin or not verify_password(password, admin.password_hash):
            # Return login page with error message
            return templates.TemplateResponse("admin_login.html", {
                "request": request,
                "error": "Invalid username or password"
            }, status_code=401)
        
        if not admin.is_active:
            return templates.TemplateResponse("admin_login.html", {
                "request": request,
                "error": "Account is disabled"
            }, status_code=403)
        
        # Create session token (simple implementation)
        # In production, use proper session management with JWT or cookies
        session_token = secrets.token_urlsafe(32)
        # Store in response headers or cookies (simplified for MVP)
        
        return RedirectResponse(url="/admin/dashboard", status_code=302)
    except Exception as e:
        logger.error(f"Admin login error: {e}")
        return templates.TemplateResponse("admin_login.html", {
            "request": request,
            "error": "An error occurred. Please try again."
        }, status_code=500)

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    """Admin dashboard"""
    entries = db.query(Entry).filter(Entry.payment_status == "completed").order_by(Entry.created_at.desc()).all()
    
    stats = {
        "total_entries": len(entries),
        "winners": len([e for e in entries if e.is_winner]),
        "pending_payouts": len([e for e in entries if e.is_winner and e.payout_status == "pending"]),
        "completed_payouts": len([e for e in entries if e.payout_status == "completed"])
    }
    
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "entries": entries,
        "stats": stats
    })

@app.post("/api/admin/mark-winner")
async def mark_winner(data: MarkWinnerRequest, db: Session = Depends(get_db)):
    """Mark entry as winner"""
    entry = db.query(Entry).filter(Entry.id == data.entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    entry.is_winner = data.is_winner
    if data.is_winner:
        entry.payout_status = "pending"
    db.commit()
    
    return {"success": True, "message": "Winner status updated"}

@app.post("/api/admin/trigger-payout")
async def trigger_payout(data: TriggerPayoutRequest, db: Session = Depends(get_db)):
    """Trigger payout for winner"""
    entry = db.query(Entry).filter(Entry.id == data.entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    if not entry.is_winner:
        raise HTTPException(status_code=400, detail="Entry is not marked as winner")
    
    if entry.payout_status == "completed":
        raise HTTPException(status_code=400, detail="Payout already completed")
    
    # Create payout record
    payout = Payout(
        entry_id=entry.id,
        amount=entry.entry_fee * 10,  # Example: 10x payout (adjust as needed)
        currency="NGN",
        status="processing",
        gateway="bank_transfer"
    )
    db.add(payout)
    
    entry.payout_status = "processing"
    db.commit()
    
    # TODO: Integrate with actual payout gateway
    # For now, mark as completed after processing
    payout.status = "completed"
    entry.payout_status = "completed"
    db.commit()
    
    # Notify player
    send_notification(
        entry.id,
        "email",
        entry.contact_email,
        "Payout Processed",
        f"Your payout of {payout.amount} NGN has been processed successfully!",
        db
    )
    
    send_notification(
        entry.id,
        "sms",
        entry.contact_phone,
        "Payout Processed",
        f"Your payout of {payout.amount} NGN has been processed.",
        db
    )
    
    return {"success": True, "message": "Payout triggered successfully"}

@app.get("/api/admin/entries")
async def get_entries(
    status_filter: Optional[str] = None,
    winner_only: bool = False,
    db: Session = Depends(get_db)
):
    """Get all entries (API endpoint)"""
    query = db.query(Entry).filter(Entry.payment_status == "completed")
    
    if winner_only:
        query = query.filter(Entry.is_winner == True)
    
    if status_filter:
        query = query.filter(Entry.payout_status == status_filter)
    
    entries = query.order_by(Entry.created_at.desc()).all()
    
    return {
        "entries": [
            {
                "id": e.id,
                "payment_reference": e.payment_reference,
                "codm_id": e.codm_id,
                "contact_phone": e.contact_phone,
                "contact_email": e.contact_email,
                "region": e.region,
                "bank_name": e.bank_name,
                "account_number": e.account_number,
                "account_name": e.account_name,
                "is_winner": e.is_winner,
                "payout_status": e.payout_status,
                "created_at": e.created_at.isoformat()
            }
            for e in entries
        ]
    }

@app.get("/api/exchange-rate")
async def get_exchange_rate_info():
    """Get current exchange rate information"""
    try:
        from exchange_rate import get_cached_rate_info, get_live_dollar_rate
        
        # Get cached rate info
        cache_info = get_cached_rate_info()
        
        # Get current live rate (this will use cache if available)
        current_rate = get_live_dollar_rate()
        
        return {
            "success": True,
            "current_rate": current_rate,
            "cache_info": cache_info
        }
    except Exception as e:
        logger.error(f"Error getting exchange rate: {e}")
        return {
            "success": False,
            "error": str(e),
            "current_rate": float(os.getenv("DOLLAR_RATE", "1500"))
        }

@app.post("/api/exchange-rate/refresh")
async def refresh_exchange_rate():
    """Force refresh the exchange rate (clears cache)"""
    try:
        from exchange_rate import clear_rate_cache, get_live_dollar_rate
        
        # Clear cache
        clear_rate_cache()
        
        # Fetch new rate
        new_rate = get_live_dollar_rate()
        
        return {
            "success": True,
            "message": "Exchange rate refreshed",
            "new_rate": new_rate
        }
    except Exception as e:
        logger.error(f"Error refreshing exchange rate: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/webhook/paystack")
async def paystack_webhook(request: Request, db: Session = Depends(get_db)):
    """Paystack webhook to update payment status"""
    try:
        body = await request.json()
        event = body.get("event")
        data = body.get("data", {})
        
        logger.info(f"Paystack webhook received: {event}")
        
        if event == "charge.success":
            reference = data.get("reference")
            if not reference:
                logger.error("No reference in webhook data")
                return {"status": "error", "message": "No reference provided"}
            
            # Find entry by payment reference
            entry = db.query(Entry).filter(Entry.payment_reference == reference).first()
            if entry:
                if entry.payment_status != "completed":
                    entry.payment_status = "completed"
                    
                    # Update payment record
                    payment = db.query(Payment).filter(Payment.reference == reference).first()
                    if payment:
                        payment.status = "success"
                        payment.gateway_response = json.dumps(data)
                    
                    db.commit()
                    db.refresh(entry)  # Refresh to get updated data
                    logger.info(f"Payment status updated to completed for reference: {reference}")
                    
                    # Update Google Sheets
                    try:
                        # Pass codm_id or email to find the row in the sheet
                        updates = {"payment_status": "completed"}
                        if entry.codm_id:
                            updates["codm_id"] = entry.codm_id
                        elif entry.contact_email:
                            updates["contact_email"] = entry.contact_email
                        update_entry_in_sheets(reference, updates)
                    except Exception as e:
                        logger.warning(f"Failed to update Google Sheets: {e}")
                else:
                    logger.info(f"Payment already marked as completed for reference: {reference}")
            else:
                logger.warning(f"Entry not found for reference: {reference}")
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e)}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "clasharena-mvp"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

