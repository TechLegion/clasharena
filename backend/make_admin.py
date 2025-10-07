#!/usr/bin/env python3
"""
Make User Admin Script
Promote a user to admin by email
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from shared.models import User
from datetime import datetime

def make_user_admin(email: str):
    """Make a user admin by email"""
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
        
        # Check if already admin
        if user.is_admin:
            print(f"✅ User '{user.username}' ({email}) is already an admin!")
            return True
        
        # Promote to admin
        user.is_admin = True
        user.updated_at = datetime.now()
        
        db.commit()
        db.refresh(user)
        db.close()
        
        print(f"🎉 Successfully promoted '{user.username}' ({email}) to admin!")
        print(f"   Username: {user.username}")
        print(f"   Full Name: {user.full_name}")
        print(f"   Email: {user.email}")
        print(f"   Admin Status: ✅ Active")
        
        return True
        
    except Exception as e:
        print(f"❌ Error promoting user to admin: {str(e)}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False

def main():
    print("🔧 ClashArena Admin Promotion Script")
    print("=" * 40)
    
    # Target email
    target_email = "techlegion01@gmail.com"
    
    print(f"🎯 Promoting user: {target_email}")
    print()
    
    # Make user admin
    success = make_user_admin(target_email)
    
    if success:
        print()
        print("✅ Admin promotion completed successfully!")
        print("🚀 The user can now access the admin panel at /admin")
    else:
        print()
        print("❌ Admin promotion failed!")
        print("💡 Make sure:")
        print("   - The email exists in the database")
        print("   - The database is running")
        print("   - The DATABASE_URL is correct in your .env file")

if __name__ == "__main__":
    main()
