"""
One-off script: set password for a ClashArena user (admin dashboard auth).

This targets the main `backend` app auth flow that uses:
  - `backend/shared/models.py` -> `User.password_hash` (bcrypt)
  - `backend/app/api/v1/auth.py` -> login by `email_or_username`

Usage:
  python set_user_password.py --email techlegion01@gmail.com --password sammyokay
"""

from __future__ import annotations

import argparse
import sys


def main() -> int:
    # `backend/app/core/config.py` prints warning symbols (Unicode). On some
    # Windows terminals this can crash imports with UnicodeEncodeError.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    from app.core.config import settings  # noqa: F401 (import for side effects)
    from app.core.security import get_password_hash
    from shared.database import SessionLocal, init_db
    from shared.models import User

    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True, help="User email to update")
    parser.add_argument("--password", required=True, help="New plaintext password")
    args = parser.parse_args()

    init_db()

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == args.email).first()
        if not user:
            print(f"No user found with email: {args.email}")
            return 1

        new_hash = get_password_hash(args.password)
        user.password_hash = new_hash
        user.is_active = True
        db.commit()

        # Verify the persisted value
        refreshed = db.query(User).filter(User.email == args.email).first()
        ok = refreshed is not None and refreshed.password_hash == new_hash

        print(
            "User password updated successfully:"
            f" email={args.email}, user_id={user.id}, is_admin={user.is_admin}, verified={ok}"
        )
        return 0 if ok else 2
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())

