"""
Celery tasks for OTP (One-Time Password) operations
"""
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))

from celery import current_task
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.celery_app import celery_app
from app.core.database import get_db
from app.core.config import settings
from shared.models import User, OTP

# SendGrid import (optional)
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

# Twilio import (optional)
try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False


@celery_app.task(bind=True)
def send_otp_sms_task(self, user_id: str, phone_number: str, purpose: str = "phone_verification"):
    """Send OTP via SMS"""
    try:
        # Update task status
        self.update_state(state='PROGRESS', meta={'status': 'Generating OTP...'})
        
        # Get database session
        db = next(get_db())
        
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            db.close()
            return {'success': False, 'error': 'User not found'}
        
        # Generate 6-digit OTP
        otp_code = secrets.randbelow(900000) + 100000  # 100000 to 999999
        otp_code_str = str(otp_code).zfill(6)
        
        # Set expiry time (10 minutes from now)
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        # Deactivate any existing OTPs for this user and purpose
        existing_otps = db.query(OTP).filter(
            OTP.user_id == user_id,
            OTP.purpose == purpose,
            OTP.is_used == False
        ).all()
        
        for otp in existing_otps:
            otp.is_used = True
        
        # Create new OTP record
        otp_record = OTP(
            user_id=user_id,
            email=phone_number,  # Store phone number in email field for SMS
            code=otp_code_str,
            purpose=purpose,
            expires_at=expires_at
        )
        
        db.add(otp_record)
        db.commit()
        
        # Update task status
        self.update_state(state='PROGRESS', meta={'status': 'Sending SMS...'})
        
        # Send SMS - try Twilio first, fallback to console
        if settings.TWILIO_ACCOUNT_SID and TWILIO_AVAILABLE:
            sms_sent = send_twilio_sms(phone_number, otp_code_str, user.username)
        else:
            sms_sent = send_verification_sms(phone_number, otp_code_str, user.username)
        
        db.close()
        
        return {
            'success': True,
            'message': 'OTP sent successfully via SMS',
            'expires_in_minutes': 10
        }
        
    except Exception as e:
        db.close()
        return {'success': False, 'error': str(e)}


@celery_app.task(bind=True)
def send_otp_email_task(self, user_id: str, email: str, purpose: str = "email_verification"):
    """Send OTP via email"""
    try:
        # Update task status
        self.update_state(state='PROGRESS', meta={'status': 'Generating OTP...'})
        
        # Get database session
        db = next(get_db())
        
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            db.close()
            return {'success': False, 'error': 'User not found'}
        
        # Generate 6-digit OTP
        otp_code = secrets.randbelow(900000) + 100000  # 100000 to 999999
        otp_code_str = str(otp_code).zfill(6)
        
        # Set expiry time (10 minutes from now)
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        # Deactivate any existing OTPs for this user and purpose
        existing_otps = db.query(OTP).filter(
            OTP.user_id == user_id,
            OTP.purpose == purpose,
            OTP.is_used == False
        ).all()
        
        for otp in existing_otps:
            otp.is_used = True
        
        # Create new OTP record
        otp_record = OTP(
            user_id=user_id,
            email=email,
            code=otp_code_str,
            purpose=purpose,
            expires_at=expires_at
        )
        
        db.add(otp_record)
        db.commit()
        
        # Update task status
        self.update_state(state='PROGRESS', meta={'status': 'Sending email...'})
        
        # Send email - try SendGrid first, fallback to console
        if settings.SENDGRID_API_KEY and SENDGRID_AVAILABLE:
            email_sent = send_sendgrid_email(email, otp_code_str, user.username)
        else:
            email_sent = send_verification_email(email, otp_code_str, user.username)
        
        db.close()
        
        return {
            'success': True,
            'message': 'OTP sent successfully',
            'expires_in_minutes': 10
        }
        
    except Exception as e:
        db.close()
        return {'success': False, 'error': str(e)}


