from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
import logging
from app.database import get_session
from app.models import User
from app.schemas import UserCreate, UserResponse, Token
from app.login_manager import manager, authenticate_user, get_password_hash
from app.config import get_settings
from app.rate_limit import auth_limiter
from app.logging_config import get_client_ip

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])
settings = get_settings()


@router.post("/register", response_model=UserResponse)
@auth_limiter.limit("5/minute")
async def register(request: Request, user: UserCreate, session: Session = Depends(get_session)):
    client_ip = get_client_ip(request)
    logger.info(f"Registration attempt: email={user.email}, ip={client_ip}")

    # Check if email already exists
    existing_user = session.exec(
        select(User).where(User.email == user.email)
    ).first()

    if existing_user:
        logger.warning(
            f"Registration failed - email exists: email={user.email}, ip={client_ip}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    db_user = User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=get_password_hash(user.password)
    )

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    logger.info(
        f"User registered successfully: email={user.email}, "
        f"full_name={user.full_name}, ip={client_ip}"
    )

    return db_user


@router.post("/token")
@auth_limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    client_ip = get_client_ip(request)
    # OAuth2 spec uses 'username' field, but we treat it as email
    logger.info(f"API login attempt: username={form_data.username}, ip={client_ip}")

    user = authenticate_user(session, form_data.username, form_data.password)

    if not user:
        logger.warning(
            f"API login failed - invalid credentials: username={form_data.username}, "
            f"ip={client_ip}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Create access token using fastapi-login
    access_token = manager.create_access_token(
        data={"sub": user.email},
        expires=timedelta(minutes=settings.access_token_expire_minutes)
    )

    # Set cookie for browser-based auth
    manager.set_cookie(response, access_token)

    logger.info(
        f"API login successful: email={user.email}, ip={client_ip}, "
        f"token_expires_minutes={settings.access_token_expire_minutes}"
    )

    # Return token for API compatibility
    return {"access_token": access_token, "token_type": "bearer"}