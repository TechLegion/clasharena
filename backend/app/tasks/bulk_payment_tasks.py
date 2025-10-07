"""
Celery tasks for processing bulk payments
"""
import logging
from celery import Celery
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.config import settings
from shared.models import BulkPayment, BulkPaymentRecipient as BulkRecipientDB, User, Transaction, Wallet
import httpx
import json

logger = logging.getLogger(__name__)

# Import Celery app
from app.core.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def process_bulk_payment(self, bulk_payment_id: str):
    """Process bulk payment by sending individual transfers via Paystack"""
    
    db = SessionLocal()
    try:
        # Get bulk payment
        bulk_payment = db.query(BulkPayment).filter(BulkPayment.id == bulk_payment_id).first()
        if not bulk_payment:
            logger.error(f"Bulk payment not found: {bulk_payment_id}")
            return {"status": "error", "message": "Bulk payment not found"}
        
        # Update status to processing
        bulk_payment.status = "processing"
        db.commit()
        
        # Get all pending recipients
        recipients = db.query(BulkRecipientDB).filter(
            BulkRecipientDB.bulk_payment_id == bulk_payment_id,
            BulkRecipientDB.status == "pending"
        ).all()
        
        logger.info(f"Processing {len(recipients)} recipients for bulk payment {bulk_payment_id}")
        
        successful_count = 0
        failed_count = 0
        
        for recipient in recipients:
            try:
                # Process individual transfer
                result = process_single_transfer(recipient, db)
                
                if result["status"] == "success":
                    successful_count += 1
                    recipient.status = "completed"
                    recipient.paystack_reference = result.get("reference")
                    
                    # Create transaction record
                    user = db.query(User).filter(User.id == recipient.user_id).first()
                    if user and user.wallet:
                        transaction = Transaction(
                            wallet_id=user.wallet.id,
                            amount=recipient.amount,
                            transaction_type="withdrawal",
                            status="completed",
                            reference=f"bulk_{bulk_payment_id}_{recipient.id}",
                            external_reference=result.get("reference"),
                            description=f"Bulk payment: {recipient.reason}"
                        )
                        db.add(transaction)
                        
                        # Update wallet balance (subtract for withdrawal)
                        user.wallet.balance -= recipient.amount
                    
                else:
                    failed_count += 1
                    recipient.status = "failed"
                    recipient.error_message = result.get("error", "Unknown error")
                    
            except Exception as e:
                logger.error(f"Error processing recipient {recipient.id}: {str(e)}")
                failed_count += 1
                recipient.status = "failed"
                recipient.error_message = str(e)
            
            # Update recipient record
            db.commit()
        
        # Update bulk payment status
        if failed_count == 0:
            bulk_payment.status = "completed"
        elif successful_count == 0:
            bulk_payment.status = "failed"
        else:
            bulk_payment.status = "partially_completed"
        
        db.commit()
        
        logger.info(f"Bulk payment {bulk_payment_id} completed: {successful_count} successful, {failed_count} failed")
        
        return {
            "status": "completed",
            "bulk_payment_id": bulk_payment_id,
            "successful_count": successful_count,
            "failed_count": failed_count
        }
        
    except Exception as e:
        logger.error(f"Bulk payment processing error: {str(e)}")
        if bulk_payment:
            bulk_payment.status = "failed"
            db.commit()
        
        # Retry the task
        raise self.retry(countdown=60, exc=e)
        
    finally:
        db.close()


async def process_single_transfer(recipient: BulkRecipientDB, db: Session) -> dict:
    """Process a single transfer via Flutterwave (cheaper) or Paystack (fallback)"""
    
    try:
        # Import Flutterwave service
        from app.services.flutterwave import flutterwave_service
        
        # Try Flutterwave first (50% cheaper)
        try:
            result = await flutterwave_service.transfer_to_bank(
                account_number=recipient.account_number,
                bank_code=recipient.bank_code,
                amount=recipient.amount,
                narration=recipient.reason,
                recipient_name=recipient.account_name
            )
            
            if result["status"]:
                return {
                    "status": "success",
                    "reference": result["data"]["reference"],
                    "provider": "flutterwave",
                    "transfer_id": result["data"]["transfer_id"]
                }
            else:
                logger.warning(f"Flutterwave transfer failed: {result['message']}, trying Paystack...")
                
        except Exception as e:
            logger.warning(f"Flutterwave error: {str(e)}, trying Paystack...")
        
        # Fallback to Paystack if Flutterwave fails
        try:
            transfer_data = {
                "source": "balance",
                "amount": int(recipient.amount * 100),  # Convert to kobo
                "recipient": recipient.account_number,
                "reason": recipient.reason,
                "reference": f"bulk_{recipient.bulk_payment_id}_{recipient.id}"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.paystack.co/transfer",
                    headers={
                        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
                        "Content-Type": "application/json"
                    },
                    json=transfer_data
                )
            
            if response.status_code == 200:
                result = response.json()
                if result["status"]:
                    return {
                        "status": "success",
                        "reference": result["data"]["reference"],
                        "provider": "paystack"
                    }
                else:
                    return {
                        "status": "error",
                        "error": result.get("message", "Transfer failed"),
                        "provider": "paystack"
                    }
            else:
                return {
                    "status": "error",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "provider": "paystack"
                }
                
        except httpx.TimeoutException:
            return {
                "status": "error",
                "error": "Request timeout",
                "provider": "paystack"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "provider": "paystack"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error": f"Transfer service error: {str(e)}"
        }


@celery_app.task
def notify_bulk_payment_recipients(bulk_payment_id: str):
    """Send notifications to bulk payment recipients"""
    
    db = SessionLocal()
    try:
        # Get bulk payment and recipients
        bulk_payment = db.query(BulkPayment).filter(BulkPayment.id == bulk_payment_id).first()
        if not bulk_payment:
            return {"status": "error", "message": "Bulk payment not found"}
        
        recipients = db.query(BulkRecipientDB).filter(
            BulkRecipientDB.bulk_payment_id == bulk_payment_id,
            BulkRecipientDB.status == "completed"
        ).all()
        
        # TODO: Implement SMS/Email notifications
        # For now, just log the notifications
        for recipient in recipients:
            logger.info(f"Would send notification to user {recipient.user_id} for amount ₦{recipient.amount}")
        
        return {
            "status": "success",
            "notifications_sent": len(recipients)
        }
        
    except Exception as e:
        logger.error(f"Notification error: {str(e)}")
        return {"status": "error", "message": str(e)}
        
    finally:
        db.close()
