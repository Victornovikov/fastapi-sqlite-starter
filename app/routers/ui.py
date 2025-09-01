from fastapi import APIRouter, Request, Response, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlmodel import Session, select
from typing import Optional
from datetime import timedelta

from app.database import get_session
from app.auth import authenticate_user, get_current_user_optional
from app.models import User
from app.schemas import UserCreate
from app.security import create_access_token, get_password_hash
from app.config import get_settings

from app.templates_config import templates

router = APIRouter(tags=["ui"], include_in_schema=False)
settings = get_settings()


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
    
    return templates.TemplateResponse(
        "auth.html",
        {
            "request": request,
        }
    )


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
):
    """Handle logout by clearing the auth cookie"""
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="access_token", path="/", secure=False, httponly=True)
    return response


@router.post("/auth/login", response_class=HTMLResponse)
async def handle_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session)
):
    """Handle login form submission and set cookie"""
    user = authenticate_user(session, username, password)
    
    if not user:
        # Return error fragment
        return templates.TemplateResponse(
            "fragments/auth_error.html",
            {
                "request": request,
                "error": "Invalid username or password"
            }
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Create response with redirect
    response = templates.TemplateResponse(
        "fragments/auth_success.html",
        {
            "request": request,
            "redirect_url": "/dashboard"
        }
    )
    
    # Set cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax"
    )
    
    return response


@router.post("/auth/signup", response_class=HTMLResponse)
async def handle_signup(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(None),
    session: Session = Depends(get_session)
):
    """Handle signup form submission"""
    # Check if user exists
    statement = select(User).where(
        (User.username == username) | (User.email == email)
    )
    existing_user = session.exec(statement).first()
    
    if existing_user:
        error_msg = "Username already taken" if existing_user.username == username else "Email already registered"
        return templates.TemplateResponse(
            "fragments/auth_error.html",
            {
                "request": request,
                "error": error_msg
            }
        )
    
    # Create new user
    db_user = User(
        username=username,
        email=email,
        full_name=full_name,
        hashed_password=get_password_hash(password)
    )
    
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": db_user.username}, expires_delta=access_token_expires
    )
    
    # Create response with redirect
    response = templates.TemplateResponse(
        "fragments/auth_success.html",
        {
            "request": request,
            "redirect_url": "/dashboard"
        }
    )
    
    # Set cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
        secure=False,  # Set to True in production
        samesite="lax"
    )
    
    return response
