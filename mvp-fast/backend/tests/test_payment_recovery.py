"""
Regression: paid users who never reached /intake must recover via the same email
(pending row + Paystack success) without creating a new checkout.
"""
from __future__ import annotations

import sys
import uuid
from decimal import Decimal
from unittest.mock import patch

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

# conftest must run first (import order: conftest, then this module)
from pathlib import Path

_MVP = Path(__file__).resolve().parents[2]
if str(_MVP) not in sys.path:
    sys.path.insert(0, str(_MVP))

# Import app after conftest has set DATABASE_URL
import main  # noqa: E402
from database.db import SessionLocal, engine  # noqa: E402
from database.models import Base, Entry, Payment  # noqa: E402


def _reset_schema() -> None:
    """Fresh tables for an isolated test (SQLite)."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        for stmt in (
            "ALTER TABLE entries ADD COLUMN IF NOT EXISTS kill_count INTEGER DEFAULT 0",
            "ALTER TABLE entries ADD COLUMN IF NOT EXISTS excluded BOOLEAN DEFAULT FALSE",
            "ALTER TABLE entries ADD COLUMN IF NOT EXISTS lobby_group INTEGER",
            "ALTER TABLE entries ADD COLUMN IF NOT EXISTS lobby_epoch INTEGER DEFAULT 0",
            "UPDATE entries SET lobby_epoch = 0 WHERE lobby_epoch IS NULL",
            "ALTER TABLE entries ADD COLUMN IF NOT EXISTS payment_completed_epoch INTEGER",
        ):
            try:
                conn.execute(text(stmt))
            except Exception:
                pass
        conn.commit()


def test_normalize_registration_email() -> None:
    assert main._normalize_registration_email("  User@EXAMPLE.com  ") == "user@example.com"
    assert main._normalize_registration_email("") == ""


@patch.object(main, "verify_paystack_payment", return_value={"verified": True, "gateway_response": "{}"})
def test_recover_syncs_pending_to_completed_when_gateway_says_paid(_mock_verify: object) -> None:
    _reset_schema()
    ref = f"CLASH_{uuid.uuid4().hex[:16].upper()}"
    eid = str(uuid.uuid4())
    db = SessionLocal()
    try:
        entry = Entry(
            id=eid,
            payment_reference=ref,
            payment_status="pending",
            contact_email="player@example.com",
            entry_fee=Decimal("100.00"),
        )
        pay = Payment(
            id=str(uuid.uuid4()),
            entry_id=eid,
            reference=ref,
            gateway="paystack",
            amount=Decimal("100.00"),
            currency="NGN",
            status="pending",
        )
        db.add(entry)
        db.add(pay)
        db.commit()
    finally:
        db.close()

    db2 = SessionLocal()
    try:
        out = main.recover_paid_intake_for_email(db2, "player@example.com")
        assert out is not None
        assert out.payment_reference == ref
        assert out.payment_status == "completed"
    finally:
        db2.close()

    db3 = SessionLocal()
    try:
        p = db3.query(Payment).filter(Payment.reference == ref).one()
        assert p.status == "success"
    finally:
        db3.close()


def test_recover_returns_completed_intake_same_lobby_epoch() -> None:
    _reset_schema()
    ref = f"CLASH_{uuid.uuid4().hex[:16].upper()}"
    eid = str(uuid.uuid4())
    db = SessionLocal()
    try:
        entry = Entry(
            id=eid,
            payment_reference=ref,
            payment_status="completed",
            contact_email="donepay@example.com",
            entry_fee=Decimal("100.00"),
            payment_completed_epoch=0,
        )
        db.add(entry)
        db.commit()
    finally:
        db.close()

    db2 = SessionLocal()
    try:
        out = main.recover_paid_intake_for_email(db2, "donepay@example.com")
        assert out is not None
        assert out.payment_reference == ref
    finally:
        db2.close()
