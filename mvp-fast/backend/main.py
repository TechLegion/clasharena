from fastapi import FastAPI, HTTPException, Depends, status, Form, Request, Query, Cookie, Body
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import and_, text
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator
import os
import logging
import hashlib
import hmac
import base64
import secrets
import json
import time

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
    from database.models import Entry, Payment, Payout, AdminUser, Notification, AppSettings, RegistrationMilestone
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
    def save_entry_to_sheets(entry_data, target_sheet=None): return False
    def update_entry_in_sheets(payment_reference, updates, target_sheet=None): return False

# Import exchange rate module
try:
    from exchange_rate import get_live_dollar_rate
except ImportError:
    logger.warning("Exchange rate module not available. Using default rate.")
    def get_live_dollar_rate(): return float(os.getenv("DOLLAR_RATE", "100"))

# Admin authentication (cookie-based) - blocks unauthenticated access
ADMIN_SESSION_COOKIE_NAME = os.getenv("ADMIN_SESSION_COOKIE_NAME", "admin_session")
ADMIN_SESSION_SECRET = os.getenv("ADMIN_SESSION_SECRET", "")
ADMIN_SESSION_TTL_SECONDS = int(os.getenv("ADMIN_SESSION_TTL_SECONDS", "604800"))  # 7 days
if not ADMIN_SESSION_SECRET:
    logger.warning(
        "ADMIN_SESSION_SECRET is not set. Admin cookie authentication will be insecure. "
        "Set ADMIN_SESSION_SECRET in mvp-fast/.env (recommended)."
    )
    ADMIN_SESSION_SECRET = "dev-insecure-admin-session-secret-change-me"

