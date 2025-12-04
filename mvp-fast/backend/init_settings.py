"""
Initialize app settings in the database
Run this script after database migration to set up default settings
"""

import sys
from pathlib import Path

# Add parent directory to path
backend_dir = Path(__file__).parent
root_dir = backend_dir.parent.resolve()
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from database.db import get_db, init_db
from database.models import AppSettings
import os

def init_app_settings():
    """Initialize app settings in the database"""
    db = next(get_db())
    
    try:
        # Initialize WhatsApp link setting
        whatsapp_link = os.getenv("WHATSAPP_GROUP_LINK", "https://chat.whatsapp.com/your-group-link")
        
        existing_setting = db.query(AppSettings).filter(AppSettings.key == "whatsapp_group_link").first()
        
        if not existing_setting:
            setting = AppSettings(
                key="whatsapp_group_link",
                value=whatsapp_link,
                description="WhatsApp group link for tournament participants"
            )
            db.add(setting)
            db.commit()
            print(f"✓ Initialized WhatsApp link setting: {whatsapp_link}")
        else:
            print(f"✓ WhatsApp link setting already exists: {existing_setting.value}")
        
        print("✓ App settings initialized successfully!")
        
    except Exception as e:
        print(f"✗ Error initializing settings: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Initializing app settings...")
    init_app_settings()
    print("Done!")

