"""Password verification and JWT encode / decode.

Password storage in the seeded database uses plain SHA-256 (demo-only).
This is NOT production-grade security — it is sufficient for a local
academic demonstration that never leaves localhost.
"""
import hashlib
import time
from typing import Any, Dict

import jwt

from app.config import settings


# ---------------------------------------------------------------------------
# Password verification
# ---------------------------------------------------------------------------

def _sha256_hex(password: str) -> str:
    """Return the lowercase hex SHA-256 digest of a UTF-8 password string."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """
    Compare the SHA-256 hex of *plain_password* with *stored_hash*.
    The stored hash was generated identically when the demo database was seeded.
    """
    return _sha256_hex(plain_password) == stored_hash


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

_ALGORITHM = "HS256"


def create_access_token(payload: Dict[str, Any]) -> str:
    """
    Sign *payload* with the application JWT secret and add an expiry claim.
    Returns a compact JWT string.
    """
    data = payload.copy()
    data["exp"] = int(time.time()) + settings.JWT_EXPIRE_MINUTES * 60
    data["iat"] = int(time.time())
    return jwt.encode(data, settings.JWT_SECRET, algorithm=_ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and verify *token*.  Raises ``jwt.PyJWTError`` on any failure
    (expired, bad signature, malformed).
    """
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[_ALGORITHM])
