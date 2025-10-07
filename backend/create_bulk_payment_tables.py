#!/usr/bin/env python3
"""
Create bulk payment tables in the database
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import engine
from shared.models import Base, BulkPayment, BulkPaymentRecipient

def create_bulk_payment_tables():
    """Create bulk payment tables"""
    try:
        print("Creating bulk payment tables...")
        
        # Create tables
        Base.metadata.create_all(bind=engine, tables=[
            BulkPayment.__table__,
            BulkPaymentRecipient.__table__
        ])
        
        print("✅ Bulk payment tables created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating bulk payment tables: {e}")
        return False
    
    return True

if __name__ == "__main__":
    create_bulk_payment_tables()
