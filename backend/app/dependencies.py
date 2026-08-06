"""Reusable FastAPI dependencies: DB session, current user, role guards."""
from typing import Annotated, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth import decode_access_token
from app.database import get_db
from app.models.user import User

# ---------------------------------------------------------------------------
# Role sets (from implementation plan §6)
# ---------------------------------------------------------------------------
APPROVER_ROLES = {"Warehouse Manager"}
PLANNER_ROLES = {"Planner"}
READ_ALL_ROLES = {
    "Warehouse Staff",
    "Warehouse Manager",
    "Planner",
    "Quality Manager",
    "Branch Manager",
}

# ---------------------------------------------------------------------------
# Bearer token extractor (auto_error=False lets us return a clean 401)
# ---------------------------------------------------------------------------
_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(_bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    Extract and validate the JWT from the Authorization header.
    Returns the corresponding User ORM object.
    Raises HTTP 401 if the token is missing, expired, or invalid.
    Raises HTTP 401 if the user no longer exists in the database.
    NOTE: password_hash is present on the returned User object but must
    never be included in any API response schema.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username: Optional[str] = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing subject",
        )

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


def require_role(allowed_roles: set[str]):
    """
    Dependency factory: returns a dependency that verifies the current
    user's role is in *allowed_roles*, raising HTTP 403 otherwise.

    Usage::

        @router.post("/approve")
        def approve(user: Annotated[User, Depends(require_role(APPROVER_ROLES))]):
            ...
    """
    def _check(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Role '{current_user.role}' is not permitted for this action. "
                    f"Required: {sorted(allowed_roles)}"
                ),
            )
        return current_user

    return _check
