"""
One-off script: set an MVP Fast admin password.

This targets `mvp-fast/database/models.py`'s `AdminUser` table used by
`mvp-fast/backend/main.py` for `/admin/login` authentication.

Usage:
  python set_admin_password.py --identifier techlegion01@gmail.com --password sammyokay
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def hash_password(password: str) -> str:
    """Hash using the same scheme as `mvp-fast/backend/main.py`."""
    return hashlib.sha256(password.encode()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--identifier",
        required=True,
        help="Admin username and/or email to update (e.g. techlegion01@gmail.com)",
    )
    parser.add_argument("--password", required=True, help="New plaintext password")
    args = parser.parse_args()

    # Ensure imports like `from database.db import ...` work
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Load mvp-fast env vars (DB_URL, etc.)
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    from database.db import SessionLocal, init_db
    from database.models import AdminUser

    init_db()

    db = SessionLocal()
    try:
        target = args.identifier
        new_password_hash = hash_password(args.password)

        matching_admins = db.query(AdminUser).filter(
            (AdminUser.email == target) | (AdminUser.username == target)
        ).all()

        if not matching_admins:
            # If there's no admin yet, create one so the dashboard can be accessed.
            admin = AdminUser(
                username=target,
                email=target,
                password_hash=new_password_hash,
                is_active=True,
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            print(
                "Created admin user (no existing match):"
                f" id={admin.id} username={admin.username} email={admin.email}"
            )
            return 0

        for admin in matching_admins:
            admin.password_hash = new_password_hash
            admin.is_active = True

        db.commit()

        # Verify the update actually stuck
        updated_admins = db.query(AdminUser).filter(
            (AdminUser.email == target) | (AdminUser.username == target)
        ).all()

        updated_ok = [
            a
            for a in updated_admins
            if a.password_hash == new_password_hash and a.is_active
        ]

        print(
            "Updated admin password successfully:"
            f" target={target}, updated_count={len(updated_ok)}/{len(updated_admins)}"
        )
        for a in updated_ok:
            print(f" - id={a.id} username={a.username} email={a.email}")

        return 0 if updated_ok else 2
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())

