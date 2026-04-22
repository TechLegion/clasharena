"""
MVP-Fast: set env and DB before any `main` or `database` import (import order matters).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Project root: mvp-fast/
_MVP = Path(__file__).resolve().parents[2]
if str(_MVP) not in sys.path:
    sys.path.insert(0, str(_MVP))
_BACKEND = _MVP / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

# One shared on-disk DB file so SQLAlchemy pooling sees the same SQLite data.
_test_sqlite = _MVP / "backend" / "tests" / ".mvp_test.db"
if _test_sqlite.exists():
    _test_sqlite.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{_test_sqlite.as_posix()}"
os.environ.pop("DATABASE_PRIVATE_URL", None)
os.environ.setdefault("PAYMENT_GATEWAY", "paystack")
# Avoid side effects in optional integrations during tests
os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", "")
