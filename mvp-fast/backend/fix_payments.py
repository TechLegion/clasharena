"""
Script to manually verify and update payment status for existing entries
Run this to fix payment status inconsistencies
"""
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Add parent directory to path
backend_dir = Path(__file__).parent
root_dir = backend_dir.parent.resolve()
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from database.db import get_db, engine
from database.models import Entry, Payment
import requests
import json
import os

PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")
PAYMENT_GATEWAY = os.getenv("PAYMENT_GATEWAY", "paystack")

def verify_paystack_payment(reference: str) -> dict:
    """Verify payment with Paystack"""
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
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") and data.get("data"):
                transaction_data = data["data"]
                transaction_status = transaction_data.get("status")
                
                if transaction_status == "success":
                    return {
                        "verified": True,
                        "amount": transaction_data.get("amount", 0) / 100,
                        "gateway_reference": transaction_data.get("reference", reference),
                        "gateway_response": json.dumps(data)
                    }
                else:
                    return {
                        "verified": False,
                        "status": transaction_status,
                        "gateway_response": json.dumps(data)
                    }
        return {"verified": False, "error": f"API returned {response.status_code}"}
    except Exception as e:
        return {"verified": False, "error": str(e)}

def main():
    """Fix payment statuses"""
    db = next(get_db())
    
    print("Checking entries with pending payment status...")
    pending_entries = db.query(Entry).filter(Entry.payment_status == "pending").all()
    
    print(f"Found {len(pending_entries)} entries with pending status")
    
    for entry in pending_entries:
        print(f"\nChecking entry: {entry.payment_reference} ({entry.contact_email})")
        
        if PAYMENT_GATEWAY == "paystack":
            verification = verify_paystack_payment(entry.payment_reference)
        else:
            print("Flutterwave verification not implemented in this script")
            continue
        
        if verification.get("verified"):
            print(f"  ✓ Payment verified! Updating status...")
            entry.payment_status = "completed"
            
            payment = db.query(Payment).filter(Payment.reference == entry.payment_reference).first()
            if payment:
                payment.status = "success"
                payment.gateway_response = verification.get("gateway_response", "")
            
            db.commit()
            print(f"  ✓ Status updated to completed")
        else:
            print(f"  ✗ Payment not verified: {verification.get('error', verification.get('status', 'Unknown'))}")
    
    print("\n" + "="*50)
    print("Checking for duplicate entries with same email...")
    
    from sqlalchemy import func
    duplicates = db.query(
        Entry.contact_email,
        func.count(Entry.id).label('count')
    ).filter(
        Entry.contact_email.isnot(None),
        Entry.contact_email != ""
    ).group_by(Entry.contact_email).having(func.count(Entry.id) > 1).all()
    
    print(f"Found {len(duplicates)} emails with multiple entries")
    
    for email, count in duplicates:
        print(f"\nEmail: {email} ({count} entries)")
        entries = db.query(Entry).filter(Entry.contact_email == email).order_by(Entry.created_at).all()
        
        completed_entries = [e for e in entries if e.payment_status == "completed"]
        if completed_entries:
            print(f"  ✓ Found {len(completed_entries)} completed entry/entries")
            for e in completed_entries:
                print(f"    - {e.payment_reference} (created: {e.created_at})")
            
            # Mark pending entries as cancelled or keep only the first completed one
            pending_for_email = [e for e in entries if e.payment_status == "pending"]
            if pending_for_email:
                print(f"  ⚠ Found {len(pending_for_email)} pending entries (will be left as-is)")
        else:
            print(f"  ⚠ No completed entries found")
    
    print("\nDone!")

if __name__ == "__main__":
    main()

