"""Admin password hashing: bcrypt; legacy SHA-256 rows upgraded on next login."""
from __future__ import annotations

import hashlib
import re
from passlib.context import CryptContext

_pwd = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)

_LEGACY_SHA256 = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)


def hash_password(plain: str) -> str:
    return _pwd.hash(plain)


def verify_password(plain: str, stored: str) -> bool:
    if not stored or not isinstance(stored, str):
        return False
    s = stored.strip()
    if s.startswith(("$2a$", "$2b$", "$2y$")):
        return _pwd.verify(plain, s)
    if _LEGACY_SHA256.match(s):
        return hashlib.sha256(plain.encode("utf-8")).hexdigest() == s
    return False


def is_legacy_sha256_hash(stored: str) -> bool:
    return bool(stored and _LEGACY_SHA256.match(stored.strip()))
