from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey, Numeric
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import uuid

Base = declarative_base()

class Entry(Base):
    """Player entry after payment"""
    __tablename__ = "entries"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    payment_reference = Column(String, unique=True, nullable=False, index=True)
    payment_status = Column(String, default="pending")  # pending, completed, failed
    codm_id = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    region = Column(String, nullable=True)
    bank_name = Column(String, nullable=True)
    account_number = Column(String, nullable=True)
    account_name = Column(String, nullable=True)
    entry_fee = Column(Numeric(10, 2), default=100.00)  # 100 NGN for testing
    is_winner = Column(Boolean, default=False)
    payout_status = Column(String, default="pending")  # pending, processing, completed, failed
    payout_reference = Column(String, nullable=True)
    whatsapp_notified = Column(Boolean, default=False)
    email_notified = Column(Boolean, default=False)
    sms_notified = Column(Boolean, default=False)
    match_time_notified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    payment = relationship("Payment", back_populates="entry", uselist=False)
    payouts = relationship("Payout", back_populates="entry")

class Payment(Base):
    """Payment transaction details"""
    __tablename__ = "payments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    entry_id = Column(String, ForeignKey("entries.id"), nullable=False)
    reference = Column(String, unique=True, nullable=False, index=True)
    gateway = Column(String, nullable=False)  # paystack, flutterwave
    gateway_reference = Column(String, nullable=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="NGN")
    status = Column(String, default="pending")  # pending, success, failed
    gateway_response = Column(Text)  # JSON response from gateway
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    entry = relationship("Entry", back_populates="payment")

class Payout(Base):
    """Payout transaction to winners"""
    __tablename__ = "payouts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    entry_id = Column(String, ForeignKey("entries.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="NGN")
    status = Column(String, default="pending")  # pending, processing, completed, failed
    gateway = Column(String, nullable=True)  # paystack, flutterwave, bank_transfer
    gateway_reference = Column(String, nullable=True)
    failure_reason = Column(Text, nullable=True)
    processed_by = Column(String, nullable=True)  # admin user id
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    entry = relationship("Entry", back_populates="payouts")

class AdminUser(Base):
    """Admin users for managing entries and payouts"""
    __tablename__ = "admin_users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Notification(Base):
    """Notification log"""
    __tablename__ = "notifications"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    entry_id = Column(String, ForeignKey("entries.id"), nullable=True)
    notification_type = Column(String, nullable=False)  # email, whatsapp, sms
    recipient = Column(String, nullable=False)
    subject = Column(String, nullable=True)
    message = Column(Text, nullable=False)
    status = Column(String, default="pending")  # pending, sent, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)

class AppSettings(Base):
    """Application settings"""
    __tablename__ = "app_settings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String, unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    description = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)  # admin user id
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class RegistrationMilestone(Base):
    """Track registration milestones (e.g., 100 users)"""
    __tablename__ = "registration_milestones"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    milestone_count = Column(Integer, nullable=False)  # e.g., 100, 200, 500
    reached_at = Column(DateTime, default=datetime.utcnow)
    notified = Column(Boolean, default=False)
    notification_sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

