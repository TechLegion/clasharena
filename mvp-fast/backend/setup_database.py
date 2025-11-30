"""
Script to setup PostgreSQL database for ClashArena MVP
This script creates the database if it doesn't exist and initializes tables
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

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

def create_database():
    """Create database if it doesn't exist"""
    try:
        # Connect to PostgreSQL server (default postgres database)
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database="postgres"  # Connect to default database first
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
            (DB_NAME,)
        )
        exists = cursor.fetchone()
        
        if exists:
            print(f" Database '{DB_NAME}' already exists")
        else:
            # Create database
            cursor.execute(f'CREATE DATABASE {DB_NAME}')
            print(f" Database '{DB_NAME}' created successfully")
        
        cursor.close()
        conn.close()
        
        return True
    except psycopg2.OperationalError as e:
        print(f" Error connecting to PostgreSQL: {e}")
        print(f"   Make sure PostgreSQL is running and credentials are correct")
        print(f"   Host: {DB_HOST}, Port: {DB_PORT}, User: {DB_USER}")
        return False
    except Exception as e:
        print(f" Error creating database: {e}")
        return False

def initialize_tables():
    """Initialize database tables"""
    try:
        from database.db import init_db
        init_db()
        print(" Database tables initialized successfully")
        return True
    except Exception as e:
        print(f" Error initializing tables: {e}")
        return False

def main():
    """Main setup function"""
    print("Setting up ClashArena MVP Database...")
    print(f"Database: {DB_NAME}")
    print(f"Host: {DB_HOST}:{DB_PORT}")
    print(f"User: {DB_USER}")
    print()
    
    # Create database
    if not create_database():
        return
    
    # Initialize tables
    if not initialize_tables():
        return
    
    print()
    print(" Database setup completed successfully!")
    print()
    print("Next steps:")
    print("1. Create an admin user: python create_admin.py")
    print("2. Run the application: python main.py")

if __name__ == "__main__":
    main()

