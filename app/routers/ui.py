from fastapi import APIRouter, Request, Response, Depends, Form, HTTPException, status, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlmodel import Session, select
from typing import Optional
from datetime import datetime, timedelta, timezone
import secrets
import logging

from app.database import get_session
from app.models import User, PasswordResetToken
from app.schemas import UserCreate
from app.rate_limit import auth_limiter
from app.login_manager import manager, authenticate_user, get_password_hash, get_current_user_optional
from app.security import (
    generate_csrf_token, set_csrf_cookie, verify_csrf, sha256_hex
)
from app.config import get_settings

from app.templates_config import templates
from app.email_client import get_email_client

from app.logging_config import get_client_ip as get_ip_from_request, mask_sensitive_data

logger = logging.getLogger(__name__)
router = APIRouter(tags=["ui"], include_in_schema=False)
settings = get_settings()


def hx_redirect(url: str, request: Request) -> Response:
    """
    Helper function for HTMX-aware redirects.

    If the request is from HTMX, sends HX-Redirect header with 204 status.
    Otherwise, performs a standard HTTP redirect.
    """
    if request.headers.get("HX-Request"):
        response = Response(status_code=204)
        response.headers["HX-Redirect"] = url
        return response
    else:
        return RedirectResponse(url=url, status_code=303)


@router.get("/", response_class=HTMLResponse)
async def home_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Render the landing page"""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "user": current_user,
        }
    )


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Render the login/signup page"""
    # If already logged in, redirect to dashboard
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)

    # Generate CSRF token
    csrf_token = generate_csrf_token()

    response = templates.TemplateResponse(
        "auth.html",
        {
            "request": request,
            "csrf": csrf_token,
        }
    )

    # Set CSRF cookie
    set_csrf_cookie(response, csrf_token)

    return response


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Render the dashboard page for logged-in users"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": current_user,
        }
    )


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Render the profile page"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": current_user,
        }
    )


@router.post("/logout", response_class=HTMLResponse)
async def logout(
    request: Request,
    response: Response,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Handle logout by clearing the auth cookie"""
    if current_user:
        logger.info(f"User logged out: email={current_user.email}")
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    # Clear the cookie
    response.delete_cookie(key=manager.cookie_name, path="/", httponly=True)
    return response


@router.post("/auth/login", response_class=HTMLResponse)
@auth_limiter.limit("10/minute")
async def handle_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    remember_me: Optional[str] = Form(None),
    csrf: str = Form(...),
    session: Session = Depends(get_session)
):
    """Handle login form submission and set cookie"""
    client_ip = get_ip_from_request(request)
    logger.info(f"Web login attempt: email={email}, ip={client_ip}")

    # Verify CSRF token
    try:
        verify_csrf(request, csrf)
    except Exception as e:
        logger.error(f"CSRF validation failed on login: email={email}, ip={client_ip}, error={str(e)}")
        raise

    user = authenticate_user(session, email, password)

    if not user:
        logger.warning(f"Web login failed - invalid credentials: email={email}, ip={client_ip}")
        # Return error fragment
        return templates.TemplateResponse(
            "fragments/auth_error.html",
            {
                "request": request,
                "error": "Invalid email or password"
            }
        )

    # Set expiry based on remember_me checkbox
    if remember_me == "true":
        # Remember for 30 days
        expires = timedelta(days=30)
        remember_duration = "30_days"
    else:
        # Standard session duration
        expires = timedelta(minutes=settings.access_token_expire_minutes)
        remember_duration = f"{settings.access_token_expire_minutes}_minutes"

    # Create access token using fastapi-login
    access_token = manager.create_access_token(
        data={"sub": user.email},
        expires=expires
    )

    # Create response with HTMX-aware redirect
    response = hx_redirect("/dashboard", request)

    # Set cookie with appropriate max_age matching token expiry
    response.set_cookie(
        key=manager.cookie_name,
        value=access_token,
        max_age=int(expires.total_seconds()),
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax"
    )

    logger.info(
        f"Web login successful: email={user.email}, ip={client_ip}, "
        f"remember_me={remember_me == 'true'}, duration={remember_duration}"
    )

    return response


@router.post("/auth/signup", response_class=HTMLResponse)
@auth_limiter.limit("5/minute")
async def handle_signup(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    csrf: str = Form(...),
    session: Session = Depends(get_session)
):
    """Handle signup form submission"""
    client_ip = get_ip_from_request(request)
    logger.info(f"Web signup attempt: email={email}, full_name={full_name}, ip={client_ip}")

    # Verify CSRF token
    try:
        verify_csrf(request, csrf)
    except Exception as e:
        logger.error(f"CSRF validation failed on signup: email={email}, ip={client_ip}, error={str(e)}")
        raise

    # Check if email already exists
    existing_user = session.exec(
        select(User).where(User.email == email)
    ).first()

    if existing_user:
        logger.warning(f"Web signup failed - email exists: email={email}, ip={client_ip}")
        return templates.TemplateResponse(
            "fragments/auth_error.html",
            {
                "request": request,
                "error": "Email already registered"
            }
        )

    # Create new user
    db_user = User(
        email=email,
        full_name=full_name,
        hashed_password=get_password_hash(password)
    )
    
    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    # Create access token using fastapi-login
    expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = manager.create_access_token(
        data={"sub": db_user.email},
        expires=expires
    )

    # Create response with HTMX-aware redirect
    response = hx_redirect("/dashboard", request)

    # Set cookie with appropriate max_age matching token expiry
    response.set_cookie(
        key=manager.cookie_name,
        value=access_token,
        max_age=int(expires.total_seconds()),
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax"
    )

    logger.info(
        f"Web signup successful: email={email}, full_name={full_name}, ip={client_ip}"
    )

    return response


@router.get("/forgot", response_class=HTMLResponse)
async def forgot_password_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Render the forgot password page"""
    # If already logged in, redirect to dashboard
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)

    # Generate CSRF token
    csrf_token = generate_csrf_token()

    response = templates.TemplateResponse(
        "forgot.html",
        {
            "request": request,
            "csrf": csrf_token,
        }
    )

    # Set CSRF cookie
    set_csrf_cookie(response, csrf_token)

    return response


