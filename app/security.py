from datetime import datetime, timedelta
from typing import Optional
import secrets
import hashlib
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Request, Response, status
from app.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_token(token: str):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None


# CSRF Protection Functions
CSRF_COOKIE_NAME = "csrftoken"

def generate_csrf_token() -> str:
    """Generate a secure random CSRF token"""
    return secrets.token_urlsafe(16)


def set_csrf_cookie(response: Response, token: str):
    """Set CSRF token as a cookie that can be read by JavaScript"""
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=token,
        httponly=False,  # Must be readable by forms/JavaScript
        samesite="lax",
        secure=settings.cookie_secure if hasattr(settings, 'cookie_secure') else False,
        path="/",
        max_age=3600  # 1 hour
    )


def verify_csrf(request: Request, form_token: str):
    """Verify CSRF token matches between cookie and form submission"""
    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
    if not cookie_token or not form_token or cookie_token != form_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF verification failed"
        )


def sha256_hex(s: str) -> str:
    """Create SHA256 hash of a string (for password reset tokens)"""
    return hashlib.sha256(s.encode()).hexdigest()