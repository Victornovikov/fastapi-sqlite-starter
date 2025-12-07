from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select
import logging
from app.database import get_session
from app.models import User
from app.schemas import UserResponse, UserUpdate
from app.login_manager import manager
from app.logging_config import get_client_ip
from app.security import verify_csrf
from app.templates_config import templates

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    request: Request,
    current_user: User = Depends(manager)
):
    # Debug token extraction
    auth_header = request.headers.get("Authorization")
    if auth_header:
        token = auth_header.replace("Bearer ", "")
        logger.debug(f"Token in header: {token[:50]}...")
    logger.info(f"Profile accessed: user={current_user.email}")
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_user_me(
    request: Request,
    user_update: UserUpdate,
    current_user: User = Depends(manager),
    session: Session = Depends(get_session)
):
    client_ip = get_client_ip(request)
    updated_fields = []
    if user_update.email:
        statement = select(User).where(
            (User.email == user_update.email) & (User.id != current_user.id)
        )
        existing_user = session.exec(statement).first()
        if existing_user:
            logger.warning(
                f"Profile update failed - email exists: user={current_user.email}, "
                f"new_email={user_update.email}, ip={client_ip}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        current_user.email = user_update.email
        updated_fields.append("email")
    
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
        updated_fields.append("full_name")
    
    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    if updated_fields:
        logger.info(
            f"Profile updated: user={current_user.email}, fields={updated_fields}, ip={client_ip}"
        )

    return current_user


@router.get("/", response_model=List[UserResponse])
async def read_users(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(manager),
    session: Session = Depends(get_session)
):
    client_ip = get_client_ip(request)

    if not current_user.is_superuser:
        logger.warning(
            f"Unauthorized admin access attempt: user={current_user.email}, ip={client_ip}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    statement = select(User).offset(skip).limit(limit)
    users = session.exec(statement).all()

    logger.info(
        f"Admin user list accessed: admin={current_user.email}, count={len(users)}, "
        f"skip={skip}, limit={limit}, ip={client_ip}"
    )

    return users


@router.post("/update-profile", response_class=HTMLResponse)
async def update_profile(
    request: Request,
    full_name: str = Form(...),
    csrf: str = Form(...),
    current_user: User = Depends(manager),
    session: Session = Depends(get_session)
):
    """Update user profile information via HTMX form"""
    client_ip = get_client_ip(request)

    # Verify CSRF token
    try:
        verify_csrf(request, csrf)
    except Exception as e:
        logger.error(f"CSRF validation failed on profile update: user={current_user.email}, ip={client_ip}, error={str(e)}")
        return HTMLResponse(
            content='<div style="color: var(--pico-del-color);">Security validation failed. Please refresh and try again.</div>',
            status_code=403
        )

    # Get fresh user from database
    db_user = session.get(User, current_user.id)
    if not db_user:
        return HTMLResponse(
            content='<div style="color: var(--pico-del-color);">User not found.</div>',
            status_code=404
        )

    # Update user information
    db_user.full_name = full_name
    session.add(db_user)
    session.commit()

    logger.info(f"Profile updated: user={current_user.email}, ip={client_ip}")

    return HTMLResponse(
        content='<div style="color: var(--pico-ins-color);">Profile updated successfully!</div>'
    )