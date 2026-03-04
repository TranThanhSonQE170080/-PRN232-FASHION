from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from core.auth import decode_access_token
from schemas.auth import UserResponse

security = HTTPBearer(auto_error=False)


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> UserResponse:
    """Decode bearer token and return user info as `UserResponse`.

    Raises 401 if token is missing/invalid.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authentication token")

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user = UserResponse(
        id=str(payload.get("sub") or ""),
        email=payload.get("email") or "",
        name=payload.get("name"),
        role=payload.get("role") or "user",
        last_login=payload.get("last_login"),
    )
    return user


async def get_admin_user(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """Ensure the current user is an admin."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return current_user