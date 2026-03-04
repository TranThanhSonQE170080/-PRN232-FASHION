"""
Password hashing and verification utilities.
"""

try:
    import bcrypt as _bcrypt  # type: ignore
except Exception:
    _bcrypt = None


def hash_password(password: str) -> str:
    """Hash a plain text password.

    Prefer the `bcrypt` library directly when available (works with existing hashed rows).
    Falls back to `passlib` if needed.
    """
    if _bcrypt:
        return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")

    from passlib.context import CryptContext

    pwd_ctx = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto", bcrypt__rounds=12)
    return pwd_ctx.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a stored hashed password.

    Try `bcrypt` native verify first (if available), then fall back to passlib.
    """
    if _bcrypt:
        try:
            return _bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception:
            return False

    try:
        from passlib.context import CryptContext

        pwd_ctx = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto", bcrypt__rounds=12)
        return pwd_ctx.verify(plain_password, hashed_password)
    except Exception:
        return False