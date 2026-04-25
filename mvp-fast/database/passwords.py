"""Admin password hashing: bcrypt; legacy SHA-256 rows upgraded on next login.

Uses the `bcrypt` package directly. Passlib is not used: passlib 1.7.4 is incompatible
with bcrypt 4.1+ (removed ``__about__``), and passlib is unmaintained.
"""
from __future__ import annotations

import hashlib
import re

import bcrypt

_LEGACY_SHA256 = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)
_BCRYPT_PREFIX = ("$2a$", "$2b$", "$2y$")


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("ascii")


def verify_password(plain: str, stored: str) -> bool:
    if not stored or not isinstance(stored, str):
        return False
    s = stored.strip()
    if s.startswith(_BCRYPT_PREFIX):
        try:
            return bcrypt.checkpw(plain.encode("utf-8"), s.encode("ascii"))
        except (ValueError, TypeError):
            return False
    if _LEGACY_SHA256.match(s):
        return hashlib.sha256(plain.encode("utf-8")).hexdigest() == s
    return False


def is_legacy_sha256_hash(stored: str) -> bool:
    return bool(stored and _LEGACY_SHA256.match(stored.strip()))
