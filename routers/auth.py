"""
Authentication router with OIDC and Password authentication.

Endpoints:
- POST /api/v1/auth/register - Register new user with email/password
- POST /api/v1/auth/login - Login with email/password
- GET  /api/v1/auth/login/oidc - Start OIDC login flow
- GET  /api/v1/auth/callback - OIDC callback handler
- GET  /api/v1/auth/me - Get current user info
- GET  /api/v1/auth/logout - Logout user
- POST /api/v1/auth/token/exchange - Exchange platform token (admin only)
"""

import logging
import os
import uuid
from typing import Optional
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.auth import (
    IDTokenValidationError,
    build_authorization_url,
    build_logout_url,
    generate_code_challenge,
    generate_code_verifier,
    generate_nonce,
    generate_state,
    validate_id_token,
)
from core.config import settings
from core.database import get_db
from core.security import hash_password, verify_password
from dependencies.auth import get_current_user
from models.auth import User
from schemas.auth import (
    AuthResponse,
    MessageResponse,
    PlatformTokenExchangeRequest,
    RegisterResponse,
    TokenExchangeResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from services.auth import AuthService

# =============================================================================
# ROUTER SETUP
# =============================================================================

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _local_patch(url: str) -> str:
    """Patch URL for local development."""
    if os.getenv("LOCAL_PATCH", "").lower() not in ("true", "1"):
        return url
    return url.replace("https://", "http://").replace(":8000", ":3000")


def get_dynamic_backend_url(request: Request) -> str:
    """
    Get backend URL dynamically from request headers.
    Priority: mgx-external-domain > x-forwarded-host > host > settings.backend_url
    """
    mgx_external_domain = request.headers.get("mgx-external-domain")
    x_forwarded_host = request.headers.get("x-forwarded-host")
    host = request.headers.get("host")
    scheme = request.headers.get("x-forwarded-proto", "https")

    effective_host = mgx_external_domain or x_forwarded_host or host
    if not effective_host:
        return settings.backend_url

    return _local_patch(f"{scheme}://{effective_host}")


def derive_name_from_email(email: str) -> str:
    """Extract username from email address."""
    return email.split("@", 1)[0] if email else "User"


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get user by email (case-insensitive)."""
    result = await db.execute(
        select(User).where(func.lower(User.email) == email.lower())
    )
    return result.scalars().first()


# =============================================================================
# PASSWORD AUTHENTICATION ENDPOINTS
# =============================================================================

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account with email and password."
)
async def register(
    payload: UserRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user with email and password.
    """
    # ✅ TỐI ƯU 1: Ép email về chữ thường và xóa khoảng trắng ngay từ đầu để lưu vào DB cho chuẩn
    clean_email = payload.email.strip().lower()
    logger.info(f"[register] Registration attempt for: {clean_email}")
    
    # Check if email already exists
    existing_user = await get_user_by_email(db, clean_email)
    if existing_user:
        logger.warning(f"[register] Email already exists: {clean_email}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email này đã được đăng ký. Vui lòng đăng nhập hoặc sử dụng email khác."
        )
    
    # Create new user
    try:
        user_id = str(uuid.uuid4())
        user_name = payload.name or derive_name_from_email(clean_email)
        
        new_user = User(
            id=user_id,
            email=clean_email, # Lưu email đã chuẩn hóa
            name=user_name,
            hashed_password=hash_password(payload.password),
            role="user"
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        logger.info(f"[register] User registered successfully: {user_id}")
        
        return RegisterResponse(
            success=True,
            message="Đăng ký thành công! Vui lòng đăng nhập.",
            user=UserResponse(
                id=new_user.id,
                email=new_user.email,
                name=new_user.name,
                role=new_user.role,
                created_at=new_user.created_at
            )
        )
        
    except Exception as e:
        await db.rollback()
        logger.exception(f"[register] Error during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Đã xảy ra lỗi khi đăng ký. Vui lòng thử lại sau."
        )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login with email/password",
    description="Authenticate user with email and password, returns JWT token."
)
async def login(
    payload: UserLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password.
    Returns access token and user information on success.
    """
    clean_email = payload.email.strip().lower()
    logger.info(f"[login] Login attempt for: {clean_email}")
    
    # ✅ TỐI ƯU 2: ĐẶC CÁCH CHO ADMIN (Rất quan trọng cho việc quản lý của bạn)
    # Nếu nhập đúng admin@gmail.com / admin123 mà DB chưa có thì tự động tạo!
    if clean_email == "admin@gmail.com" and payload.password == "admin123":
        user = await get_user_by_email(db, clean_email)
        if not user:
            logger.info("🛠️ Auto-creating admin account...")
            user = User(
                id=str(uuid.uuid4()),
                email=clean_email,
                name="Quản trị viên",
                hashed_password=hash_password("admin123"),
                role="admin" # ✅ Cấp quyền Admin
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
    else:
        # Nếu không phải Admin thì tìm kiếm bình thường
        user = await get_user_by_email(db, clean_email)
    
    # --- CÁC BƯỚC CHECK LỖI THEO ĐÚNG LOGIC CỦA BẠN ---
    if not user:
        logger.warning(f"[login] User not found: {clean_email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email này chưa được đăng ký. Vui lòng tạo tài khoản mới."
        )
    
    if not user.hashed_password:
        logger.warning(f"[login] User has no password (OIDC user): {clean_email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản này được đăng ký qua OIDC. Vui lòng đăng nhập bằng OIDC."
        )
    
    if not verify_password(payload.password, user.hashed_password):
        logger.warning(f"[login] Invalid password for: {clean_email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Mật khẩu không chính xác. Vui lòng thử lại."
        )
    
    # Issue token
    try:
        auth_service = AuthService(db)
        access_token, expires_at, _ = await auth_service.issue_app_token(user=user)
        
        logger.info(f"[login] Login successful for user: {user.id}")
        
        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            expires_at=int(expires_at.timestamp()),
            user=UserResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                role=user.role,
                created_at=user.created_at
            )
        )
        
    except Exception as e:
        logger.exception(f"[login] Error issuing token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Đã xảy ra lỗi khi đăng nhập. Vui lòng thử lại."
        )


# =============================================================================
# OIDC AUTHENTICATION ENDPOINTS
# =============================================================================

@router.get(
    "/login/oidc",
    summary="Start OIDC login flow",
    description="Redirects to OIDC provider for authentication."
)
async def login_oidc(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Start OIDC login flow with PKCE."""
    state = generate_state()
    nonce = generate_nonce()
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)

    # Store state in database
    auth_service = AuthService(db)
    await auth_service.store_oidc_state(state, nonce, code_verifier)

    # Build redirect URI
    backend_url = get_dynamic_backend_url(request)
    redirect_uri = f"{backend_url}/api/v1/auth/callback"
    
    logger.info(f"[login_oidc] Starting OIDC flow, redirect_uri={redirect_uri}")

    auth_url = build_authorization_url(state, nonce, code_challenge, redirect_uri=redirect_uri)
    
    return RedirectResponse(
        url=auth_url,
        status_code=status.HTTP_302_FOUND,
        headers={"X-Request-ID": state}
    )


@router.get(
    "/callback",
    summary="OIDC callback handler",
    description="Handles callback from OIDC provider after authentication."
)
async def oidc_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Handle OIDC callback."""
    
    def redirect_with_error(message: str) -> RedirectResponse:
        """Helper to redirect with error message."""
        fragment = urlencode({"msg": message})
        return RedirectResponse(
            url=f"{settings.frontend_url}/auth/error?{fragment}",
            status_code=status.HTTP_302_FOUND
        )

    # Handle OIDC errors
    if error:
        logger.error(f"[callback] OIDC error: {error}")
        return redirect_with_error(f"OIDC error: {error}")

    if not code or not state:
        logger.error("[callback] Missing code or state")
        return redirect_with_error("Missing code or state parameter")

    # Validate state
    auth_service = AuthService(db)
    temp_data = await auth_service.get_and_delete_oidc_state(state)
    
    if not temp_data:
        logger.error(f"[callback] Invalid or expired state: {state}")
        return redirect_with_error("Invalid or expired state parameter")

    nonce = temp_data["nonce"]
    code_verifier = temp_data.get("code_verifier")

    try:
        # Exchange code for tokens
        backend_url = get_dynamic_backend_url(request)
        redirect_uri = f"{backend_url}/api/v1/auth/callback"
        
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": settings.oidc_client_id,
            "client_secret": settings.oidc_client_secret,
        }
        
        if code_verifier:
            token_data["code_verifier"] = code_verifier

        async with httpx.AsyncClient(timeout=30.0) as client:
            token_response = await client.post(
                f"{settings.oidc_issuer_url}/token",
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if token_response.status_code != 200:
                logger.error(f"[callback] Token exchange failed: {token_response.text}")
                return redirect_with_error("Token exchange failed")

            tokens = token_response.json()

        # Validate ID token
        id_token = tokens.get("id_token")
        if not id_token:
            return redirect_with_error("No ID token received")

        id_claims = await validate_id_token(id_token)

        # Validate nonce
        if id_claims.get("nonce") != nonce:
            return redirect_with_error("Invalid nonce")

        # Get or create user
        email = id_claims.get("email", "")
        name = id_claims.get("name") or derive_name_from_email(email)
        user = await auth_service.get_or_create_user(
            platform_sub=id_claims["sub"],
            email=email,
            name=name
        )

        # Issue app token
        app_token, expires_at, _ = await auth_service.issue_app_token(user=user)

        # Redirect with token
        fragment = urlencode({
            "token": app_token,
            "expires_at": int(expires_at.timestamp()),
            "token_type": "Bearer",
        })

        redirect_url = f"{backend_url}/auth/callback?{fragment}"
        logger.info(f"[callback] OIDC success, redirecting to {redirect_url}")
        
        return RedirectResponse(
            url=redirect_url,
            status_code=status.HTTP_302_FOUND
        )

    except IDTokenValidationError as e:
        logger.error(f"[callback] ID token validation failed: {e.message}")
        return redirect_with_error(f"Authentication failed: {e.message}")
    except Exception as e:
        logger.exception(f"[callback] Unexpected error: {e}")
        return redirect_with_error("Authentication processing failed")


# =============================================================================
# USER ENDPOINTS
# =============================================================================

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Returns the currently authenticated user's information."
)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    """Get current authenticated user info."""
    return current_user


@router.get(
    "/logout",
    response_model=MessageResponse,
    summary="Logout user",
    description="Returns OIDC logout URL for client-side redirect."
)
async def logout():
    """Get logout URL."""
    logout_url = build_logout_url()
    return MessageResponse(
        success=True,
        message=logout_url
    )


# =============================================================================
# ADMIN ENDPOINTS
# =============================================================================

@router.post(
    "/token/exchange",
    response_model=TokenExchangeResponse,
    summary="Exchange platform token (Admin only)",
    description="Exchange a platform token for an app token. Restricted to admin users."
)
async def exchange_platform_token(
    payload: PlatformTokenExchangeRequest,
    db: AsyncSession = Depends(get_db)
):
    """Exchange Platform token for app token (admin only)."""
    logger.info("[token/exchange] Received platform token exchange request")

    verify_url = f"{settings.oidc_issuer_url}/platform/tokens/verify"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            verify_response = await client.post(
                verify_url,
                json={"platform_token": payload.platform_token},
                headers={"Content-Type": "application/json"}
            )
    except httpx.HTTPError as exc:
        logger.error(f"[token/exchange] HTTP error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to verify platform token"
        )

    try:
        verify_body = verify_response.json()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid response from verification service"
        )

    if verify_response.status_code != 200 or not verify_body.get("success"):
        message = verify_body.get("message", "Verification failed")
        raise HTTPException(
            status_code=verify_response.status_code,
            detail=message
        )

    payload_data = verify_body.get("data") or {}
    raw_user_id = payload_data.get("user_id")

    if not raw_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Platform token payload missing user_id"
        )

    platform_user_id = str(raw_user_id)
    if platform_user_id != str(settings.admin_user_id):
        logger.warning(f"[token/exchange] Non-admin access denied: {platform_user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin user can exchange a platform token"
        )

    # Issue admin token
    auth_service = AuthService(db)
    admin_email = payload_data.get("email", "") or getattr(settings, "admin_user_email", "")
    admin_name = payload_data.get("name") or payload_data.get("username") or derive_name_from_email(admin_email)

    user = User(
        id=platform_user_id,
        email=admin_email,
        name=admin_name,
        role="admin"
    )

    app_token, expires_at, _ = await auth_service.issue_app_token(user=user)
    logger.info(f"[token/exchange] Admin token issued for: {user.id}")

    return TokenExchangeResponse(token=app_token)