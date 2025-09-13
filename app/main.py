from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware
from app.database import create_db_and_tables
from app.routers import auth, users, ui
from app.templates_config import templates

app = FastAPI(
    title="FastAPI Auth App",
    description="A FastAPI application with JWT authentication",
    version="1.0.0",
)

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


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


# Error handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with custom error pages"""
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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    # Check if the request expects JSON
    if request.url.path.startswith("/auth/") or request.url.path.startswith("/users/"):
        # Return JSON for API endpoints
        return {"detail": str(exc)}
    
    # Return HTML error page for UI routes
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "status_code": 422,
            "title": "Validation Error",
            "detail": "Please check your input and try again."
        },
        status_code=422
    )