@celery_app.task(bind=True)
def verify_otp_task(self, user_id: str, otp_code: str, purpose: str = "email_verification"):
    """Verify OTP code"""
    try:
        # Get database session
        db = next(get_db())
        
        # Find valid OTP
        otp_record = db.query(OTP).filter(
            OTP.user_id == user_id,
            OTP.code == otp_code,
            OTP.purpose == purpose,
            OTP.is_used == False,
            OTP.expires_at > datetime.utcnow()
        ).first()
        
        if not otp_record:
            db.close()
            return {'success': False, 'error': 'Invalid or expired OTP'}
        
        # Mark OTP as used
        otp_record.is_used = True
        
        # Update user email verification status
        user = db.query(User).filter(User.id == user_id).first()
        if user and purpose == "email_verification":
            user.email_verified = True
        
        db.commit()
        db.close()
        
        return {
            'success': True,
            'message': 'OTP verified successfully',
            'email_verified': True if purpose == "email_verification" else False
        }
        
    except Exception as e:
        db.close()
        return {'success': False, 'error': str(e)}


def send_verification_email(email: str, otp_code: str, username: str) -> bool:
    """Send verification email with OTP (development version)"""
    try:
        # For development, we'll just log the OTP
        # In production, you'd use SMTP or email service like SendGrid
        
        print("=" * 60)
        print("📧 EMAIL VERIFICATION (DEVELOPMENT)")
        print("=" * 60)
        print(f"To: {email}")
        print(f"Subject: Verify your ClashArena account")
        print("-" * 60)
        print(f"Hi {username},")
        print()
        print("Welcome to ClashArena! Please verify your email address")
        print("by entering the following OTP code:")
        print()
        print(f"🔑 Your OTP Code: {otp_code}")
        print()
        print("This code will expire in 10 minutes.")
        print("If you didn't create an account, please ignore this email.")
        print()
        print("Best regards,")
        print("ClashArena Team")
        print("=" * 60)
        
        # In production, replace this with actual email sending:
        # return send_smtp_email(email, otp_code, username)
        
        return True
        
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def send_smtp_email(email: str, otp_code: str, username: str) -> bool:
    """Send email via SMTP (production version)"""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_USERNAME
        msg['To'] = email
        msg['Subject'] = "Verify your ClashArena account"
        
        # Email body
        body = f"""
        <html>
        <body>
            <h2>Welcome to ClashArena!</h2>
            <p>Hi {username},</p>
            <p>Please verify your email address by entering the following OTP code:</p>
            <h1 style="color: #F5AD27; font-size: 32px; text-align: center;">{otp_code}</h1>
            <p>This code will expire in 10 minutes.</p>
            <p>If you didn't create an account, please ignore this email.</p>
            <br>
            <p>Best regards,<br>ClashArena Team</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(settings.SMTP_USERNAME, email, text)
        server.quit()
        
        return True
        
    except Exception as e:
        print(f"SMTP email failed: {e}")
        return False


def send_sendgrid_email(email: str, otp_code: str, username: str) -> bool:
    """Send email via SendGrid API (recommended for production)"""
    try:
        if not SENDGRID_AVAILABLE or not settings.SENDGRID_API_KEY:
            print("SendGrid not available, falling back to console output")
            return send_verification_email(email, otp_code, username)
        
        # Create SendGrid client
        sg = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        
        # Create email message
        message = Mail(
            from_email=(settings.FROM_EMAIL, settings.FROM_NAME),
            to_emails=email,
            subject='Verify your ClashArena account',
            html_content=f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #F5AD27, #C48612); padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
                    <h1 style="color: white; margin: 0;">ClashArena</h1>
                    <p style="color: white; margin: 10px 0 0 0;">Gaming Platform</p>
                </div>
                
                <h2 style="color: #333;">Welcome to ClashArena!</h2>
                <p>Hi {username},</p>
                <p>Please verify your email address by entering the following OTP code:</p>
                
                <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
                    <h1 style="color: #F5AD27; font-size: 32px; margin: 0; letter-spacing: 5px;">{otp_code}</h1>
                </div>
                
                <p style="color: #666; font-size: 14px;">This code will expire in 10 minutes.</p>
                <p style="color: #666; font-size: 14px;">If you didn't create an account, please ignore this email.</p>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                    <p style="color: #999; font-size: 12px;">Best regards,<br>ClashArena Team</p>
                </div>
            </body>
            </html>
            """
        )
        
        # Send email
        response = sg.send(message)
        
        if response.status_code == 202:
            print(f"✅ Email sent successfully to {email}")
            return True
        else:
            print(f"❌ SendGrid error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ SendGrid email failed: {e}")
        # Fallback to console output
        return send_verification_email(email, otp_code, username)


