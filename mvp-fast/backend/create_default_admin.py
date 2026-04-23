"""
Quick script to create a default admin user
Usage: python create_default_admin.py
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import SessionLocal, init_db
from database.models import AdminUser
from database.passwords import hash_password

def create_default_admin():
    """Create a default admin user"""
    init_db()
    db = SessionLocal()
    
    try:
        # Default admin credentials
        username = "admin"
        password = "admin123"  # Change this in production!
        email = "admin@clasharena.com"
        
        # Check if admin already exists
        existing = db.query(AdminUser).filter(AdminUser.username == username).first()
        if existing:
            print(f"Admin user '{username}' already exists!")
            print("To create a new admin, use: python create_admin.py")
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
        
        print(f"\n✅ Default admin user created successfully!")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        print(f"   Email: {email}")
        print(f"\n⚠️  WARNING: Change the default password in production!")
        
    except Exception as e:
        print(f"❌ Error creating admin: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_default_admin()

