#!/usr/bin/env python3
"""
Create Admin User Script
Create a new admin user with specified credentials
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.security import get_password_hash
from shared.models import User
from datetime import datetime

def create_admin_user(username: str, password: str, email: str, full_name: str = None):
    """Create a new admin user"""
    try:
        # Create database connection
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == email) | (User.username == username)
        ).first()
        
        if existing_user:
            print(f"❌ User already exists!")
            print(f"   Email: {existing_user.email}")
            print(f"   Username: {existing_user.username}")
            return False
        
        # Hash password
        hashed_password = get_password_hash(password)
        
        # Create new admin user
        new_user = User(
            email=email,
            username=username,
            full_name=full_name or username.title(),
            password_hash=hashed_password,
            is_active=True,
            is_admin=True  # Make them admin
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        db.close()
        
        print(f"🎉 Successfully created admin user!")
        print(f"   Username: {new_user.username}")
        print(f"   Email: {new_user.email}")
        print(f"   Full Name: {new_user.full_name}")
        print(f"   Password: {password}")
        print(f"   Admin Status: ✅ Active")
        print(f"   User ID: {new_user.id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin user: {str(e)}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False

def main():
    print("🔧 ClashArena Admin User Creation Script")
    print("=" * 45)
    
    # Admin user details
    username = "testadmin"
    password = "sammyokay"
    email = "testadmin@clasharena.com"
    full_name = "Test Admin"
    
    print(f"🎯 Creating admin user:")
    print(f"   Username: {username}")
    print(f"   Password: {password}")
    print(f"   Email: {email}")
    print(f"   Full Name: {full_name}")
    print()
    
    # Create admin user
    success = create_admin_user(username, password, email, full_name)
    
    if success:
        print()
        print("✅ Admin user created successfully!")
        print("🚀 Login credentials:")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        print("📱 Access admin panel at: /admin")
    else:
        print()
        print("❌ Admin user creation failed!")
        print("💡 Make sure:")
        print("   - The database is running")
        print("   - The DATABASE_URL is correct in your .env file")
        print("   - The username/email doesn't already exist")

if __name__ == "__main__":
    main()