def send_verification_sms(phone_number: str, otp_code: str, username: str) -> bool:
    """Send verification SMS (development version)"""
    try:
        # For development, we'll just log the SMS
        # In production, you'd use Twilio SMS
        
        print("=" * 60)
        print("📱 SMS VERIFICATION (DEVELOPMENT)")
        print("=" * 60)
        print(f"To: {phone_number}")
        print("-" * 60)
        print(f"Hi {username},")
        print()
        print("Welcome to ClashArena! Please verify your phone number")
        print("by entering the following OTP code:")
        print()
        print(f"🔑 Your OTP Code: {otp_code}")
        print()
        print("This code will expire in 10 minutes.")
        print("If you didn't create an account, please ignore this SMS.")
        print()
        print("Best regards,")
        print("ClashArena Team")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"Failed to send SMS: {e}")
        return False


def send_twilio_sms(phone_number: str, otp_code: str, username: str) -> bool:
    """Send SMS via Twilio (production version)"""
    try:
        if not TWILIO_AVAILABLE or not settings.TWILIO_ACCOUNT_SID:
            print("Twilio not available, falling back to console output")
            return send_verification_sms(phone_number, otp_code, username)
        
        # Create Twilio client
        client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        # SMS message
        message_body = f"""ClashArena Verification

Hi {username},

Your verification code is: {otp_code}

This code expires in 10 minutes.

If you didn't create an account, please ignore this message.

- ClashArena Team"""
        
        # Send SMS
        message = client.messages.create(
            body=message_body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        
        print(f"✅ SMS sent successfully to {phone_number} - SID: {message.sid}")
        return True
        
    except Exception as e:
        print(f"❌ Twilio SMS failed: {e}")
        # Fallback to console output
        return send_verification_sms(phone_number, otp_code, username)


@celery_app.task(bind=True)
def resend_otp_task(self, user_id: str, purpose: str = "email_verification"):
    """Resend OTP to user"""
    try:
        # Get database session
        db = next(get_db())
        
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            db.close()
            return {'success': False, 'error': 'User not found'}
        
        # Check if user already has a recent OTP (within 1 minute)
        recent_otp = db.query(OTP).filter(
            OTP.user_id == user_id,
            OTP.purpose == purpose,
            OTP.is_used == False,
            OTP.created_at > datetime.utcnow() - timedelta(minutes=1)
        ).first()
        
        if recent_otp:
            db.close()
            return {'success': False, 'error': 'Please wait 1 minute before requesting another OTP'}
        
        # Generate new OTP
        otp_code = secrets.randbelow(900000) + 100000
        otp_code_str = str(otp_code).zfill(6)
        
        # Set expiry time
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        # Create new OTP record
        otp_record = OTP(
            user_id=user_id,
            email=user.email,
            code=otp_code_str,
            purpose=purpose,
            expires_at=expires_at
        )
        
        db.add(otp_record)
        db.commit()
        
        # Send email
        email_sent = send_verification_email(user.email, otp_code_str, user.username)
        
        db.close()
        
        return {
            'success': True,
            'message': 'OTP resent successfully',
            'expires_in_minutes': 10
        }
        
    except Exception as e:
        db.close()
        return {'success': False, 'error': str(e)}
