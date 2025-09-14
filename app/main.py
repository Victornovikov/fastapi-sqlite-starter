from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import logging
from app.database import create_db_and_tables
from app.routers import auth, users, ui
from app import webhooks
from app.templates_config import templates
from app.rate_limit import auth_limiter
from app.logging_config import setup_logging, get_client_ip
from app.config import get_settings

# Initialize settings and logging
settings = get_settings()
setup_logging(
    log_level=settings.log_level,
    log_dir=settings.log_dir,
    log_file=settings.log_file,
    max_bytes=settings.log_max_bytes,
    backup_count=settings.log_backup_count,
    enable_console=settings.log_to_console
)

# Get logger for this module
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FastAPI Auth App",
    description="A FastAPI application with JWT authentication",
    version="1.0.0",
)

logger.info("FastAPI application initialized")

# Add rate limiter to app state
app.state.limiter = auth_limiter

# Custom rate limit handler that logs the event
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    client_ip = get_client_ip(request)
    logger.warning(
        f"Rate limit exceeded: path={request.url.path}, ip={client_ip}, "
        f"limit={exc.detail}"
    )

    # Check if this is a UI endpoint that expects HTML
    if request.url.path.startswith("/auth/") or request.url.path in ["/login", "/signup", "/forgot-password", "/reset-password"]:
        from fastapi.responses import HTMLResponse
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html>
            <head><title>Rate Limit Exceeded</title></head>
            <body>
                <h1>Too Many Requests</h1>
                <p>You have made too many requests. Please wait a moment and try again.</p>
                <p><a href="/">Go back</a></p>
            </body>
            </html>
            """,
            status_code=429
        )

    # For API endpoints, return JSON
    return _rate_limit_exceeded_handler(request, exc)

# Add rate limit exceeded handler
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# Add session middleware for cookie-based auth
app.add_middleware(
    SessionMiddleware,
    secret_key="your-session-secret-key-change-in-production",  # TODO: Load from config
    session_cookie="session",
    max_age=3600,  # 1 hour
    same_site="lax",
    https_only=False,  # Set to True in production with HTTPS
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(ui.router)
app.include_router(webhooks.router)


@app.on_event("startup")
def on_startup():
    logger.info("Application startup: Creating database tables")
    create_db_and_tables()
    logger.info(f"Application started in {settings.environment} mode")


@app.on_event("shutdown")
def on_shutdown():
    logger.info("Application shutdown initiated")


# Error handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    client_ip = get_client_ip(request)
    logger.warning(
        f"Validation error: path={request.url.path}, ip={client_ip}, "
        f"errors={exc.errors()}"
    )
    # Return JSON for all validation errors since they're mostly API/form related
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with custom error pages"""
    client_ip = get_client_ip(request)

    # Log different levels based on status code
    if exc.status_code >= 500:
        logger.error(
            f"Server error: status={exc.status_code}, path={request.url.path}, "
            f"ip={client_ip}, detail={exc.detail}"
        )
    elif exc.status_code >= 400:
        if exc.status_code == 404:
            logger.info(f"Not found: path={request.url.path}, ip={client_ip}")
        else:
            logger.warning(
                f"Client error: status={exc.status_code}, path={request.url.path}, "
                f"ip={client_ip}, detail={exc.detail}"
            )

    # Check if the request expects JSON (API endpoints)
    if request.url.path.startswith("/auth/") or request.url.path.startswith("/users/"):
        # Return JSON for API endpoints
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    
    # Return HTML error page for UI routes
    if exc.status_code == 404:
        return templates.TemplateResponse(
            "404.html",
            {"request": request},
            status_code=404
        )
    
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "status_code": exc.status_code,
            "title": {
                400: "Bad Request",
                401: "Unauthorized",
                403: "Forbidden",
                500: "Internal Server Error",
            }.get(exc.status_code, "Error"),
            "detail": exc.detail
        },
        status_code=exc.status_code
    )

