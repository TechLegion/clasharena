"""
Migration: Add kill_count column to entries table if it doesn't exist.
Run this once after pulling the new workflow features.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from sqlalchemy import text
from database.db import engine

def migrate():
    # Add kill_count
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE entries ADD COLUMN kill_count INTEGER DEFAULT 0"))
            conn.commit()
        print("Added kill_count column")
    except Exception as e:
        if "already exists" in str(e).lower():
            print("kill_count already exists")
        else:
            raise
    # Add excluded
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE entries ADD COLUMN excluded BOOLEAN DEFAULT FALSE"))
            conn.commit()
        print("Added excluded column")
    except Exception as e:
        if "already exists" in str(e).lower():
            print("excluded already exists")
        else:
            raise
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