@router.post("/auth/forgot", response_class=HTMLResponse)
@auth_limiter.limit("3/minute")
async def handle_forgot_password(
    request: Request,
    email: str = Form(...),
    csrf: str = Form(...),
    session: Session = Depends(get_session),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Handle forgot password form submission"""
    client_ip = get_ip_from_request(request)
    logger.info(f"Password reset requested: email={email}, ip={client_ip}")

    # Verify CSRF token
    try:
        verify_csrf(request, csrf)
    except Exception as e:
        logger.error(f"CSRF validation failed on forgot password: email={email}, ip={client_ip}, error={str(e)}")
        raise

    # Always return success to prevent email enumeration
    user = session.exec(select(User).where(User.email == email)).first()

    if user:
        # Generate reset token
        raw_token = secrets.token_urlsafe(32)

        # Create token record
        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=sha256_hex(raw_token),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        session.add(reset_token)
        session.commit()

        # Send email in background (non-blocking)
        email_client = get_email_client()
        if email_client:
            try:
                background_tasks.add_task(
                    email_client.send_password_reset,
                    email=email,
                    token=raw_token,
                    user_name=user.full_name
                )
            except Exception as e:
                # Log error but don't expose it to user
                logger.error(f"Failed to queue password reset email: {e}")
                # Continue anyway to prevent enumeration
        else:
            # Fallback to logging if email not configured
            reset_link = f"{request.base_url}reset?token={raw_token}"
            logger.info(f"Password reset link for {email}: {reset_link}")

    # Always return success message
    return templates.TemplateResponse(
        "fragments/forgot_success.html",
        {
            "request": request,
            "message": "If an account exists with that email, you will receive a password reset link."
        }
    )


@router.get("/reset", response_class=HTMLResponse)
async def reset_password_page(
    request: Request,
    token: str,
    session: Session = Depends(get_session)
):
    """Render the password reset form"""
    # Verify token exists and is valid
    token_hash = sha256_hex(token)
    reset_token = session.exec(
        select(PasswordResetToken)
        .where(PasswordResetToken.token_hash == token_hash)
        .where(PasswordResetToken.used_at.is_(None))
        .where(PasswordResetToken.expires_at > datetime.now(timezone.utc))
    ).first()

    if not reset_token:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "status_code": 400,
                "title": "Invalid or Expired Token",
                "detail": "This password reset link is invalid or has expired. Please request a new one."
            },
            status_code=400
        )

    # Generate CSRF token
    csrf_token = generate_csrf_token()

    response = templates.TemplateResponse(
        "reset.html",
        {
            "request": request,
            "csrf": csrf_token,
            "token": token,
        }
    )

    # Set CSRF cookie
    set_csrf_cookie(response, csrf_token)

    return response


@router.post("/auth/reset", response_class=HTMLResponse)
@auth_limiter.limit("5/minute")
async def handle_reset_password(
    request: Request,
    token: str = Form(...),
    new_password: str = Form(...),
    csrf: str = Form(...),
    session: Session = Depends(get_session)
):
    """Handle password reset form submission"""
    client_ip = get_ip_from_request(request)
    logger.info(f"Password reset attempt: token={mask_sensitive_data(token)}, ip={client_ip}")

    # Verify CSRF token
    try:
        verify_csrf(request, csrf)
    except Exception as e:
        logger.error(f"CSRF validation failed on reset password: ip={client_ip}, error={str(e)}")
        raise

    # Verify reset token
    token_hash = sha256_hex(token)
    reset_token = session.exec(
        select(PasswordResetToken)
        .where(PasswordResetToken.token_hash == token_hash)
        .where(PasswordResetToken.used_at.is_(None))
        .where(PasswordResetToken.expires_at > datetime.now(timezone.utc))
    ).first()

    if not reset_token:
        logger.warning(f"Password reset failed - invalid token: ip={client_ip}")
        return templates.TemplateResponse(
            "fragments/reset_error.html",
            {
                "request": request,
                "error": "Invalid or expired token"
            }
        )

    # Get user and update password
    user = session.get(User, reset_token.user_id)
    if not user:
        return templates.TemplateResponse(
            "fragments/reset_error.html",
            {
                "request": request,
                "error": "User not found"
            }
        )

    # Update password
    user.hashed_password = get_password_hash(new_password)

    # Mark token as used
    reset_token.used_at = datetime.now(timezone.utc)

    session.commit()

    logger.info(f"Password reset completed: email={user.email}, ip={client_ip}")

    # Return HTMX-aware redirect to login
    return hx_redirect("/login", request)

