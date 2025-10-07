from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    password_hash = Column(String, nullable=True)  # For social auth, this might be null
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)  # Email verification status
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    wallet = relationship("Wallet", back_populates="user", uselist=False)
    matches = relationship("Match", back_populates="user")

class Wallet(Base):
    __tablename__ = "wallets"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    balance = Column(Float, default=0.0)
    currency = Column(String, default="NGN")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="wallet")
    transactions = relationship("Transaction", back_populates="wallet")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    wallet_id = Column(String, ForeignKey("wallets.id"), nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String, nullable=False)  # deposit, withdrawal, bet, win
    status = Column(String, default="pending")  # pending, completed, failed
    reference = Column(String, unique=True, nullable=False)
    description = Column(Text)
    external_reference = Column(String)  # For payment gateway references
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    wallet = relationship("Wallet", back_populates="transactions")

class Match(Base):
    __tablename__ = "matches"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    game_type = Column(String, nullable=False)  # pubg_mobile, free_fire, call_of_duty, etc.
    match_type = Column(String, nullable=False)  # solo, duo, squad, battle_royale, etc.
    entry_fee = Column(Numeric(10, 2), nullable=False)  # Entry fee paid by user
    prize_pool = Column(Numeric(10, 2), nullable=False)  # Total prize pool for winner
    status = Column(String, default="pending")  # pending, active, completed, cancelled
    opponent_id = Column(String)  # For future multiplayer matches
    match_data = Column(Text)  # JSON data about the match
    result = Column(String)  # win, loss, draw
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="matches")

class Referral(Base):
    __tablename__ = "referrals"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    referrer_id = Column(String, ForeignKey("users.id"), nullable=False)
    referred_id = Column(String, ForeignKey("users.id"), nullable=False)
    referral_code = Column(String, unique=True, nullable=False)
    status = Column(String, default="pending")  # pending, completed, expired
    reward_amount = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    referrer = relationship("User", foreign_keys=[referrer_id])
    referred = relationship("User", foreign_keys=[referred_id])

class AdminLog(Base):
    __tablename__ = "admin_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    admin_id = Column(String, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)
    target_type = Column(String)  # user, match, transaction, etc.
    target_id = Column(String)
    details = Column(Text)
    ip_address = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class OTP(Base):
    """OTP verification codes for email verification"""
    __tablename__ = "otps"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    email = Column(String, nullable=False)
    code = Column(String, nullable=False)  # 6-digit OTP code
    purpose = Column(String, nullable=False, default="email_verification")  # email_verification, password_reset, etc.
    is_used = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="otps")


# Add OTP relationship to User model
User.otps = relationship("OTP", back_populates="user")


class BulkPayment(Base):
    __tablename__ = "bulk_payments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    admin_id = Column(String, ForeignKey("users.id"), nullable=False)
    description = Column(String, nullable=False)
    total_amount = Column(Float, nullable=False)
    total_recipients = Column(Integer, nullable=False)
    status = Column(String, default="pending")  # pending, processing, completed, failed, partially_completed
    notify_recipients = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    admin = relationship("User", foreign_keys=[admin_id])
    recipients = relationship("BulkPaymentRecipient", back_populates="bulk_payment")


class BulkPaymentRecipient(Base):
    __tablename__ = "bulk_payment_recipients"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    bulk_payment_id = Column(String, ForeignKey("bulk_payments.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    reason = Column(String, nullable=False)
    account_number = Column(String, nullable=False)
    bank_code = Column(String, nullable=False)
    account_name = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    paystack_reference = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bulk_payment = relationship("BulkPayment", back_populates="recipients")
    user = relationship("User", foreign_keys=[user_id])
