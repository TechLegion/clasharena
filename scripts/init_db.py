#!/usr/bin/env python3
"""
Database initialization script for ClashArena
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared.database import init_db, engine
from shared.models import Base
from sqlalchemy import text

def create_database():
    """Create database if it doesn't exist"""
    # Connect to postgres database to create the clasharena database
    postgres_url = os.getenv("DATABASE_URL", "postgresql://clasharena_user:clasharena_password@localhost:5432/clasharena")
    
    # Extract database name from URL
    db_name = postgres_url.split("/")[-1]
    base_url = postgres_url.rsplit("/", 1)[0]
    
    # Connect to postgres database
    from sqlalchemy import create_engine
    postgres_engine = create_engine(base_url + "/postgres")
    
    with postgres_engine.connect() as conn:
        # Check if database exists
        result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"))
        
        if not result.fetchone():
            # Create database
            conn.execute(text(f"CREATE DATABASE {db_name}"))
            print(f"Database '{db_name}' created successfully")
        else:
            print(f"Database '{db_name}' already exists")

def initialize_tables():
    """Initialize all database tables"""
    try:
        print("Initializing database tables...")
        init_db()
        print("Database tables initialized successfully")
        
        # Create indexes for better performance
        with engine.connect() as conn:
            # Create indexes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
                "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);",
                "CREATE INDEX IF NOT EXISTS idx_wallets_user_id ON wallets(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_transactions_wallet_id ON transactions(wallet_id);",
                "CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);",
                "CREATE INDEX IF NOT EXISTS idx_matches_user_id ON matches(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(status);",
                "CREATE INDEX IF NOT EXISTS idx_matches_game_type ON matches(game_type);",
                "CREATE INDEX IF NOT EXISTS idx_referrals_referrer_id ON referrals(referrer_id);",
                "CREATE INDEX IF NOT EXISTS idx_referrals_referral_code ON referrals(referral_code);",
                "CREATE INDEX IF NOT EXISTS idx_admin_logs_admin_id ON admin_logs(admin_id);",
                "CREATE INDEX IF NOT EXISTS idx_admin_logs_created_at ON admin_logs(created_at);"
            ]
            
            for index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                    print(f"Created index: {index_sql.split()[4]}")
                except Exception as e:
                    print(f"Index might already exist: {e}")
            
            conn.commit()
        
        print("Database initialization completed successfully!")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)

def create_sample_data():
    """Create sample data for testing"""
    try:
        from shared.database import SessionLocal
        from shared.models import User, Wallet
        
        db = SessionLocal()
        
        # Check if admin user exists
        admin_user = db.query(User).filter(User.username == "admin").first()
        
        if not admin_user:
            # Create admin user
            admin_user = User(
                email="admin@clasharena.com",
                username="admin",
                full_name="ClashArena Admin",
                password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/Le1P5Qp5T5YJ5J5J5",  # password: admin123
                is_active=True,
                is_admin=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            
            # Create wallet for admin
            admin_wallet = Wallet(
                user_id=admin_user.id,
                balance=10000.0,
                currency="NGN"
            )
            db.add(admin_wallet)
            db.commit()
            
            print("Admin user created successfully")
            print("Admin credentials: username=admin, password=admin123")
        else:
            print("Admin user already exists")
        
        db.close()
        
    except Exception as e:
        print(f"Error creating sample data: {e}")

if __name__ == "__main__":
    print("ClashArena Database Initialization")
    print("==================================")
    
    # Create database
    create_database()
    
    # Initialize tables
    initialize_tables()
    
    # Create sample data
    create_sample_data()
    
    print("\nDatabase initialization completed!")
    print("You can now start the services with: docker-compose up")
