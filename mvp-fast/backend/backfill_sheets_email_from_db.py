"""
Backfill column D (Email) in a Google Sheet tab from `entries.contact_email`.

Rows are found the same way as the app: match column B (IGN), C (phone), or D (email).
Use this when the sheet had empty Email cells but the database already has emails.

Run from repo: mvp-fast/

  .\\.venv\\Scripts\\python backend/backfill_sheets_email_from_db.py --dry-run
  .\\.venv\\Scripts\\python backend/backfill_sheets_email_from_db.py --tab \"Lobby 1\"

If --tab is omitted, the current admin registration lobby name is read from AppSettings
(same default as the live app for `target_sheet`).

Requires: GOOGLE_SHEETS_ENABLED=true, GOOGLE_SPREADSHEET_ID, and credentials
(same as the running backend).
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

backend_dir = Path(__file__).parent
root_dir = backend_dir.parent.resolve()
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from sqlalchemy.orm import Session

from database.db import engine
from database.models import AppSettings, Entry

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

REGISTRATION_LOBBY_NAME_KEY = "registration_lobby_name"


def _get_registration_lobby_name(db: Session) -> str:
    s = db.query(AppSettings).filter(AppSettings.key == REGISTRATION_LOBBY_NAME_KEY).first()
    if not s or not (s.value or "").strip():
        return ""
    return s.value.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill Google Sheet column D (Email) from the database")
    parser.add_argument(
        "--tab",
        type=str,
        default="",
        help="Sheet tab name. If empty, use registration_lobby_name from AppSettings (same as app default).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List actions only; do not call Google Sheets",
    )
    args = parser.parse_args()

    try:
        from google_sheets import (
            SPREADSHEET_ID,
            ensure_header_row,
            get_sheets_service,
            update_entry_in_sheets,
        )
    except ImportError as e:
        logger.error("google_sheets not available: %s", e)
        return 1

    if os.getenv("GOOGLE_SHEETS_ENABLED", "false").lower() != "true":
        logger.error("Set GOOGLE_SHEETS_ENABLED=true in .env")
        return 1
    if not (SPREADSHEET_ID or "").strip():
        logger.error("GOOGLE_SPREADSHEET_ID is not set")
        return 1
    if not get_sheets_service():
        logger.error("Google Sheets service could not be initialized (credentials missing or invalid)")
        return 1

    with Session(engine) as db:
        target_tab = (args.tab or "").strip() or _get_registration_lobby_name(db)
        if not target_tab:
            logger.error("No tab: pass --tab \"Your Tab Name\" or set registration lobby name in admin settings")
            return 1

        if not args.dry_run:
            if not ensure_header_row(SPREADSHEET_ID, target_tab):
                logger.error("Failed to ensure header row on tab %r", target_tab)
                return 1

        q = (
            db.query(Entry)
            .filter(
                Entry.payment_status == "completed",
                Entry.codm_id.isnot(None),
                Entry.excluded == False,
                Entry.contact_email.isnot(None),
            )
        )
        # Copy primitives while the session is open (avoid expired ORM after close).
        entries_data: list[dict] = []
        for e in q.all():
            email = (e.contact_email or "").strip()
            if not email:
                continue
            phone = (e.contact_phone or "").strip()
            ign = (e.codm_id or "").strip()
            if not ign and not phone:
                continue
            entries_data.append(
                {
                    "payment_reference": e.payment_reference,
                    "contact_email": email,
                    "codm_id": ign,
                    "contact_phone": phone,
                }
            )

    updated = 0
    not_found = 0

    for row in entries_data:
        payload: dict = {
            "codm_id": row["codm_id"],
            "contact_phone": row["contact_phone"],
            "contact_email": row["contact_email"],
        }
        if args.dry_run:
            logger.info(
                "[dry-run] would set D=%r for ref=%s ign=%r phone=%r tab=%r",
                row["contact_email"],
                row["payment_reference"],
                row["codm_id"],
                row["contact_phone"],
                target_tab,
            )
            updated += 1
            continue

        ok = update_entry_in_sheets(
            row["payment_reference"],
            payload,
            target_sheet=target_tab,
        )
        if ok:
            updated += 1
            logger.info("OK ref=%s -> email written", row["payment_reference"])
        else:
            not_found += 1
            logger.warning("Not found in sheet: ref=%s ign=%r", row["payment_reference"], row["codm_id"])

    logger.info("Done. updated=%s not_found=%s tab=%r dry_run=%s", updated, not_found, target_tab, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
