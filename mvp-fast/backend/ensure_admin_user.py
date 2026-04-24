"""
Idempotently ensure the MVP-Fast admin account exists.

This targets the `/admin/login` dashboard which authenticates against
`mvp-fast/database/models.py:AdminUser` (bcrypt `password_hash`).

Exit code is always 0 on completion so a deploy start command
(`ensure_admin_user && gunicorn`) never blocks the web server if the DB
is unavailable or a row already exists in an unexpected shape.
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

    try:
        init_db()
    except Exception as e:
        print(
            f"ensure_admin_user: init_db failed (web server will still try to start): {e}",
            file=sys.stderr,
        )
        return 0

    db = SessionLocal()
    try:
        new_hash = hash_password(args.password)

        existing_by_email = db.query(AdminUser).filter(AdminUser.email == args.email).first()
        existing_by_username = (
            db.query(AdminUser).filter(AdminUser.username == args.username).first()
        )

        if existing_by_username:
            u = existing_by_username
            u.password_hash = new_hash
            u.is_active = True
            if not u.email:
                u.email = args.email
            db.commit()
            target_user = u
        elif existing_by_email:
            # Do not create a second row: email is unique; sync password for that account.
            u = existing_by_email
            u.password_hash = new_hash
            u.is_active = True
            db.commit()
            target_user = u
        else:
            u = AdminUser(
                username=args.username,
                email=args.email,
                password_hash=new_hash,
                is_active=True,
            )
            db.add(u)
            db.commit()
            db.refresh(u)
            target_user = u

        print(
            "Admin ensure result:"
            f" username={target_user.username}"
            f" email={target_user.email}"
            f" id={target_user.id}"
        )
        return 0
    except Exception as e:
        print(
            f"Failed to ensure admin user (not blocking server start): {e}",
            file=sys.stderr,
        )
        try:
            db.rollback()
        except Exception:
            pass
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
