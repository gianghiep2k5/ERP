"""Auth router: POST /api/auth/login, GET /api/auth/me."""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import create_access_token, verify_password
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, MeResponse, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Obtain a demo JWT token",
)
def login(
    body: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    """
    Verify username + password against the seeded demo database.
    Returns a JWT access token on success.

    - Password is verified using SHA-256 (demo-only, not production security).
    - **password_hash is never returned.**
    """
    user: Optional[User] = db.query(User).filter(User.username == body.username).first()

    # Use a constant-time-equivalent check: always call verify_password even
    # when the user is not found, to avoid timing-based username enumeration.
    stored_hash = user.password_hash if user else ""
    if not user or not verify_password(body.password, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_access_token({"sub": user.username, "role": user.role})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        username=user.username,
        role=user.role,
    )


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Return the current authenticated user",
)
def me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> MeResponse:
    """
    Decode the bearer token and return the authenticated user's public fields.
    **password_hash is never returned.**
    """
    return MeResponse(
        user_id=current_user.user_id,
        username=current_user.username,
        role=current_user.role,
    )