# Helper: create/verify signed session tokens (no DB session table needed)
def _make_admin_session_token(admin_id: str, issued_at: int) -> str:
    payload = f"{admin_id}:{issued_at}"
    signature = hmac.new(
        ADMIN_SESSION_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    payload_b64 = base64.urlsafe_b64encode(payload.encode("utf-8")).decode("utf-8").rstrip("=")
    return f"{payload_b64}.{signature}"

def _verify_admin_session_token(token: str) -> Optional[str]:
    if not token or "." not in token:
        return None
    try:
        payload_b64, signature = token.split(".", 1)
        padding = "=" * (-len(payload_b64) % 4)  # restore base64 padding
        payload = base64.urlsafe_b64decode((payload_b64 + padding).encode("utf-8")).decode("utf-8")
        expected_signature = hmac.new(
            ADMIN_SESSION_SECRET.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            return None

        admin_id, issued_at_str = payload.split(":", 1)
        issued_at = int(issued_at_str)
        if time.time() - issued_at > ADMIN_SESSION_TTL_SECONDS:
            return None
        return admin_id
    except Exception:
        return None

def get_current_admin(
    admin_session: Optional[str] = Cookie(None, alias=ADMIN_SESSION_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> AdminUser:
    """Return the authenticated admin user from the signed cookie."""
    if not admin_session:
        raise HTTPException(status_code=401, detail="Admin authentication required")

    admin_id = _verify_admin_session_token(admin_session)
    if not admin_id:
        raise HTTPException(status_code=401, detail="Invalid or expired admin session")

    admin = db.query(AdminUser).filter(AdminUser.id == admin_id, AdminUser.is_active == True).first()
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid or inactive admin session")
    return admin

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
    # Run migrations for new columns (kill_count, excluded) on existing databases
    try:
        from database.db import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE entries ADD COLUMN IF NOT EXISTS kill_count INTEGER DEFAULT 0"))
            conn.execute(text("ALTER TABLE entries ADD COLUMN IF NOT EXISTS excluded BOOLEAN DEFAULT FALSE"))
            conn.execute(text("ALTER TABLE entries ADD COLUMN IF NOT EXISTS lobby_group INTEGER"))
            conn.execute(text("ALTER TABLE entries ADD COLUMN IF NOT EXISTS lobby_epoch INTEGER DEFAULT 0"))
            conn.execute(text("UPDATE entries SET lobby_epoch = 0 WHERE lobby_epoch IS NULL"))
            conn.execute(text("ALTER TABLE entries ADD COLUMN IF NOT EXISTS payment_completed_epoch INTEGER"))
            conn.execute(
                text(
                    "UPDATE entries SET payment_completed_epoch = 0 "
                    "WHERE payment_status = 'completed' AND payment_completed_epoch IS NULL"
                )
            )
            conn.commit()
        logger.info("Database migrations applied (kill_count, excluded, lobby_group, lobby_epoch, payment_completed_epoch)")
    except Exception as mig_e:
        if "already exists" in str(mig_e).lower():
            pass  # Columns exist, skip
        else:
            logger.warning(f"Migration skipped (tables may not exist yet): {mig_e}")
    # Assign lobby_group for legacy rows (chronological order, same buckets as LOBBY_GROUP_SIZE)
    try:
        from database.db import engine
        from sqlalchemy.orm import sessionmaker

        MigSession = sessionmaker(autoflush=False, autocommit=False, bind=engine)
        mdb = MigSession()
        try:
            ordered = (
                mdb.query(Entry)
                .filter(
                    Entry.payment_status == "completed",
                    Entry.codm_id.isnot(None),
                    Entry.excluded == False,
                )
                .order_by(Entry.created_at.asc())
                .all()
            )
            if ordered and any(e.lobby_group is None for e in ordered):
                gs = max(
                    1,
                    int(os.getenv("LOBBY_GROUP_SIZE", os.getenv("MAX_ENTRIES_PER_SHEET", "100"))),
                )
                for i, e in enumerate(ordered):
                    e.lobby_group = (i // gs) + 1
                mdb.commit()
                logger.info("Backfilled lobby_group for %s registrations", len(ordered))
        finally:
            mdb.close()
    except Exception as bf_e:
        logger.warning("lobby_group backfill skipped: %s", bf_e)
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
# For Railway deployment, use RAILWAY_PUBLIC_DOMAIN if BASE_URL is not set
BASE_URL = os.getenv("BASE_URL")
if not BASE_URL:
    railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
    if railway_domain:
        BASE_URL = f"https://{railway_domain}"
        logger.info(f"Using Railway domain: {BASE_URL}")
    else:
        BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@clasharena.com")
# Registration milestone for testing (set to 10 for testing phase, change to 100 for production)
REGISTRATION_MILESTONE = int(os.getenv("REGISTRATION_MILESTONE", "10"))

# Public-facing lobby grouping size (countdown resets every N registrations).
# This should match how your lobby/WhatsApp groups are rotated (default: 100).
LOBBY_GROUP_SIZE = int(os.getenv("LOBBY_GROUP_SIZE", os.getenv("MAX_ENTRIES_PER_SHEET", "100")))


def normalize_codm_for_match(codm_id: Optional[str]) -> str:
    if not codm_id:
        return ""
    return codm_id.strip().lower()


def normalize_phone_digits(phone: Optional[str]) -> str:
    if not phone:
        return ""
    return "".join(c for c in phone if c.isdigit())


REGISTRATION_LOBBY_EPOCH_KEY = "registration_lobby_epoch"
REGISTRATION_LOBBY_NAME_KEY = "registration_lobby_name"


def get_registration_lobby_epoch(db: Session) -> int:
    """Monotonic counter bumped when admin opens a new registration lobby cycle."""
    setting = db.query(AppSettings).filter(AppSettings.key == REGISTRATION_LOBBY_EPOCH_KEY).first()
    if not setting or not (setting.value or "").strip():
        return 0
    try:
        return int(setting.value.strip())
    except ValueError:
        return 0


def bump_registration_lobby_epoch(db: Session, admin_id: Optional[str] = None) -> int:
    """Increment registration lobby epoch (manual reset). Returns the new epoch value."""
    cur = get_registration_lobby_epoch(db)
    new_epoch = cur + 1
    setting = db.query(AppSettings).filter(AppSettings.key == REGISTRATION_LOBBY_EPOCH_KEY).first()
    if setting:
        setting.value = str(new_epoch)
        setting.updated_by = admin_id
        setting.updated_at = datetime.utcnow()
    else:
        db.add(
            AppSettings(
                key=REGISTRATION_LOBBY_EPOCH_KEY,
                value=str(new_epoch),
                description="Increments when admin resets the registration lobby; entries use lobby_epoch to match",
                updated_by=admin_id,
            )
        )
    db.commit()
    logger.info("Registration lobby epoch bumped %s -> %s", cur, new_epoch)
    return new_epoch


def get_registration_lobby_name(db: Session) -> str:
    """Human-readable name for the current registration lobby (landing / intake)."""
    setting = db.query(AppSettings).filter(AppSettings.key == REGISTRATION_LOBBY_NAME_KEY).first()
    if not setting or not (setting.value or "").strip():
        return ""
    return setting.value.strip()


def set_registration_lobby_name(db: Session, name: str, admin_id: Optional[str] = None) -> None:
    cleaned = (name or "").strip()
    setting = db.query(AppSettings).filter(AppSettings.key == REGISTRATION_LOBBY_NAME_KEY).first()
    if setting:
        setting.value = cleaned
        setting.updated_by = admin_id
        setting.updated_at = datetime.utcnow()
    else:
        db.add(
            AppSettings(
                key=REGISTRATION_LOBBY_NAME_KEY,
                value=cleaned,
                description="Display name for the current registration lobby (public signup)",
                updated_by=admin_id,
            )
        )
    db.commit()
    logger.info("Registration lobby name set to: %r", cleaned or "(empty)")


def get_target_lobby_for_next_registrant(db: Session) -> int:
    """Lobby batch the next completed intake joins (same indexing as /api/registration-group-status)."""
    group_size = max(1, LOBBY_GROUP_SIZE)
    epoch = get_registration_lobby_epoch(db)
    total = db.query(Entry).filter(
        Entry.payment_status == "completed",
        Entry.codm_id.isnot(None),
        Entry.excluded == False,
        Entry.lobby_epoch == epoch,
    ).count()
    return (total // group_size) + 1


def get_sheets_tab_for_current_lobby(db: Session) -> Optional[str]:
    """Return the admin lobby name to use as the Google Sheets tab, or None to fall back to env logic."""
    name = get_registration_lobby_name(db)
    return name if name else None


def mark_entry_payment_completed(entry: Entry, db: Session) -> None:
    """Record payment success and the registration lobby epoch at that moment (for stale-pending handling)."""
    entry.payment_status = "completed"
    entry.payment_completed_epoch = get_registration_lobby_epoch(db)


def _payment_epoch_for_duplicate_checks(entry: Entry) -> int:
    """Epoch to use when comparing pending rows to current lobby (coalesce for legacy rows)."""
    if entry.payment_completed_epoch is not None:
        return int(entry.payment_completed_epoch)
    return 0


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
        default_rate = float(os.getenv("DOLLAR_RATE", "100"))
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

def get_whatsapp_link(db: Session) -> str:
    """Get WhatsApp group link from database or environment"""
    setting = db.query(AppSettings).filter(AppSettings.key == "whatsapp_group_link").first()
    if setting:
        return setting.value
    return WHATSAPP_GROUP_LINK

def set_whatsapp_link(db: Session, link: str, admin_id: str = None):
    """Set WhatsApp group link in database"""
    setting = db.query(AppSettings).filter(AppSettings.key == "whatsapp_group_link").first()
    if setting:
        setting.value = link
        setting.updated_by = admin_id
        setting.updated_at = datetime.utcnow()
    else:
        setting = AppSettings(
            key="whatsapp_group_link",
            value=link,
            description="WhatsApp group link for tournament participants",
            updated_by=admin_id
        )
        db.add(setting)
    db.commit()
    logger.info(f"WhatsApp link updated to: {link}")

def get_cod_lobby_link(db: Session) -> str:
    """Get COD lobby link from database"""
    setting = db.query(AppSettings).filter(AppSettings.key == "cod_lobby_link").first()
    if setting:
        return setting.value
    return ""

def set_cod_lobby_link(db: Session, link: str, admin_id: str = None):
    """Set COD lobby link in database"""
    setting = db.query(AppSettings).filter(AppSettings.key == "cod_lobby_link").first()
    if setting:
        setting.value = link
        setting.updated_by = admin_id
        setting.updated_at = datetime.utcnow()
    else:
        setting = AppSettings(
            key="cod_lobby_link",
            value=link,
            description="COD Mobile lobby link for tournament match",
            updated_by=admin_id
        )
        db.add(setting)
    db.commit()
    logger.info(f"COD lobby link updated")

def get_tournament_status(db: Session) -> str:
    """Get tournament status: active, closed, archived"""
    setting = db.query(AppSettings).filter(AppSettings.key == "tournament_status").first()
    if setting:
        return setting.value
    return "active"

def set_tournament_status(db: Session, status: str, admin_id: str = None):
    """Set tournament status"""
    valid = ("active", "closed", "archived")
    if status not in valid:
        raise ValueError(f"Status must be one of {valid}")
    setting = db.query(AppSettings).filter(AppSettings.key == "tournament_status").first()
    if setting:
        setting.value = status
        setting.updated_by = admin_id
        setting.updated_at = datetime.utcnow()
    else:
        setting = AppSettings(
            key="tournament_status",
            value=status,
            description="Tournament status: active, closed, archived",
            updated_by=admin_id
        )
        db.add(setting)
    db.commit()
    logger.info(f"Tournament status updated to: {status}")

def check_registration_milestone(db: Session):
    """Check if registration milestone has been reached and notify admin"""
    try:
        # Count completed registrations (entries with payment completed and codm_id filled)
        total_registrations = db.query(Entry).filter(
            Entry.payment_status == "completed",
            Entry.codm_id.isnot(None)
        ).count()
        
        # Check if we've reached the milestone threshold
        if total_registrations >= REGISTRATION_MILESTONE:
            # Check if we've already notified for this milestone
            milestone = db.query(RegistrationMilestone).filter(
                RegistrationMilestone.milestone_count == REGISTRATION_MILESTONE,
                RegistrationMilestone.notified == True
            ).first()
            
            if not milestone:
                # Create milestone record
                milestone = RegistrationMilestone(
                    milestone_count=REGISTRATION_MILESTONE,
                    notified=False
                )
                db.add(milestone)
                db.commit()
                
                # Send notification to admin
                send_notification(
                    entry_id=None,
                    notification_type="email",
                    recipient=ADMIN_EMAIL,
                    subject=f"🎉 Milestone Reached: {REGISTRATION_MILESTONE} Users Registered!",
                    message=f"Congratulations! Your tournament has reached {REGISTRATION_MILESTONE} registered users. Total registrations: {total_registrations}",
                    db=db
                )
                
                # Mark as notified
                milestone.notified = True
                milestone.notification_sent_at = datetime.utcnow()
                db.commit()
                
                logger.info(f"🎉 Milestone reached: {REGISTRATION_MILESTONE} users registered! Total: {total_registrations}")
                return True
        
        return False
    except Exception as e:
        logger.error(f"Error checking registration milestone: {e}")
        return False

# Routes
@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request, db: Session = Depends(get_db)):
    """Landing page with entry button"""
    entry_fee_ngn = get_entry_fee_ngn()
    try:
        cycle = calculate_registration_group_status(db)
        remaining_in_group = cycle["remaining_in_group"]
    except Exception:
        remaining_in_group = LOBBY_GROUP_SIZE

    return templates.TemplateResponse("landing.html", {
        "request": request,
        "entry_fee": int(entry_fee_ngn),  # Display as integer (no decimals)
        "remaining_in_group": remaining_in_group,
    })

def initiate_paystack_payment(amount: float, email: str, reference: str) -> dict:
    """Initiate Paystack payment"""
    import requests
    try:
        base_url = os.getenv('BASE_URL', 'http://localhost:8000')
        # Remove trailing slash if present
        base_url = base_url.rstrip('/')
        callback_url = f"{base_url}/intake/{reference}"
        
        logger.info(f"Initializing Paystack payment - Callback URL: {callback_url}")
        
        headers = {
            "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "email": email,
            "amount": int(amount * 100),  # Convert to kobo
            "reference": reference,
            "callback_url": callback_url,
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
            json=data,
            timeout=10
        )
        
        logger.info(f"Paystack response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Paystack response: {result}")
            
            if result.get("status"):
                auth_url = result["data"]["authorization_url"]
                logger.info(f"Payment URL generated: {auth_url}")
                return {
                    "success": True,
                    "authorization_url": auth_url,
                    "access_code": result["data"]["access_code"],
                    "callback_url": callback_url
                }
            else:
                error_msg = result.get("message", "Unknown error")
                logger.error(f"Paystack error: {error_msg}")
                return {"success": False, "error": error_msg}
        else:
            error_text = response.text
            logger.error(f"Paystack API error: {response.status_code} - {error_text}")
            return {"success": False, "error": f"API returned {response.status_code}: {error_text}"}
    except Exception as e:
        logger.error(f"Paystack initiation error: {e}")
        import traceback
        logger.error(traceback.format_exc())
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
        # Test database connection first
        try:
            db.execute(text("SELECT 1"))
        except Exception as db_error:
            logger.error(f"Database connection error in payment initiation: {db_error}")
            raise HTTPException(
                status_code=503, 
                detail="Database connection error. Please try again in a moment."
            )
        # Pending intake for this email: always finish that flow first
        current_epoch = get_registration_lobby_epoch(db)
        pending_intake = (
            db.query(Entry)
            .filter(
                Entry.contact_email == email,
                Entry.payment_status == "completed",
                Entry.codm_id.is_(None),
            )
            .order_by(Entry.created_at.desc())
            .first()
        )
        if pending_intake:
            pending_ep = _payment_epoch_for_duplicate_checks(pending_intake)
            if current_epoch <= pending_ep:
                return {
                    "success": True,
                    "payment_completed": True,
                    "message": "Payment already completed. Please complete your registration",
                    "redirect_url": f"/intake/{pending_intake.payment_reference}",
                }
            # Paid before a prior lobby reset; new cycle — allow a fresh checkout

        already_in_open_lobby = db.query(Entry).filter(
            Entry.contact_email == email,
            Entry.payment_status == "completed",
            Entry.codm_id.isnot(None),
            Entry.excluded == False,
            Entry.lobby_epoch == current_epoch,
        ).first()
        if already_in_open_lobby:
            return {
                "success": True,
                "already_registered": True,
                "message": "You are already registered for the current lobby. You can register again when the next lobby opens.",
                "redirect_url": f"/thank-you/{already_in_open_lobby.payment_reference}",
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

@app.get("/intake", response_class=HTMLResponse)
async def intake_page_query(
    request: Request,
    db: Session = Depends(get_db),
    reference: Optional[str] = Query(None, alias="reference"),
    trxref: Optional[str] = Query(None, alias="trxref")
):
    """Player intake form page - handles Paystack redirect with query parameters"""
    # Handle Paystack redirect with query parameters (reference or trxref)
    payment_reference = reference or trxref
    if not payment_reference:
        raise HTTPException(status_code=400, detail="Payment reference is required")
    
    # Process directly instead of redirecting to avoid double slash issues
    logger.info(f"Intake page accessed via query params for reference: {payment_reference}")
    return await intake_page(request, payment_reference, db)

@app.get("/intake/{payment_reference}", response_class=HTMLResponse)
async def intake_page(
    request: Request, 
    payment_reference: str, 
    db: Session = Depends(get_db)
):
    """Player intake form page (locked to payment reference)"""
    logger.info(f"Intake page accessed for reference: {payment_reference}")
    
    # Verify payment first
    entry = db.query(Entry).filter(Entry.payment_reference == payment_reference).first()
    if not entry:
        logger.error(f"Entry not found for reference: {payment_reference}")
        logger.error(f"Available entries: {[e.payment_reference for e in db.query(Entry).limit(10).all()]}")
        raise HTTPException(
            status_code=404, 
            detail=f"Payment reference '{payment_reference}' not found. Please contact support if you completed payment."
        )
    
    if entry.payment_status != "completed":
        # Verify payment
        logger.info(f"Verifying payment for reference: {payment_reference}")
        if PAYMENT_GATEWAY == "paystack":
            verification = verify_paystack_payment(payment_reference)
        else:
            verification = verify_flutterwave_payment(payment_reference)
        
        logger.info(f"Verification result: {verification}")
        
        if verification.get("verified"):
            mark_entry_payment_completed(entry, db)
            payment = db.query(Payment).filter(Payment.reference == payment_reference).first()
            if payment:
                payment.status = "success"
                payment.gateway_response = verification.get("gateway_response", "")
            db.commit()
            db.refresh(entry)  # Refresh to get updated status
            logger.info(f"Payment verified and updated for reference: {payment_reference}")
            
            # Check if already submitted - redirect immediately after verification
            if entry.codm_id:
                return RedirectResponse(url=f"/thank-you/{payment_reference}", status_code=302)
        else:
            logger.warning(f"Payment verification failed for reference: {payment_reference}, reason: {verification.get('error', 'Unknown')}")
            return templates.TemplateResponse("payment_pending.html", {
                "request": request,
                "payment_reference": payment_reference,
                "error": verification.get("error", "Payment verification failed")
            })
    
    # Check if already submitted (double check after refresh)
    if entry.codm_id:
        return RedirectResponse(url=f"/thank-you/{payment_reference}", status_code=302)
    
    # Payment verified, show intake form
    try:
        cycle = calculate_registration_group_status(db)
        remaining_in_group = cycle["remaining_in_group"]
    except Exception:
        remaining_in_group = LOBBY_GROUP_SIZE

    return templates.TemplateResponse("intake.html", {
        "request": request,
        "payment_reference": payment_reference,
        "remaining_in_group": remaining_in_group,
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
                mark_entry_payment_completed(entry, db)
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

        current_epoch = get_registration_lobby_epoch(db)
        total_before = db.query(Entry).filter(
            Entry.payment_status == "completed",
            Entry.codm_id.isnot(None),
            Entry.excluded == False,
            Entry.lobby_epoch == current_epoch,
        ).count()
        lobby_group = (total_before // max(1, LOBBY_GROUP_SIZE)) + 1

        codm_key = normalize_codm_for_match(data.codm_id)
        phone_key = normalize_phone_digits(phone_cleaned)
        email_key = (data.contact_email or "").strip().lower()

        # Same email/phone/CODM once per registration lobby epoch (not per 100-slot batch).
        peers = db.query(Entry).filter(
            Entry.payment_status == "completed",
            Entry.codm_id.isnot(None),
            Entry.excluded == False,
            Entry.lobby_epoch == current_epoch,
            Entry.id != entry.id,
        ).all()
        for o in peers:
            if normalize_codm_for_match(o.codm_id) == codm_key:
                raise HTTPException(
                    status_code=409,
                    detail="This CODM ID is already registered for the current lobby.",
                )
            if (o.contact_email or "").strip().lower() == email_key:
                raise HTTPException(
                    status_code=409,
                    detail="This email is already registered for the current lobby.",
                )
            if phone_key and normalize_phone_digits(o.contact_phone) == phone_key:
                raise HTTPException(
                    status_code=409,
                    detail="This phone number is already registered for the current lobby.",
                )

        # Update entry with player details (use cleaned values)
        entry.codm_id = data.codm_id
        entry.contact_phone = phone_cleaned
        entry.contact_email = data.contact_email
        entry.region = data.region
        entry.bank_name = data.bank_name
        entry.account_number = account_cleaned
        entry.account_name = data.account_name
        entry.lobby_group = lobby_group
        entry.lobby_epoch = current_epoch
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
                "per_kill_value": per_kill_value,
                "kill_count": entry.kill_count or 0,
            }
            
            sheets_tab = get_sheets_tab_for_current_lobby(db)
            logger.info(f"Attempting to save entry to Google Sheets (tab={sheets_tab}): {entry.payment_reference}")
            result = save_entry_to_sheets(entry_data, target_sheet=sheets_tab)
            if result:
                logger.info(f"Successfully saved entry to Google Sheets: {entry.payment_reference}")
            else:
                logger.warning(f"Failed to save entry to Google Sheets: {entry.payment_reference}")
                logger.warning("Check GOOGLE_SHEETS_ENABLED, GOOGLE_SPREADSHEET_ID, and credentials file")
        except Exception as e:
            logger.error(f"Error saving to Google Sheets: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        # Get current WhatsApp link from database
        whatsapp_link = get_whatsapp_link(db)
        
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
            f"Welcome! Join our WhatsApp group: {whatsapp_link}",
            db
        )
        
        # Check for registration milestone (100 users)
        check_registration_milestone(db)
        
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
    
    # Get WhatsApp link from database
    whatsapp_link = get_whatsapp_link(db)
    
    return templates.TemplateResponse("thank_you.html", {
        "request": request,
        "whatsapp_link": whatsapp_link,
        "codm_id": entry.codm_id
    })

def calculate_registration_group_status(db: Session) -> dict:
    """Compute current lobby group + remaining spots until the next reset (current admin lobby epoch only)."""
    group_size = max(1, LOBBY_GROUP_SIZE)
    epoch = get_registration_lobby_epoch(db)

    total_registrations = db.query(Entry).filter(
        Entry.payment_status == "completed",
        Entry.codm_id.isnot(None),
        Entry.excluded == False,
        Entry.lobby_epoch == epoch,
    ).count()

    group_number = (total_registrations // group_size) + 1
    within_group_count = total_registrations % group_size
    remaining_in_group = group_size - within_group_count

    if remaining_in_group < 0:
        remaining_in_group = 0

    return {
        "group_size": group_size,
        "total_registrations": total_registrations,
        "group_number": group_number,
        "within_group_count": within_group_count,
        "remaining_in_group": remaining_in_group,
        "registration_lobby_epoch": epoch,
        "registration_lobby_name": get_registration_lobby_name(db),
    }


@app.get("/api/registration-group-status")
async def registration_group_status(db: Session = Depends(get_db)):
    """
    Public endpoint for the countdown.

    Counts only the current admin registration lobby epoch. Admins can bump the epoch
    to reset the countdown without waiting for `LOBBY_GROUP_SIZE` registrations.

    Within an epoch, groups advance every `LOBBY_GROUP_SIZE` registrations.
    """
    status = calculate_registration_group_status(db)
    return {
        "success": True,
        **status,
    }

# Admin Routes
@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request, error: Optional[str] = Query(None)):
    """Admin login page"""
    return templates.TemplateResponse("admin_login.html", {"request": request, "error": error})

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
        
        issued_at = int(time.time())
        session_token = _make_admin_session_token(admin.id, issued_at)
        response = RedirectResponse(url="/admin/dashboard", status_code=302)
        response.set_cookie(
            key=ADMIN_SESSION_COOKIE_NAME,
            value=session_token,
            httponly=True,
            secure=(request.url.scheme == "https"),
            samesite="lax",
            max_age=ADMIN_SESSION_TTL_SECONDS,
            path="/",
        )
        return response
    except Exception as e:
        logger.error(f"Admin login error: {e}")
        return templates.TemplateResponse("admin_login.html", {
            "request": request,
            "error": "An error occurred. Please try again."
        }, status_code=500)

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    admin_session: Optional[str] = Cookie(None, alias=ADMIN_SESSION_COOKIE_NAME),
):
    """Admin dashboard"""
    # HTML UX: redirect back to login page instead of returning JSON 401.
    if not admin_session:
        return RedirectResponse(url="/admin/login?error=Admin%20authentication%20required", status_code=302)

    admin_id = _verify_admin_session_token(admin_session)
    if not admin_id:
        return RedirectResponse(url="/admin/login?error=Invalid%20or%20expired%20session", status_code=302)

    admin = db.query(AdminUser).filter(AdminUser.id == admin_id, AdminUser.is_active == True).first()
    if not admin:
        return RedirectResponse(url="/admin/login?error=Invalid%20or%20inactive%20session", status_code=302)

    entries = db.query(Entry).filter(Entry.payment_status == "completed").order_by(Entry.created_at.desc()).all()
    
    # Count total registrations (exclude removed players)
    total_registrations = db.query(Entry).filter(
        Entry.payment_status == "completed",
        Entry.codm_id.isnot(None),
        Entry.excluded == False
    ).count()
    
    # Get WhatsApp link and COD lobby link from database
    whatsapp_link = get_whatsapp_link(db)
    cod_lobby_link = get_cod_lobby_link(db)
    tournament_status = get_tournament_status(db)
    
    # Check if milestone reached
    milestone = db.query(RegistrationMilestone).filter(
        RegistrationMilestone.milestone_count == REGISTRATION_MILESTONE,
        RegistrationMilestone.notified == True
    ).first()

    cycle = calculate_registration_group_status(db)
    
    stats = {
        "total_entries": len(entries),
        "total_registrations": total_registrations,
        "winners": len([e for e in entries if e.is_winner]),
        "pending_payouts": len([e for e in entries if e.payout_status == "pending" and not (e.excluded or False)]),
        "completed_payouts": len([e for e in entries if e.payout_status == "completed"]),
        "whatsapp_link": whatsapp_link,
        "cod_lobby_link": cod_lobby_link,
        "tournament_status": tournament_status,
        "milestone_threshold": REGISTRATION_MILESTONE,
        "milestone_reached": milestone is not None,
        "registration_lobby_epoch": cycle["registration_lobby_epoch"],
        "registration_lobby_name": cycle["registration_lobby_name"],
        "current_cycle_registrations": cycle["total_registrations"],
        "current_cycle_group_number": cycle["group_number"],
        "current_cycle_remaining_in_group": cycle["remaining_in_group"],
    }
    
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "entries": entries,
        "stats": stats
    })

@app.get("/admin/logout")
async def admin_logout(request: Request):
    """Clear admin session cookie and redirect to login page."""
    response = RedirectResponse(url="/admin/login?error=Signed%20out", status_code=302)
    response.set_cookie(
        key=ADMIN_SESSION_COOKIE_NAME,
        value="",
        httponly=True,
        secure=(request.url.scheme == "https"),
        samesite="lax",
        max_age=0,
        path="/",
    )
    return response

@app.post("/api/admin/mark-winner")
async def mark_winner(data: MarkWinnerRequest, db: Session = Depends(get_db), admin: AdminUser = Depends(get_current_admin)):
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
async def trigger_payout(data: TriggerPayoutRequest, db: Session = Depends(get_db), admin: AdminUser = Depends(get_current_admin)):
    """Trigger payout for entry. Amount = kill_count * per_kill_value * dollar_rate"""
    entry = db.query(Entry).filter(Entry.id == data.entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    if entry.payout_status == "completed":
        raise HTTPException(status_code=400, detail="Payout already completed")
    
    per_kill_value = float(os.getenv("PER_KILL_VALUE", "0.6"))
    dollar_rate = get_live_dollar_rate()
    amount = (entry.kill_count or 0) * per_kill_value * dollar_rate
    if amount <= 0:
        amount = float(entry.entry_fee or 0)  # Fallback: entry fee only
    
    # Create payout record
    payout = Payout(
        entry_id=entry.id,
        amount=amount,
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
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
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
                "kill_count": e.kill_count or 0,
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
            "current_rate": float(os.getenv("DOLLAR_RATE", "100"))
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
                    mark_entry_payment_completed(entry, db)

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
                        updates = {"payment_status": "completed"}
                        if entry.codm_id:
                            updates["codm_id"] = entry.codm_id
                        if entry.contact_phone:
                            updates["contact_phone"] = entry.contact_phone
                        elif entry.contact_email:
                            updates["contact_email"] = entry.contact_email
                        update_entry_in_sheets(reference, updates, target_sheet=get_sheets_tab_for_current_lobby(db))
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

# Admin Settings Routes
class UpdateWhatsAppLinkRequest(BaseModel):
    whatsapp_link: str = Field(..., min_length=1, description="WhatsApp group link")

class CreateAdminUserRequest(BaseModel):
    username: str = Field(..., min_length=3, description="Admin username")
    email: Optional[EmailStr] = None
    password: str = Field(..., min_length=6, description="Admin password")

class UpdateCodLobbyLinkRequest(BaseModel):
    cod_lobby_link: str = Field(..., description="COD lobby link")

class UpdateTournamentStatusRequest(BaseModel):
    status: str = Field(..., description="active, closed, or archived")

class UpdateKillCountRequest(BaseModel):
    entry_id: str
    kill_count: int = Field(..., ge=0, description="Kill count")

class LobbyCrossCheckRequest(BaseModel):
    lobby_player_ids: List[str] = Field(..., description="List of CODM IDs from lobby")

class RemovePlayerRequest(BaseModel):
    entry_id: str

class RemoveAdminUserRequest(BaseModel):
    admin_user_id: str = Field(..., description="Admin user id to deactivate/remove")


class ResetRegistrationLobbyRequest(BaseModel):
    lobby_name: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Optional display name for the new cycle; default Lobby {epoch} if omitted or blank",
    )


class SetRegistrationLobbyNameRequest(BaseModel):
    lobby_name: str = Field(default="", max_length=200, description="Shown on public signup; empty hides the name line")


@app.get("/api/admin/stats")
async def get_admin_stats(db: Session = Depends(get_db), admin: AdminUser = Depends(get_current_admin)):
    """Get admin statistics including registration count"""
    try:
        # Count total registrations (entries with payment completed and codm_id filled)
        total_registrations = db.query(Entry).filter(
            Entry.payment_status == "completed",
            Entry.codm_id.isnot(None)
        ).count()
        
        # Count all entries
        total_entries = db.query(Entry).filter(Entry.payment_status == "completed").count()
        
        # Count winners
        winners = db.query(Entry).filter(Entry.is_winner == True).count()
        
        # Count pending payouts
        pending_payouts = db.query(Entry).filter(
            Entry.is_winner == True,
            Entry.payout_status == "pending"
        ).count()
        
        # Get WhatsApp link, COD lobby link, tournament status
        whatsapp_link = get_whatsapp_link(db)
        cod_lobby_link = get_cod_lobby_link(db)
        tournament_status = get_tournament_status(db)
        
        # Check if milestone reached
        milestone = db.query(RegistrationMilestone).filter(
            RegistrationMilestone.milestone_count == REGISTRATION_MILESTONE,
            RegistrationMilestone.notified == True
        ).first()

        cycle = calculate_registration_group_status(db)
        
        return {
            "success": True,
            "stats": {
                "total_registrations": total_registrations,
                "total_entries": total_entries,
                "winners": winners,
                "pending_payouts": pending_payouts,
                "whatsapp_link": whatsapp_link,
                "cod_lobby_link": cod_lobby_link,
                "tournament_status": tournament_status,
                "milestone_threshold": REGISTRATION_MILESTONE,
                "milestone_reached": milestone is not None,
                "milestone_notified_at": milestone.notification_sent_at.isoformat() if milestone else None,
                "registration_lobby_epoch": cycle["registration_lobby_epoch"],
                "registration_lobby_name": cycle["registration_lobby_name"],
                "current_cycle_registrations": cycle["total_registrations"],
                "current_cycle_group_number": cycle["group_number"],
                "current_cycle_remaining_in_group": cycle["remaining_in_group"],
            }
        }
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/admin/update-whatsapp-link")
async def update_whatsapp_link(
    data: UpdateWhatsAppLinkRequest,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    """Update WhatsApp group link (Admin only)"""
    try:
        if not data.whatsapp_link.startswith(("http://", "https://")):
            raise HTTPException(status_code=400, detail="WhatsApp link must be a valid URL")
        set_whatsapp_link(db, data.whatsapp_link)
        logger.info(f"WhatsApp link updated to: {data.whatsapp_link}")
        return {
            "success": True,
            "message": "WhatsApp link updated successfully",
            "whatsapp_link": data.whatsapp_link
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating WhatsApp link: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/update-cod-lobby-link")
async def update_cod_lobby_link(
    data: UpdateCodLobbyLinkRequest,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    """Update COD lobby link (Admin only)"""
    try:
        set_cod_lobby_link(db, data.cod_lobby_link)
        return {"success": True, "message": "COD lobby link updated", "cod_lobby_link": data.cod_lobby_link}
    except Exception as e:
        logger.error(f"Error updating COD lobby link: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/update-tournament-status")
async def update_tournament_status(
    data: UpdateTournamentStatusRequest,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    """Update tournament status: active, closed, archived"""
    try:
        set_tournament_status(db, data.status)
        return {"success": True, "message": f"Tournament status set to {data.status}", "status": data.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating tournament status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/reset-registration-lobby")
async def reset_registration_lobby(
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
    data: ResetRegistrationLobbyRequest = Body(default_factory=ResetRegistrationLobbyRequest),
):
    """
    Open a new registration lobby cycle: public countdown and per-lobby duplicate rules
    apply only to entries recorded from now on (same email/CODM/phone can register again).
    """
    try:
        new_epoch = bump_registration_lobby_epoch(db, admin.id)
        raw = (data.lobby_name or "").strip()
        display_name = raw if raw else f"Lobby {new_epoch}"
        set_registration_lobby_name(db, display_name, admin.id)
        cycle = calculate_registration_group_status(db)
        return {
            "success": True,
            "message": "New registration lobby cycle started.",
            "registration_lobby_epoch": new_epoch,
            "registration_lobby_name": cycle["registration_lobby_name"],
            "current_cycle_registrations": cycle["total_registrations"],
            "current_cycle_group_number": cycle["group_number"],
            "current_cycle_remaining_in_group": cycle["remaining_in_group"],
        }
    except Exception as e:
        logger.error(f"Error resetting registration lobby: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/set-registration-lobby-name")
async def set_registration_lobby_name_route(
    data: SetRegistrationLobbyNameRequest,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    """Update the public display name for the current registration lobby (no cycle reset)."""
    try:
        set_registration_lobby_name(db, data.lobby_name, admin.id)
        name = get_registration_lobby_name(db)
        return {"success": True, "message": "Lobby name updated", "registration_lobby_name": name}
    except Exception as e:
        logger.error(f"Error setting registration lobby name: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/update-kill-count")
async def update_kill_count(
    data: UpdateKillCountRequest,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    """Update kill count for an entry and sync to Google Sheets"""
    try:
        entry = db.query(Entry).filter(Entry.id == data.entry_id).first()
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        entry.kill_count = data.kill_count
        db.commit()
        db.refresh(entry)
        # Sync to Google Sheets
        try:
            per_kill_value = float(os.getenv("PER_KILL_VALUE", "0.6"))
            dollar_rate = get_live_dollar_rate()
            kc = data.kill_count or 0
            payout_ngn = kc * per_kill_value * dollar_rate
            entry_fee = float(entry.entry_fee) if entry.entry_fee else 0
            payout_str = f"₦{payout_ngn:,.2f}" if kc else f"₦{entry_fee:,.2f}"
            update_entry_in_sheets(entry.payment_reference, {
                "codm_id": entry.codm_id,
                "contact_phone": entry.contact_phone or "",
                "kill": data.kill_count,
                "payout": payout_str,
            }, target_sheet=get_sheets_tab_for_current_lobby(db))
        except Exception as e:
            logger.warning(f"Failed to sync kill count to Google Sheets: {e}")
        return {"success": True, "message": "Kill count updated", "entry_id": entry.id, "kill_count": data.kill_count}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating kill count: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/lobby-cross-check")
async def lobby_cross_check(
    data: LobbyCrossCheckRequest,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    """Compare lobby player IDs against registered entries. Returns matches, in_lobby_not_registered, in_sheets_not_in_lobby"""
    try:
        lobby_ids = [pid.strip() for pid in data.lobby_player_ids if pid.strip()]
        registered = db.query(Entry).filter(
            Entry.payment_status == "completed",
            Entry.codm_id.isnot(None),
            Entry.excluded == False
        ).all()
        registered_ids = {e.codm_id.strip().lower(): e for e in registered if e.codm_id}
        in_lobby_not_registered = [pid for pid in lobby_ids if pid.lower() not in registered_ids]
        in_sheets_not_in_lobby = [e.codm_id for e in registered if e.codm_id and e.codm_id.strip().lower() not in [p.lower() for p in lobby_ids]]
        matches = [pid for pid in lobby_ids if pid.lower() in registered_ids]
        return {
            "success": True,
            "matches": matches,
            "in_lobby_not_registered": in_lobby_not_registered,
            "in_sheets_not_in_lobby": in_sheets_not_in_lobby,
            "match_count": len(matches),
            "mismatch_count": len(in_lobby_not_registered) + len(in_sheets_not_in_lobby)
        }
    except Exception as e:
        logger.error(f"Error in lobby cross-check: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/export-csv")
async def export_csv(db: Session = Depends(get_db), admin: AdminUser = Depends(get_current_admin)):
    """Export all entries as CSV file"""
    from fastapi.responses import StreamingResponse
    import csv
    import io
    try:
        entries = db.query(Entry).filter(
            Entry.payment_status == "completed",
            Entry.codm_id.isnot(None),
            Entry.excluded == False
        ).order_by(Entry.created_at.desc()).all()
        dollar_rate = get_live_dollar_rate()
        per_kill_value = float(os.getenv("PER_KILL_VALUE", "0.6"))
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Time",
            "Gamer ID Name",
            "Number",
            "Region",
            "Bank Name",
            "Bank Account Number",
            "Kill",
            "Payout",
            "Paid",
        ])
        for e in entries:
            entry_fee = float(e.entry_fee) if e.entry_fee else 0
            kill_count = e.kill_count or 0
            payout_ngn = kill_count * per_kill_value * dollar_rate
            payout_str = f"₦{payout_ngn:,.2f}" if kill_count else f"₦{entry_fee:,.2f}"
            writer.writerow([
                e.created_at.strftime("%I:%M %p") if e.created_at else "",
                e.codm_id or "",
                e.contact_phone or "",
                e.region or "",
                e.bank_name or "",
                e.account_number or "",
                kill_count,
                payout_str,
                "Yes" if e.payout_status == "completed" else "",
            ])
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=clasharena_entries.csv"}
        )
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/bulk-payout")
async def bulk_payout(db: Session = Depends(get_db), admin: AdminUser = Depends(get_current_admin)):
    """Trigger payout for all registered players with pending payout. Amount = kill_count * per_kill_value * dollar_rate"""
    try:
        per_kill_value = float(os.getenv("PER_KILL_VALUE", "0.6"))
        dollar_rate = get_live_dollar_rate()
        entries = db.query(Entry).filter(
            Entry.payment_status == "completed",
            Entry.codm_id.isnot(None),
            Entry.excluded == False,
            Entry.payout_status != "completed"
        ).all()
        processed = 0
        errors = []
        for entry in entries:
            try:
                amount = (entry.kill_count or 0) * per_kill_value * dollar_rate
                payout = Payout(
                    entry_id=entry.id,
                    amount=amount,
                    currency="NGN",
                    status="completed",
                    gateway="bank_transfer"
                )
                db.add(payout)
                entry.payout_status = "completed"
                db.commit()
                processed += 1
                try:
                    update_entry_in_sheets(entry.payment_reference, {
                        "codm_id": entry.codm_id,
                        "contact_phone": entry.contact_phone or "",
                        "payment_status": "completed",
                    }, target_sheet=get_sheets_tab_for_current_lobby(db))
                except Exception:
                    pass
            except Exception as e:
                errors.append({"entry_id": entry.id, "error": str(e)})
                db.rollback()
        return {"success": True, "processed": processed, "total_pending": len(entries), "errors": errors}
    except Exception as e:
        logger.error(f"Error in bulk payout: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/remove-player")
async def remove_player(data: RemovePlayerRequest, db: Session = Depends(get_db), admin: AdminUser = Depends(get_current_admin)):
    """Mark player as excluded (details incorrect - remove from lobby/payout)"""
    try:
        entry = db.query(Entry).filter(Entry.id == data.entry_id).first()
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        entry.excluded = True
        db.commit()
        return {"success": True, "message": "Player removed from active list"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing player: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/restore-player")
async def restore_player(data: RemovePlayerRequest, db: Session = Depends(get_db), admin: AdminUser = Depends(get_current_admin)):
    """Restore excluded player back to active list"""
    try:
        entry = db.query(Entry).filter(Entry.id == data.entry_id).first()
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        entry.excluded = False
        db.commit()
        return {"success": True, "message": "Player restored"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring player: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/registration-count")
async def get_registration_count(db: Session = Depends(get_db), admin: AdminUser = Depends(get_current_admin)):
    """Get current registration count"""
    try:
        # Count total registrations (entries with payment completed and codm_id filled)
        total_registrations = db.query(Entry).filter(
            Entry.payment_status == "completed",
            Entry.codm_id.isnot(None)
        ).count()
        
        return {
            "success": True,
            "total_registrations": total_registrations,
            "milestone_threshold": REGISTRATION_MILESTONE,
            "milestone_reached": total_registrations >= REGISTRATION_MILESTONE,
            "remaining_to_milestone": max(0, REGISTRATION_MILESTONE - total_registrations)
        }
    except Exception as e:
        logger.error(f"Error getting registration count: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/admin/create-admin-user")
async def create_admin_user(
    data: CreateAdminUserRequest,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    """Create a new admin user (Admin only)"""
    try:
        # Reactivate/update if username already exists (deactivation keeps the row)
        existing_by_username = db.query(AdminUser).filter(AdminUser.username == data.username).first()
        if existing_by_username:
            # If an email is provided, validate uniqueness if it differs.
            if data.email and existing_by_username.email != data.email:
                conflicting_email = (
                    db.query(AdminUser)
                    .filter(AdminUser.email == data.email, AdminUser.id != existing_by_username.id)
                    .first()
                )
                if conflicting_email:
                    raise HTTPException(status_code=400, detail=f"Email '{data.email}' already exists")

                existing_by_username.email = data.email

            existing_by_username.password_hash = hash_password(data.password)
            existing_by_username.is_active = True

            db.commit()
            db.refresh(existing_by_username)

            logger.info(f"Admin user reactivated/updated: {data.username}")
            return {
                "success": True,
                "message": f"Admin user '{data.username}' reactivated successfully",
                "admin_id": existing_by_username.id,
                "username": existing_by_username.username,
                "email": existing_by_username.email,
                "reactivated": True,
            }

        # If username doesn't exist, check if email already exists (and potentially reactivate by email)
        if data.email:
            existing_by_email = db.query(AdminUser).filter(AdminUser.email == data.email).first()
            if existing_by_email:
                # Username is unique; since it didn't exist above, this should be safe.
                existing_by_email.username = data.username
                existing_by_email.password_hash = hash_password(data.password)
                existing_by_email.is_active = True

                db.commit()
                db.refresh(existing_by_email)

                logger.info(f"Admin user reactivated/updated by email: {data.username}")
                return {
                    "success": True,
                    "message": f"Admin user '{data.username}' reactivated successfully",
                    "admin_id": existing_by_email.id,
                    "username": existing_by_email.username,
                    "email": existing_by_email.email,
                    "reactivated": True,
                }

        # Create new admin user (both username and email are available)
        new_admin = AdminUser(
            username=data.username,
            password_hash=hash_password(data.password),
            email=data.email,
            is_active=True,
        )

        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)

        logger.info(f"New admin user created: {data.username}")

        return {
            "success": True,
            "message": f"Admin user '{data.username}' created successfully",
            "admin_id": new_admin.id,
            "username": new_admin.username,
            "email": new_admin.email,
            "reactivated": False,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create admin user: {str(e)}")

@app.post("/api/admin/deactivate-admin-user")
async def deactivate_admin_user(
    data: RemoveAdminUserRequest,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    """Deactivate/remove an admin user (sets is_active=false).

    Important: admins cannot deactivate their own account to avoid lockout.
    """
    try:
        target = db.query(AdminUser).filter(AdminUser.id == data.admin_user_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="Admin user not found")

        if target.id == admin.id:
            raise HTTPException(status_code=400, detail="You cannot deactivate your own admin account")

        target.is_active = False
        db.commit()
        return {"success": True, "message": "Admin user deactivated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating admin user: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/admin-users")
async def get_admin_users(db: Session = Depends(get_db), admin: AdminUser = Depends(get_current_admin)):
    """Get list of all admin users"""
    try:
        admins = db.query(AdminUser).order_by(AdminUser.created_at.desc()).all()
        
        return {
            "success": True,
            "admins": [
                {
                    "id": admin.id,
                    "username": admin.username,
                    "email": admin.email,
                    "is_active": admin.is_active,
                    "created_at": admin.created_at.isoformat() if admin.created_at else None
                }
                for admin in admins
            ]
        }
    except Exception as e:
        logger.error(f"Error getting admin users: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "clasharena-mvp"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 