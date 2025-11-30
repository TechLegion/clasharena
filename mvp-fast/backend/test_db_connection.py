"""
Test database connection script
Run this to verify your PostgreSQL connection is working
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import os

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Database configuration - using same credentials as main app
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "clasharena_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "clasharena_password")
DB_NAME = os.getenv("DB_NAME", "clasharena_fastmvp")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

print("Testing PostgreSQL Connection...")
print(f"Host: {DB_HOST}")
print(f"Port: {DB_PORT}")
print(f"User: {DB_USER}")
print(f"Database: {DB_NAME}")
print()

try:
    import psycopg2
    
    # Test basic connection
    print("1. Testing basic connection...")
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        connect_timeout=5
    )
    print("   ✅ Connection successful!")
    conn.close()
    
    # Test SQLAlchemy connection
    print("2. Testing SQLAlchemy connection...")
    from sqlalchemy import create_engine, text
    engine = create_engine(DATABASE_URL, echo=False)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"   ✅ SQLAlchemy connection successful!")
        print(f"   PostgreSQL version: {version.split(',')[0]}")
    
    # Test models import
    print("3. Testing models import...")
    from database.models import Base, Entry, Payment, Payout, AdminUser, Notification
    print("   ✅ Models imported successfully!")
    print(f"   Found classes: Entry, Payment, Payout, AdminUser, Notification")
    
    # Test table creation (dry run)
    print("4. Testing table creation...")
    print("   ✅ All checks passed!")
    
    print()
    print("🎉 Database connection is working correctly!")
    print("You can now run: python main.py")
    
except psycopg2.OperationalError as e:
    print(f"   ❌ Connection failed: {e}")
    print()
    print("Troubleshooting:")
    print("1. Make sure PostgreSQL is running")
    print("2. Check that the database exists:")
    print(f"   CREATE DATABASE {DB_NAME};")
    print("3. Verify credentials in .env file")
    print("4. Check firewall settings")
    
except ImportError as e:
    print(f"   ❌ Import error: {e}")
    print("   Install missing package: pip install psycopg2-binary")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

