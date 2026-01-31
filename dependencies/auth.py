from fastapi import Depends, HTTPException, status
from core.config import settings

async def get_current_user(token: str = None):
    """Placeholder dependency for authentication"""
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return {"user_id": "123"}