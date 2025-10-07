#!/usr/bin/env python3
"""
Check Admin User Script
Verify if a user is an admin in the database
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from shared.models import User

def check_admin_user(email: str):
    """Check if a user is admin"""
    try:
        # Create database connection
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"❌ User with email '{email}' not found!")
            return False
        
        print(f"📋 User Details:")
        print(f"   ID: {user.id}")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Full Name: {user.full_name}")
        print(f"   Is Active: {user.is_active}")
        print(f"   Is Admin: {user.is_admin}")
        print(f"   Created: {user.created_at}")
        print(f"   Updated: {user.updated_at}")
        
        db.close()
        return user.is_admin
        
    except Exception as e:
        print(f"❌ Error checking user: {str(e)}")
        if 'db' in locals():
            db.close()
        return False

def main():
    print("🔍 ClashArena Admin Check Script")
    print("=" * 35)
    
    # Check both users
    emails = [
        "techlegion01@gmail.com",
        "testadmin@clasharena.com"
    ]
    
    for email in emails:
        print(f"\n🎯 Checking: {email}")
        print("-" * 40)
        is_admin = check_admin_user(email)
        print(f"Admin Status: {'✅ YES' if is_admin else '❌ NO'}")

if __name__ == "__main__":
    main()
