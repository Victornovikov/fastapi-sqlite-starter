"""
FastAPI-Login configuration and setup.
"""
from typing import Optional
from fastapi import Request, Response, Depends
from fastapi_login import LoginManager
from fastapi_login.exceptions import InvalidCredentialsException
from sqlmodel import Session, select
from passlib.context import CryptContext
import logging

from app.models import User
from app.database import get_session
from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create LoginManager instance
from datetime import timedelta

manager = LoginManager(
    secret=settings.secret_key,
    token_url="/auth/token",
    use_cookie=True,
    use_header=True,  # Support both cookie and header auth
    cookie_name="access-token",
    default_expiry=timedelta(minutes=settings.access_token_expire_minutes),
    not_authenticated_exception=InvalidCredentialsException
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


@manager.user_loader()
def load_user(email: str) -> Optional[User]:
    """
    Load a user by email for fastapi-login.

    This function is called by fastapi-login to load the user from the database
    when a valid token is presented.
    """
    # Create a new session for this request
    # Import the module to access the potentially overridden engine
    import app.database
    db = Session(app.database.engine)

    logger.debug(f"load_user called with email: {email}, engine: {id(app.database.engine)}")

    try:
        # Ensure we get fresh data - important for tests with multiple users
        db.expire_all()

        statement = select(User).where(User.email == email)
        user = db.exec(statement).first()
        logger.debug(f"load_user found user: {user.email if user else None}")

        # Check if user is active
        if user and not user.is_active:
            logger.warning(f"Inactive user attempted access: email={email}")
            return None

        if not user:
            logger.debug(f"User not found for token: email={email}")

        return user
    finally:
        db.close()


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user by email and password.
    """
    statement = select(User).where(User.email == email)
    user = db.exec(statement).first()

    if not user:
        logger.debug(f"Authentication failed - user not found: email={email}")
        return None
    if not verify_password(password, user.hashed_password):
        logger.debug(f"Authentication failed - invalid password: email={email}")
        return None
    if not user.is_active:
        logger.warning(f"Authentication failed - inactive user: email={email}")
        return None

    return user


async def get_current_user_optional(request: Request, db: Session = Depends(get_session)) -> Optional[User]:
    """
    Get current user from cookie if present, return None if not authenticated.
    This is for optional authentication where routes work for both authenticated and anonymous users.
    """
    try:
        # Try to get the token from cookie
        token = request.cookies.get(manager.cookie_name)
        if not token:
            return None

        # Decode the token using JWT directly
        import jwt
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        if not payload:
            return None

        email = payload.get("sub")
        if not email:
            return None

        # Load the user
        return load_user(email)
    except Exception as e:
        logger.debug(f"Optional auth failed: {str(e)}")
        return None