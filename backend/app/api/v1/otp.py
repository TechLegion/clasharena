"""
OTP (One-Time Password) API endpoints for email verification
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging

from app.api.deps import get_current_user
from app.tasks.otp_tasks import send_otp_email_task, send_otp_sms_task, verify_otp_task, resend_otp_task
from app.core.rate_limiting import safe_rate_limit, general_rate_limit
from shared.models import User

router = APIRouter()
logger = logging.getLogger(__name__)


class SendOTPRequest(BaseModel):
    email: EmailStr
    purpose: str = "email_verification"

class SendSMSOTPRequest(BaseModel):
    phone_number: str
    purpose: str = "phone_verification"


class VerifyOTPRequest(BaseModel):
    otp_code: str
    purpose: str = "email_verification"


class TaskResponse(BaseModel):
    task_id: str
    status: str


@router.post("/send/email", response_model=TaskResponse)
@safe_rate_limit(general_rate_limit)
async def send_otp_email(
    otp_request: SendOTPRequest,
    current_user: User = Depends(get_current_user)
):
    """Send OTP to user's email"""
    
    # Validate purpose
    valid_purposes = ["email_verification", "password_reset", "two_factor"]
    if otp_request.purpose not in valid_purposes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid purpose. Must be one of: email_verification, password_reset, two_factor"
        )
    
    # Check if user is already verified for email verification
    if otp_request.purpose == "email_verification" and current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified"
        )
    
    # Send OTP task
    task = send_otp_email_task.delay(
        current_user.id,
        otp_request.email,
        otp_request.purpose
    )
    
    return TaskResponse(task_id=task.id, status="queued")


@router.post("/send/sms", response_model=TaskResponse)
@safe_rate_limit(general_rate_limit)
async def send_otp_sms(
    sms_request: SendSMSOTPRequest,
    current_user: User = Depends(get_current_user)
):
    """Send OTP to user's phone number"""
    
    # Validate purpose
    valid_purposes = ["phone_verification", "password_reset", "two_factor"]
    if sms_request.purpose not in valid_purposes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid purpose. Must be one of: phone_verification, password_reset, two_factor"
        )
    
    # Basic phone number validation (should start with + and be at least 10 digits)
    if not sms_request.phone_number.startswith('+') or len(sms_request.phone_number) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number format. Must start with + and be at least 10 digits"
        )
    
    # Send SMS OTP task
    task = send_otp_sms_task.delay(
        current_user.id,
        sms_request.phone_number,
        sms_request.purpose
    )
    
    return TaskResponse(task_id=task.id, status="queued")


@router.post("/verify", response_model=TaskResponse)
@safe_rate_limit(general_rate_limit)
async def verify_otp(
    verify_request: VerifyOTPRequest,
    current_user: User = Depends(get_current_user)
):
    """Verify OTP code"""
    
    # Validate OTP code format (6 digits)
    if not verify_request.otp_code.isdigit() or len(verify_request.otp_code) != 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP must be a 6-digit number"
        )
    
    # Verify OTP task
    task = verify_otp_task.delay(
        current_user.id,
        verify_request.otp_code,
        verify_request.purpose
    )
    
    return TaskResponse(task_id=task.id, status="queued")


@router.post("/resend", response_model=TaskResponse)
@safe_rate_limit(general_rate_limit)
async def resend_otp(
    purpose: str = "email_verification",
    current_user: User = Depends(get_current_user)
):
    """Resend OTP to user"""
    
    # Validate purpose
    valid_purposes = ["email_verification", "password_reset", "two_factor"]
    if purpose not in valid_purposes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid purpose. Must be one of: email_verification, password_reset, two_factor"
        )
    
    # Resend OTP task
    task = resend_otp_task.delay(current_user.id, purpose)
    
    return TaskResponse(task_id=task.id, status="queued")


@router.get("/status")
async def get_otp_status(current_user: User = Depends(get_current_user)):
    """Get user's OTP verification status"""
    return {
        "email_verified": current_user.email_verified,
        "email": current_user.email,
        "can_resend_otp": True  # Could add logic to check recent OTP requests
    }
