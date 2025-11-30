"""
Script to create an admin user for the MVP
Usage: python create_admin.py
"""
import sys
import os
from getpass import getpass

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import SessionLocal, init_db
from database.models import AdminUser
import hashlib

def hash_password(password: str) -> str:
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_admin():
    """Create an admin user"""
    init_db()
    db = SessionLocal()
    
    try:
        username = input("Enter admin username: ").strip()
        if not username:
            print("Username cannot be empty!")
            return
        
        # Check if username already exists
        existing = db.query(AdminUser).filter(AdminUser.username == username).first()
        if existing:
            print(f"Username '{username}' already exists!")
            return
        
        email = input("Enter admin email (optional): ").strip() or None
        
        password = getpass("Enter admin password: ")
        if len(password) < 6:
            print("Password must be at least 6 characters!")
            return
        
        password_confirm = getpass("Confirm password: ")
        if password != password_confirm:
            print("Passwords do not match!")
            return
        
        # Create admin user
        admin = AdminUser(
            username=username,
            password_hash=hash_password(password),
            email=email,
            is_active=True
        )
        
        db.add(admin)
        db.commit()
        
        print(f"\n✅ Admin user '{username}' created successfully!")
        print(f"   Email: {email or 'Not provided'}")
        
    except Exception as e:
        print(f"❌ Error creating admin: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()

