"""
Idempotently ensure the MVP-Fast admin account exists.

This targets the `/admin/login` dashboard which authenticates against
`mvp-fast/database/models.py:AdminUser` (bcrypt `password_hash`).
"""

from __future__ import annotations

import os
import sys
import argparse
from pathlib import Path

from dotenv import load_dotenv

_env = Path(__file__).resolve().parent.parent / ".env"
if _env.exists():
    load_dotenv(_env)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", default="techlegion01@gmail.com")
    parser.add_argument("--username", default="techlegin")
    parser.add_argument("--password", default="sammyokay")
    args = parser.parse_args()

    # Ensure `from database...` works when run from different CWDs.
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from database.db import SessionLocal, init_db
    from database.models import AdminUser
    from database.passwords import hash_password

    init_db()
    db = SessionLocal()
    try:
        new_hash = hash_password(args.password)

        existing_by_email = db.query(AdminUser).filter(AdminUser.email == args.email).first()
        existing_by_username = db.query(AdminUser).filter(AdminUser.username == args.username).first()

        updated = False

        # Ensure the username we want exists with the right password.
        if existing_by_username:
            existing_by_username.password_hash = new_hash
            existing_by_username.is_active = True
            if not existing_by_username.email:
                existing_by_username.email = args.email
            updated = True
            target_user = existing_by_username
        else:
            # If email exists under a different username, we can't change username/email safely
            # due to unique constraints; instead create the requested username record.
            target_user = AdminUser(
                username=args.username,
                email=args.email,
                password_hash=new_hash,
                is_active=True,
            )
            db.add(target_user)
            db.commit()
            db.refresh(target_user)
            updated = True

        # If email existed as a separate row, align its password too (optional but harmless).
        if existing_by_email and existing_by_email.id != target_user.id:
            existing_by_email.password_hash = new_hash
            existing_by_email.is_active = True
            updated = True

        if updated and not existing_by_username:
            # Already committed in creation path.
            pass
        elif updated:
            db.commit()

        print(
            "Admin ensure result:"
            f" username={target_user.username}"
            f" email={target_user.email}"
            f" id={target_user.id}"
        )
        return 0
    except Exception as e:
        print(f"Failed to ensure admin user: {e}")
        db.rollback()
        return 2
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())

