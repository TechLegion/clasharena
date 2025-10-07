from celery import Celery
import os
from datetime import datetime
import requests

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Create Celery app
app = Celery('clasharena_workers')
app.conf.broker_url = REDIS_URL
app.conf.result_backend = REDIS_URL
app.conf.task_serializer = 'json'
app.conf.accept_content = ['json']
app.conf.result_serializer = 'json'
app.conf.timezone = 'UTC'
app.conf.enable_utc = True

# Task routes
app.conf.task_routes = {
    'workers.main.send_email': {'queue': 'email'},
    'workers.main.send_sms': {'queue': 'sms'},
    'workers.main.process_payment': {'queue': 'payments'},
    'workers.main.process_match_result': {'queue': 'matches'},
    'workers.main.send_notification': {'queue': 'notifications'},
}

@app.task(bind=True, max_retries=3)
def send_email(self, to_email, subject, body, email_type='general'):
    """Send email notification"""
    try:
        # In production, integrate with email service like SendGrid, AWS SES, etc.
        print(f"Sending email to {to_email}: {subject}")
        
        # Simulate email sending
        email_data = {
            "to": to_email,
            "subject": subject,
            "body": body,
            "type": email_type,
            "sent_at": datetime.utcnow().isoformat()
        }
        
        # Log email sending
        print(f"Email sent successfully: {email_data}")
        
        return {
            "status": "success",
            "message": "Email sent successfully",
            "email_data": email_data
        }
        
    except Exception as exc:
        print(f"Email sending failed: {exc}")
        # Retry the task
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@app.task(bind=True, max_retries=3)
def send_sms(self, phone_number, message):
    """Send SMS notification"""
    try:
        # In production, integrate with SMS service like Twilio, AWS SNS, etc.
        print(f"Sending SMS to {phone_number}: {message}")
        
        # Simulate SMS sending
        sms_data = {
            "to": phone_number,
            "message": message,
            "sent_at": datetime.utcnow().isoformat()
        }
        
        # Log SMS sending
        print(f"SMS sent successfully: {sms_data}")
        
        return {
            "status": "success",
            "message": "SMS sent successfully",
            "sms_data": sms_data
        }
        
    except Exception as exc:
        print(f"SMS sending failed: {exc}")
        # Retry the task
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@app.task(bind=True, max_retries=5)
def process_payment(self, payment_data):
    """Process payment asynchronously"""
    try:
        payment_id = payment_data.get("payment_id")
        amount = payment_data.get("amount")
        payment_method = payment_data.get("payment_method")
        
        print(f"Processing payment {payment_id} for amount {amount} via {payment_method}")
        
        # Simulate payment processing
        if amount > 0:
            # Simulate successful payment
            result = {
                "status": "success",
                "payment_id": payment_id,
                "amount": amount,
                "method": payment_method,
                "processed_at": datetime.utcnow().isoformat(),
                "transaction_reference": f"TXN_{payment_id}_{int(datetime.utcnow().timestamp())}"
            }
        else:
            # Simulate failed payment
            result = {
                "status": "failed",
                "payment_id": payment_id,
                "error": "Invalid amount",
                "processed_at": datetime.utcnow().isoformat()
            }
        
        print(f"Payment processed: {result}")
        return result
        
    except Exception as exc:
        print(f"Payment processing failed: {exc}")
        # Retry the task
        raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))

@app.task(bind=True, max_retries=3)
def process_match_result(self, match_id, match_result):
    """Process match result asynchronously"""
    try:
        print(f"Processing match result for match {match_id}: {match_result}")
        
        # Update match in database
        # In production, this would make API calls to the match service
        result = {
            "match_id": match_id,
            "result": match_result,
            "processed_at": datetime.utcnow().isoformat(),
            "status": "completed"
        }
        
        print(f"Match result processed: {result}")
        return result
        
    except Exception as exc:
        print(f"Match result processing failed: {exc}")
        # Retry the task
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@app.task(bind=True, max_retries=3)
def send_notification(self, user_id, notification_type, message, data=None):
    """Send push notification"""
    try:
        print(f"Sending {notification_type} notification to user {user_id}: {message}")
        
        # In production, integrate with push notification service like Firebase, OneSignal, etc.
        notification_data = {
            "user_id": user_id,
            "type": notification_type,
            "message": message,
            "data": data or {},
            "sent_at": datetime.utcnow().isoformat()
        }
        
        # Log notification
        print(f"Notification sent: {notification_data}")
        
        return {
            "status": "success",
            "message": "Notification sent successfully",
            "notification_data": notification_data
        }
        
    except Exception as exc:
        print(f"Notification sending failed: {exc}")
        # Retry the task
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@app.task
def cleanup_old_data():
    """Clean up old data (run daily)"""
    try:
        print("Starting data cleanup task")
        
        # In production, implement actual cleanup logic
        # - Delete old logs
        # - Archive old transactions
        # - Clean up temporary files
        
        result = {
            "status": "success",
            "message": "Data cleanup completed",
            "cleaned_at": datetime.utcnow().isoformat()
        }
        
        print(f"Data cleanup completed: {result}")
        return result
        
    except Exception as exc:
        print(f"Data cleanup failed: {exc}")
        return {
            "status": "failed",
            "error": str(exc),
            "cleaned_at": datetime.utcnow().isoformat()
        }

@app.task
def generate_reports():
    """Generate daily reports"""
    try:
        print("Generating daily reports")
        
        # In production, implement actual report generation
        # - User statistics
        # - Revenue reports
        # - Match statistics
        
        result = {
            "status": "success",
            "message": "Reports generated successfully",
            "generated_at": datetime.utcnow().isoformat(),
            "reports": ["user_stats", "revenue_report", "match_stats"]
        }
        
        print(f"Reports generated: {result}")
        return result
        
    except Exception as exc:
        print(f"Report generation failed: {exc}")
        return {
            "status": "failed",
            "error": str(exc),
            "generated_at": datetime.utcnow().isoformat()
        }

if __name__ == '__main__':
    app.start()
