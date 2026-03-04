from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    role: str = "user"
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserLoginRequest(BaseModel):
    email: str
    password: str


class UserRegisterRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    expires_at: int
    user: UserResponse


class RegisterResponse(BaseModel):
    success: bool
    message: str
    user: UserResponse


class MessageResponse(BaseModel):
    success: bool
    message: str


class PlatformTokenExchangeRequest(BaseModel):
    platform_token: str


class TokenExchangeResponse(BaseModel):
    token: str
