"""
Security utilities for CSRF protection and password reset tokens.
Password hashing and authentication are now handled by fastapi-login in login_manager.py
"""
import secrets
import hashlib
import logging
from fastapi import HTTPException, Request, Response, status
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

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
        # Get client IP for logging
        from app.logging_config import get_client_ip, mask_sensitive_data
        client_ip = get_client_ip(request)

        logger.error(
            f"CSRF validation failed: expected={mask_sensitive_data(cookie_token or 'none')}, "
            f"received={mask_sensitive_data(form_token or 'none')}, ip={client_ip}, "
            f"path={request.url.path}"
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF verification failed"
        )


def sha256_hex(s: str) -> str:
    """Create SHA256 hash of a string (for password reset tokens)"""
    return hashlib.sha256(s.encode()).hexdigest()