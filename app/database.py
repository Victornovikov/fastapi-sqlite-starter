from sqlmodel import SQLModel, Session, create_engine
import logging
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Mask database URL for logging (hide credentials if present)
def mask_db_url(url: str) -> str:
    """Mask sensitive parts of database URL."""
    if "@" in url:
        # Has credentials, mask them
        protocol, rest = url.split("://", 1)
        if "@" in rest:
            _, host_and_path = rest.rsplit("@", 1)
            return f"{protocol}://***:***@{host_and_path}"
    return url

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    echo=False  # Disable SQLAlchemy echo, use our logging instead
)

logger.info(f"Database initialized: url={mask_db_url(settings.database_url)}")


def create_db_and_tables():
    """Create database tables if they don't exist."""
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        raise


def get_session():
    """Get a database session for dependency injection."""
    with Session(engine) as session:
        # Log at DEBUG level to avoid spam
        logger.debug(f"Database session created: id={id(session)}")
        try:
            yield session
        finally:
            logger.debug(f"Database session closed: id={id(session)}")