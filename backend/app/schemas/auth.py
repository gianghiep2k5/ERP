"""Pydantic schemas for auth endpoints.

password_hash is explicitly excluded from every response model.
"""
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    username: str
    password: str


# ---------------------------------------------------------------------------
# Responses  (password_hash is NEVER included)
# ---------------------------------------------------------------------------

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str


class MeResponse(BaseModel):
    user_id: str
    username: str
    role: str
